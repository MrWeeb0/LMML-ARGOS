import os
os.environ['OPENBLAS_NUM_THREADS']='4'
import csv,json,time
from pathlib import Path
import numpy as np
import joblib
from sklearn.ensemble import ExtraTreesClassifier,HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,average_precision_score
from features import cv2,extract
import features

root=Path(__file__).parent
cache=root/'cache';cache.mkdir(exist_ok=True)
paths=sorted((root/'data/exhibits').glob('*.jpg'))
records=[];names=None
for p in paths:
    target=cache/(p.stem+'.npz')
    if not target.exists():
        image=cv2.imread(str(p));mask=cv2.imread(str(p.with_name(p.stem+'_mask.png')),0)
        f=extract(image)
        names=features.NAMES
        m=mask[2::4,2::4]>127
        valid=np.zeros(m.shape,bool);valid[6:-6,6:-6]=True
        np.savez_compressed(target,features=f,mask=m,valid=valid)
    z=np.load(target);records.append((p,z['features'],z['mask'],z['valid']))
    print('features',p.stem,flush=True)
if names: (cache/'feature-names.json').write_text(json.dumps(names))
rng=np.random.default_rng(72)
xs=[];ys=[];gs=[]
for i,(p,f,m,valid) in enumerate(records):
    pos=np.flatnonzero((m&valid).ravel());neg=np.flatnonzero((~m&valid).ravel())
    take=np.r_[pos,rng.choice(neg,min(len(neg),6000),replace=False)]
    xs.append(f.reshape(-1,f.shape[-1])[take]);ys.append(m.ravel()[take]);gs.extend([i]*len(take))
X=np.vstack(xs);y=np.concatenate(ys);g=np.array(gs)
print('Training',X.shape,int(y.sum()),flush=True)
out=[]
for fold in range(5):
    test=(g%5)==fold
    model=ExtraTreesClassifier(n_estimators=160,max_depth=22,min_samples_leaf=5,max_features=.7,class_weight='balanced',n_jobs=6,random_state=17)
    model.fit(X[~test],y[~test])
    for i,(p,f,m,valid) in enumerate(records):
        if i%5!=fold: continue
        score=model.predict_proba(f.reshape(-1,f.shape[-1]))[:,1].reshape(m.shape)
        score[~valid]=0
        smooth=cv2.GaussianBlur(score.astype(np.float32),(0,0),3)
        cy,cx=np.unravel_index(smooth.argmax(),smooth.shape)
        hit=bool(m[cy,cx])
        auc=roc_auc_score(m[valid],score[valid]);ap=average_precision_score(m[valid],score[valid])
        out.append({'image':p.name,'fold':fold,'hit':hit,'auc':auc,'ap':ap,'x':int(cx*4+2),'y':int(cy*4+2),'peak':float(smooth[cy,cx])})
        np.save(cache/(p.stem+'-oof.npy'),score)
        print('heldout',p.stem,hit,round(auc,3),round(ap,3),flush=True)
    joblib.dump(model,cache/f'fold-{fold}.joblib',compress=3)
(root/'exhibit-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print('CENTER HITS',sum(r['hit'] for r in out),'/',len(out),'mean AUC',np.mean([r['auc'] for r in out]),'mean AP',np.mean([r['ap'] for r in out]),flush=True)
model=ExtraTreesClassifier(n_estimators=200,max_depth=24,min_samples_leaf=4,max_features=.7,class_weight='balanced',n_jobs=6,random_state=17).fit(X,y)
joblib.dump(model,root/'detector.joblib',compress=3)
names=json.loads((cache/'feature-names.json').read_text())
print('TOP FEATURES',sorted(zip(names,model.feature_importances_),key=lambda x:-x[1])[:25],flush=True)
