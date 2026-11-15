import os
os.environ['OPENBLAS_NUM_THREADS']='4'
import json,time
from pathlib import Path
import numpy as np
import joblib,torch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import KFold
from sklearn.metrics import average_precision_score
from features import cv2
from trufor_experiment import build,predict

root=Path(__file__).parent
chosen=np.sort(np.random.default_rng(9).choice(512,128,replace=False))

def cache():
    model=build();out=root/'deep-cache';out.mkdir(exist_ok=True)
    captured=[]
    def hook(module,inputs):captured.append(inputs[0][:,chosen].detach().cpu().numpy()[0].transpose(1,2,0).astype(np.float16))
    model.decode_head.linear_pred.register_forward_pre_hook(hook)
    for path in sorted((root/'data/exhibits').glob('*.jpg')):
        target=out/(path.stem+'.npz')
        if target.exists():continue
        started=time.time();image=cv2.imread(str(path));mask=cv2.imread(str(path.with_name(path.stem+'_mask.png')),0)
        captured.clear();score,confidence,noise=predict(model,image);f=captured[-1]
        m=cv2.resize(mask,(f.shape[1],f.shape[0]),interpolation=cv2.INTER_NEAREST)>127
        valid=np.zeros(m.shape,bool);valid[6:-6,6:-6]=True
        np.savez_compressed(target,features=f,mask=m,valid=valid)
        print('deep features',path.stem,'seconds',round(time.time()-started,1),flush=True)

def train():
    data=[];xs=[];ys=[];groups=[];rng=np.random.default_rng(55)
    for i,path in enumerate(sorted((root/'deep-cache').glob('*.npz'))):
        z=np.load(path);f=z['features'].astype(np.float32);m=z['mask'];v=z['valid'];data.append((path.stem,f,m,v))
        pos=np.flatnonzero((m&v).ravel());neg=np.flatnonzero((~m&v).ravel());take=np.r_[pos,rng.choice(neg,min(5000,len(neg)),replace=False)]
        xs.append(f.reshape(-1,128)[take]);ys.append(m.ravel()[take]);groups.extend([i]*len(take))
    X=np.vstack(xs);y=np.concatenate(ys);groups=np.array(groups);reports=[]
    for strength in [.001,.01,.1,1.]:
        output=[]
        for fit,held in KFold(5,shuffle=True,random_state=23).split(data):
            active=np.isin(groups,fit)
            model=make_pipeline(StandardScaler(),LogisticRegression(C=strength,max_iter=500,class_weight={0:1,1:4}))
            model.fit(X[active],y[active])
            for i in held:
                name,f,m,v=data[i];p=model.predict_proba(f.reshape(-1,128))[:,1].reshape(m.shape).astype(np.float32);p[~v]=0
                s=cv2.GaussianBlur(p,(0,0),1.5);cy,cx=np.unravel_index(s.argmax(),s.shape)
                output.append({'image':name,'hit':bool(m[cy,cx]),'ap':float(average_precision_score(m[v],p[v]))})
                np.save(root/'deep-cache'/f'{name}-oof-{strength}.npy',p)
        metric=sum(z['hit'] for z in output)+np.mean([z['ap'] for z in output])
        reports.append({'C':strength,'metric':metric,'results':output})
        print('deep adapted C',strength,'hits',sum(z['hit'] for z in output),'AP',round(np.mean([z['ap'] for z in output]),3),flush=True)
    winner=max(reports,key=lambda z:z['metric'])
    model=make_pipeline(StandardScaler(),LogisticRegression(C=winner['C'],max_iter=500,class_weight={0:1,1:4})).fit(X,y)
    joblib.dump(model,root/'deep-adapter.joblib',compress=3)
    (root/'deep-validation.json').write_text(json.dumps({'channels':chosen.tolist(),'winner':winner['C'],'experiments':reports},indent=2)+'\n')

if __name__=='__main__':cache();train()
