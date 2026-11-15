import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,sys,time,types
from pathlib import Path
import numpy as np
import torch
from torch import nn
import yaml
from sklearn.metrics import average_precision_score,roc_auc_score
from features import cv2

root=Path(__file__).parent
torch.set_num_threads(4)

class DropPath(nn.Module):
    def __init__(self,drop_prob=0.,scale_by_keep=True):
        super().__init__();self.drop_prob=drop_prob;self.scale_by_keep=scale_by_keep
    def forward(self,x):
        if not self.training or self.drop_prob==0:return x
        keep=1-self.drop_prob
        gate=x.new_empty((x.shape[0],)+(1,)*(x.ndim-1)).bernoulli_(keep)
        return x*gate/keep

class Options(dict):
    def __getattr__(self,key):return self[key]

def build():
    for name in ['timm','timm.models','timm.models.layers']:sys.modules[name]=types.ModuleType(name)
    layer=sys.modules['timm.models.layers']
    layer.DropPath=DropPath;layer.to_2tuple=lambda v:v if isinstance(v,tuple) else (v,v)
    layer.trunc_normal_=torch.nn.init.trunc_normal_
    source=root/'trufor/TruFor_train_test'
    sys.path.insert(0,str(source))
    def convert(x):return Options({k:convert(v) for k,v in x.items()}) if isinstance(x,dict) else x
    cfg=convert(yaml.safe_load((source/'lib/config/trufor_ph3.yaml').read_text()))
    cfg.MODEL.MODS=['RGB','NP++']
    from lib.models.cmx.builder_np_conf import EncoderDecoder
    model=EncoderDecoder(cfg=cfg)
    checkpoint=torch.load(root/'trufor-weights/weights/trufor.pth.tar',map_location='cpu',weights_only=False)
    model.load_state_dict(checkpoint['state_dict']);model.eval()
    return model

def predict(model,image):
    rgb=torch.from_numpy(image[:,:,::-1].transpose(2,0,1).copy()).float()[None]/255
    with torch.inference_mode():
        logits,confidence,det,noise=model(rgb,save_np=True)
        return logits.softmax(1)[0,1].numpy(),confidence.sigmoid()[0,0].numpy(),noise[0,0].numpy()

if __name__=='__main__':
    model=build();results=[]
    output=root/'trufor-output';output.mkdir(exist_ok=True)
    for path in sorted((root/'data/exhibits').glob('*.jpg')):
        started=time.time();image=cv2.imread(str(path));mask=cv2.imread(str(path.with_name(path.stem+'_mask.png')),0)>127
        target=output/(path.stem+'.npz')
        if target.exists():z=np.load(target);score=z['heat'];conf=z['confidence']
        else:
            score,conf,noise=predict(model,image)
            np.savez_compressed(target,heat=score,confidence=conf,noise=noise)
        smooth=cv2.GaussianBlur(score,(0,0),7);smooth[:20]=0;smooth[-20:]=0;smooth[:,:20]=0;smooth[:,-20:]=0
        cy,cx=np.unravel_index(smooth.argmax(),smooth.shape)
        result={'image':path.name,'hit':bool(mask[cy,cx]),'ap':float(average_precision_score(mask.ravel(),score.ravel())),'auc':float(roc_auc_score(mask.ravel(),score.ravel())),'x':int(cx),'y':int(cy)}
        results.append(result)
        print('TruFor',path.stem,'hit',result['hit'],'AP',round(result['ap'],3),'seconds',round(time.time()-started,1),flush=True)
        (root/'trufor-validation.json').write_text(json.dumps(results,indent=2)+'\n')
