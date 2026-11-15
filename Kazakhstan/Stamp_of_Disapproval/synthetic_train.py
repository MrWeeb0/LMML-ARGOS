import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,time
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
from pixel_model import PixelNet,pixel_features,get_data
from features import cv2,inside

root=Path(__file__).parent
torch.set_num_threads(2)

def train():
    torch.manual_seed(73);rng=np.random.default_rng(73)
    data=get_data();normal=[]
    for path in sorted((root/'data/albums').glob('*/*.jpg')):
        image=cv2.imread(str(path));_,boxes=inside(image)
        for x,y,w,h in boxes:
            if w>=144 and h>=144:normal.append(image[y:y+h,x:x+w].copy())
    print('Unlabelled stamp crops',len(normal),flush=True)
    model=PixelNet();model.load_state_dict(torch.load(root/'pixel-detector.pt',map_location='cpu',weights_only=True))
    optimizer=torch.optim.AdamW(model.parameters(),lr=.0002,weight_decay=.0001)
    losses=[];started=time.time()
    for step in range(1,801):
        xs=[];ys=[]
        for b in range(8):
            if b<4:
                name,f,mask=data[int(rng.integers(len(data)))];h,w=mask.shape
                yy,xx=np.where(mask);j=int(rng.integers(len(xx)))
                y=int(np.clip(yy[j]-64+rng.integers(-36,37),0,h-128))
                x=int(np.clip(xx[j]-64+rng.integers(-36,37),0,w-128))
                a=f[:,y:y+128,x:x+128].copy();m=mask[y:y+128,x:x+128].astype(np.float32)
            else:
                image=normal[int(rng.integers(len(normal)))];h,w=image.shape[:2]
                y=int(rng.integers(h-127));x=int(rng.integers(w-127))
                patch=image[y:y+128,x:x+128].copy()
                m=np.zeros((128,128),np.float32)
                if b<7:
                    bw=int(rng.integers(20,63));bh=int(rng.integers(18,69))
                    x0=int(rng.integers(16,112-bw));y0=int(rng.integers(16,112-bh))
                    m[y0:y0+bh,x0:x0+bw]=1
                    kind=int(rng.integers(3))
                    if kind==0:
                        patch=cv2.inpaint(patch,(m*255).astype(np.uint8),3,cv2.INPAINT_TELEA)
                    elif kind==1:
                        color=np.median(patch[max(0,y0-5):min(128,y0+bh+5),max(0,x0-5):min(128,x0+bw+5)].reshape(-1,3),axis=0)
                        alpha=cv2.GaussianBlur(m,(0,0),float(rng.uniform(.5,1.5)))[:,:,None]
                        patch=np.clip(patch*(1-alpha)+color*alpha,0,255).astype(np.uint8)
                    else:
                        sx=int(rng.integers(0,129-bw));sy=int(rng.integers(0,129-bh))
                        block=patch[sy:sy+bh,sx:sx+bw].copy()
                        patch[y0:y0+bh,x0:x0+bw]=block
                    patch=np.clip(patch.astype(float)+rng.normal(0,float(rng.uniform(.4,1.8)),patch.shape),0,255).astype(np.uint8)
                    patch=cv2.imdecode(cv2.imencode('.jpg',patch,[cv2.IMWRITE_JPEG_QUALITY,97])[1],1)
                a=pixel_features(patch)
            if rng.random()<.5:a=a[:,:,::-1];m=m[:,::-1]
            if rng.random()<.5:a=a[:,::-1];m=m[::-1]
            xs.append(a.copy());ys.append(m[None].copy())
        model.train();x=torch.from_numpy(np.stack(xs));y=torch.from_numpy(np.stack(ys))
        logits=model(x);prob=logits.sigmoid()
        dice=1-(2*(prob*y).sum((1,2,3))+1)/(prob.sum((1,2,3))+y.sum((1,2,3))+1)
        loss=F.binary_cross_entropy_with_logits(logits,y,pos_weight=torch.tensor(3.))+dice.mean()
        optimizer.zero_grad();loss.backward();optimizer.step();losses.append(loss.item())
        if step%100==0:print('synthetic adaptation',step,'loss',round(float(np.mean(losses[-100:])),4),'seconds',round(time.time()-started),flush=True)
    torch.save(model.state_dict(),root/'pixel-synthetic-detector.pt')
    (root/'synthetic-training.json').write_text(json.dumps({'steps':800,'seed':73,'real_exhibits':len(data),'unlabelled_stamp_crops':len(normal),'batch_composition':{'real_positive_crops':4,'synthetic_manipulations':3,'unlabelled_normal_crops':1},'mean_final_loss':float(np.mean(losses[-100:])),'independent_validation':False,'note':'Adapted from a model already fitted on all exhibits. Training loss is not independent evaluation.'},indent=2)+'\n')

if __name__=='__main__':train()
