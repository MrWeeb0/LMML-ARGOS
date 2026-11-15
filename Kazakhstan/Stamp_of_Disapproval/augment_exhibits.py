import json,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
from features import cv2,extract

root=Path(__file__).parent
scales=[.7,.85,1.,1.15,1.3]

def run(item):
    path,index=item;target=root/'cache'/(path.stem+f'-aug{index}.npz')
    if target.exists():return target.name
    rng=np.random.default_rng(int(path.stem[-2:])*31+index)
    image=cv2.imread(str(path));mask=cv2.imread(str(path.with_name(path.stem+'_mask.png')),0)
    scale=scales[index]
    image=cv2.resize(image,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    mask=cv2.resize(mask,(image.shape[1],image.shape[0]),interpolation=cv2.INTER_NEAREST)
    dx,dy=map(int,rng.integers(0,8,size=2));h,w=image.shape[:2]
    a=np.zeros((h+16,w+16,3),np.float32);a[:]=[38,36,34]
    a[dy:dy+h,dx:dx+w]=image
    sigma=[1.4,1.,.3,.8,1.2][index]
    a=np.clip(a+rng.normal(0,sigma,a.shape),0,255).astype(np.uint8)
    a=cv2.imdecode(cv2.imencode('.jpg',a,[cv2.IMWRITE_JPEG_QUALITY,97])[1],1)
    m=np.zeros(a.shape[:2],np.uint8);m[dy:dy+h,dx:dx+w]=mask
    f=extract(a);m=m[2::4,2::4]>127
    valid=np.zeros(m.shape,bool);valid[7:-7,7:-7]=True
    np.savez_compressed(target,features=f,mask=m,valid=valid)
    return target.name

if __name__=='__main__':
    tasks=[(p,i) for p in sorted((root/'data/exhibits').glob('*.jpg')) for i in range(5)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for count,result in enumerate(pool.map(run,tasks),1):
            if count%15==0:print('augmented',count,'/',len(tasks),flush=True)
