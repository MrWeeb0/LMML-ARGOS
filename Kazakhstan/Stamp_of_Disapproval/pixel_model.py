import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,time
from pathlib import Path
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from sklearn.metrics import average_precision_score
from features import cv2

root=Path(__file__).parent
torch.set_num_threads(2)

def pixel_features(image):
    a=image.astype(np.float32)
    blur=cv2.GaussianBlur(a,(0,0),1)
    median=cv2.medianBlur(image,3).astype(np.float32)
    lap=cv2.Laplacian(a,-1,ksize=1)
    return np.concatenate([(a-128)/128,(a-blur)/12,(a-median)/16,lap/24],axis=2).transpose(2,0,1).copy()

class Unit(nn.Module):
    def __init__(self,a,b):
        super().__init__();self.net=nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.BatchNorm2d(b),nn.SiLU(),nn.Conv2d(b,b,3,padding=1),nn.BatchNorm2d(b),nn.SiLU())
    def forward(self,x):return self.net(x)

class PixelNet(nn.Module):
    def __init__(self):
        super().__init__();self.a=Unit(12,16);self.b=Unit(16,32);self.c=Unit(32,64)
        self.ub=Unit(96,32);self.ua=Unit(48,16);self.out=nn.Conv2d(16,1,1)
    def forward(self,x):
        a=self.a(x);b=self.b(F.avg_pool2d(a,2));c=self.c(F.avg_pool2d(b,2))
        b=self.ub(torch.cat([b,F.interpolate(c,size=b.shape[-2:],mode='bilinear',align_corners=False)],1))
        a=self.ua(torch.cat([a,F.interpolate(b,size=a.shape[-2:],mode='bilinear',align_corners=False)],1))
        return self.out(a)

def get_data():
    data=[]
    for path in sorted((root/'data/exhibits').glob('*.jpg')):
        image=cv2.imread(str(path));mask=cv2.imread(str(path.with_name(path.stem+'_mask.png')),0)>127
        data.append((path.stem,pixel_features(image),mask))
    return data

def train(data,final=False,steps=1600):
    torch.manual_seed(41);rng=np.random.default_rng(41)
    held=set(rng.permutation(len(data))[:6]) if not final else set()
    active=[i for i in range(len(data)) if i not in held]
    model=PixelNet();opt=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
    history=[];best=-1;beststep=steps;started=time.time()
    for step in range(1,steps+1):
        model.train();xs=[];ys=[]
        for _ in range(8):
            i=int(rng.choice(active));_,f,mask=data[i];h,w=mask.shape
            if rng.random()<.75:
                yy,xx=np.where(mask);j=int(rng.integers(len(xx)));y,x=int(yy[j]),int(xx[j])
            else:y,x=int(rng.integers(h)),int(rng.integers(w))
            y=int(np.clip(y-64+rng.integers(-40,41),0,h-128));x=int(np.clip(x-64+rng.integers(-40,41),0,w-128))
            a=f[:,y:y+128,x:x+128].copy();m=mask[y:y+128,x:x+128].astype(np.float32)[None]
            if rng.random()<.5:a=a[:,:,::-1];m=m[:,:,::-1]
            if rng.random()<.5:a=a[:,::-1];m=m[:,::-1]
            xs.append(a.copy());ys.append(m.copy())
        x=torch.from_numpy(np.stack(xs));y=torch.from_numpy(np.stack(ys))
        logits=model(x);p=logits.sigmoid()
        loss=F.binary_cross_entropy_with_logits(logits,y,pos_weight=torch.tensor(3.))+(1-(2*(p*y).sum((1,2,3))+1)/(p.sum((1,2,3))+y.sum((1,2,3))+1)).mean()
        opt.zero_grad();loss.backward();opt.step()
        if step%100==0:
            if held:
                model.eval();results=[]
                with torch.inference_mode():
                    for i in sorted(held):
                        name,f,m=data[i];prob=model(torch.from_numpy(f)[None]).sigmoid()[0,0].numpy()
                        s=cv2.GaussianBlur(prob,(0,0),7);s[:22]=0;s[-22:]=0;s[:,:22]=0;s[:,-22:]=0
                        y,x=np.unravel_index(s.argmax(),s.shape)
                        results.append({'image':name,'hit':bool(m[y,x]),'ap':float(average_precision_score(m.ravel(),prob.ravel()))})
                value=sum(z['hit'] for z in results)+np.mean([z['ap'] for z in results])
                history.append({'step':step,'results':results,'metric':value})
                print('pixel',step,'hits',sum(z['hit'] for z in results),'AP',round(np.mean([z['ap'] for z in results]),3),'loss',round(loss.item(),3),'seconds',round(time.time()-started),flush=True)
                if value>best:
                    best=value;beststep=step;torch.save(model.state_dict(),root/'pixel-validation.pt')
            else:print('final pixel',step,'loss',round(loss.item(),3),'seconds',round(time.time()-started),flush=True)
    if held:
        (root/'pixel-validation.json').write_text(json.dumps({'heldout':[data[i][0] for i in sorted(held)],'best_step':beststep,'history':history},indent=2)+'\n')
        return beststep
    torch.save(model.state_dict(),root/'pixel-detector.pt')
    return steps

if __name__=='__main__':
    data=get_data();steps=train(data,False,1000);train(data,True,steps)
