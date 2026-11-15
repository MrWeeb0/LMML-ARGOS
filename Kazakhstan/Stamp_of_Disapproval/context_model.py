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

torch.set_num_threads(4)
root=Path(__file__).parent

class Unit(nn.Module):
    def __init__(self,a,b):
        super().__init__()
        self.net=nn.Sequential(nn.Conv2d(a,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU(),nn.Conv2d(b,b,3,padding=1),nn.GroupNorm(4,b),nn.SiLU())
    def forward(self,x):return self.net(x)

class ContextNet(nn.Module):
    def __init__(self,channels):
        super().__init__()
        self.project=nn.Sequential(nn.Conv2d(channels,24,1),nn.SiLU())
        self.a=Unit(24,24);self.b=Unit(24,48);self.c=Unit(48,96)
        self.upb=Unit(144,48);self.upa=Unit(72,24);self.head=nn.Conv2d(24,1,1)
    def forward(self,x):
        a=self.a(self.project(x));b=self.b(F.avg_pool2d(a,2));c=self.c(F.avg_pool2d(b,2))
        b=self.upb(torch.cat([b,F.interpolate(c,size=b.shape[-2:],mode='bilinear',align_corners=False)],1))
        a=self.upa(torch.cat([a,F.interpolate(b,size=a.shape[-2:],mode='bilinear',align_corners=False)],1))
        return self.head(a)

def records():
    out=[]
    for path in sorted((root/'cache').glob('exhibit_*.npz')):
        z=np.load(path);f=z['features'];m=z['mask'];v=z['valid']
        pad=((0,max(0,64-f.shape[0])),(0,max(0,64-f.shape[1])))
        f=np.pad(f,(*pad,(0,0)),mode='edge');m=np.pad(m,pad);v=np.pad(v,pad)
        out.append((path.stem,f,m,v))
    return out

def normalize(f,mean,scale):return np.clip((f-mean)/scale,-6,6).transpose(2,0,1).copy()

def train(final=False,steps=500):
    torch.manual_seed(27);rng=np.random.default_rng(27)
    data=records();groups=sorted({r[0].split('-')[0] for r in data})
    held_names={groups[i] for i in rng.permutation(len(groups))[:6]} if not final else set()
    held={i for i,r in enumerate(data) if r[0].split('-')[0] in held_names}
    validation=[i for i in sorted(held) if '-aug' not in data[i][0]]
    active=[i for i in range(len(data)) if i not in held]
    sample=np.concatenate([data[i][1].reshape(-1,126)[::20] for i in active])
    mean=np.median(sample,0).astype(np.float32);scale=np.maximum(np.std(sample,0),.05).astype(np.float32)
    prepared=[normalize(f,mean,scale) for _,f,_,_ in data]
    model=ContextNet(len(mean));optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.0001)
    best=-1;best_step=steps;history=[];started=time.time()
    for step in range(1,steps+1):
        model.train();xs=[];ys=[]
        for _ in range(8):
            i=int(rng.choice(active));name,f,mask,valid=data[i];h,w=mask.shape
            if rng.random()<.8:
                yy,xx=np.where(mask);j=int(rng.integers(len(xx)));y,x=int(yy[j]),int(xx[j])
            else:y,x=int(rng.integers(h)),int(rng.integers(w))
            y=int(np.clip(y-32+rng.integers(-20,21),0,h-64));x=int(np.clip(x-32+rng.integers(-20,21),0,w-64))
            a=prepared[i][:,y:y+64,x:x+64];m=mask[y:y+64,x:x+64].astype(np.float32)[None]
            if rng.random()<.5:a=a[:,:,::-1];m=m[:,:,::-1]
            if rng.random()<.5:a=a[:,::-1];m=m[:,::-1]
            xs.append(a.copy());ys.append(m.copy())
        x=torch.from_numpy(np.stack(xs));y=torch.from_numpy(np.stack(ys))
        logits=model(x);prob=logits.sigmoid()
        bce=F.binary_cross_entropy_with_logits(logits,y,pos_weight=torch.tensor(4.))
        dice=1-(2*(prob*y).sum((1,2,3))+1)/(prob.sum((1,2,3))+y.sum((1,2,3))+1)
        loss=bce+dice.mean()
        optimizer.zero_grad();loss.backward();optimizer.step()
        if step%50==0:
            if held:
                model.eval();measure=[]
                with torch.inference_mode():
                    for i in validation:
                        score=model(torch.from_numpy(prepared[i])[None]).sigmoid()[0,0].numpy()
                        name,f,m,valid=data[i];score[~valid]=0
                        smooth=cv2.GaussianBlur(score,(0,0),2)
                        cy,cx=np.unravel_index(smooth.argmax(),smooth.shape)
                        measure.append({'image':name,'hit':bool(m[cy,cx]),'ap':float(average_precision_score(m[valid],score[valid]))})
                metric=sum(z['hit'] for z in measure)+np.mean([z['ap'] for z in measure])
                history.append({'step':step,'results':measure,'metric':metric})
                print('context',step,'loss',round(float(loss),3),'hits',sum(z['hit'] for z in measure),'AP',round(np.mean([z['ap'] for z in measure]),3),'seconds',round(time.time()-started),flush=True)
                if metric>best:
                    best=metric;best_step=step
                    torch.save({'state_dict':model.state_dict(),'mean':mean,'scale':scale,'step':step},root/'context-aug-validation.pt')
            else:print('final context',step,'loss',round(float(loss),3),'seconds',round(time.time()-started),flush=True)
    if held:
        (root/'context-aug-validation.json').write_text(json.dumps({'heldout_images':[data[i][0] for i in validation],'best_step':best_step,'history':history},indent=2)+'\n')
        return best_step
    torch.save({'state_dict':model.state_dict(),'mean':mean,'scale':scale,'step':steps},root/'context-aug-detector.pt')
    return steps

if __name__=='__main__':
    steps=train(False,800)
    train(True,steps)
