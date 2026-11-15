import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,time
from pathlib import Path
import numpy as np
from scipy.fft import dctn
from scipy.spatial import cKDTree
from features import cv2

root=Path(__file__).parent

def copy_map(image,radius=5):
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY).astype(np.float32)
    k=radius*2+1
    patches=np.lib.stride_tricks.sliding_window_view(gray,(k,k))
    local_mean=cv2.boxFilter(gray,-1,(k,k))
    std=np.sqrt(np.maximum(0,cv2.boxFilter(gray*gray,-1,(k,k))-local_mean**2))
    valid=std[radius:-radius,radius:-radius]>12
    valid[:10]=False;valid[-10:]=False;valid[:,:10]=False;valid[:,-10:]=False
    by,bx=np.where(valid)
    allpatch=patches[by,bx]
    f=dctn(allpatch,axes=(-2,-1),norm='ortho')[:,:5,:5].reshape(len(by),25)
    tree=cKDTree(f)
    qi=np.flatnonzero(((by%2)==0)&((bx%2)==0))
    dist,ids=tree.query(f[qi],k=8,workers=3)
    score=np.zeros(gray.shape,np.float32)
    for column in range(1,8):
        selected=ids[:,column]
        spatial=(bx[selected]-bx[qi])**2+(by[selected]-by[qi])**2
        good=(spatial>k*k)&(dist[:,column]<k*5)
        src=qi[good];dst=selected[good]
        if not len(src):continue
        diff=allpatch[src]-allpatch[dst]
        rmse=np.sqrt(np.mean(diff*diff,axis=(1,2)))
        normalized=rmse/(std[by[src]+radius,bx[src]+radius]+1)
        strength=np.exp(-.5*(rmse/3)**2)*np.exp(-.5*(normalized/.12)**2)
        np.maximum.at(score,(by[src]+radius,bx[src]+radius),strength)
        np.maximum.at(score,(by[dst]+radius,bx[dst]+radius),strength)
    return cv2.GaussianBlur(score,(0,0),5)

if __name__=='__main__':
    results=[]
    for path in sorted((root/'data/exhibits').glob('*.jpg')):
        start=time.time();image=cv2.imread(str(path));mask=cv2.imread(str(path.with_name(path.stem+'_mask.png')),0)>127
        target=root/'cache'/(path.stem+'-copy.npy')
        score=np.load(target) if target.exists() else copy_map(image)
        np.save(target,score)
        cy,cx=np.unravel_index(score.argmax(),score.shape)
        peakmask=float(score[mask].max());peak=float(score.max())
        results.append({'image':path.name,'hit':bool(mask[cy,cx]),'peak':peak,'positive_peak':peakmask,'x':int(cx),'y':int(cy)})
        print(path.stem,'hit',mask[cy,cx],'peak',round(peak,4),'positive',round(peakmask,4),'seconds',round(time.time()-start,1),flush=True)
    (root/'copy-validation.json').write_text(json.dumps(results,indent=2)+'\n')
