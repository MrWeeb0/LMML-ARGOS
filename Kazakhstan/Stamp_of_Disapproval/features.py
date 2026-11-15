import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'vendor'))
import cv2
import numpy as np

cv2.setNumThreads(1)
NAMES=[]

def extract(image,stride=4):
    a=image.astype(np.float32)
    gray=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY)
    channels=[gray,a[:,:,0]-a[:,:,1],a[:,:,2]-a[:,:,1]]
    h,w=gray.shape
    rows=[];names=[]
    def add(v,name):
        rows.append(v[2::stride,2::stride]);names.append(name)
    def local(v,k): return cv2.boxFilter(v,-1,(k,k),borderType=cv2.BORDER_REFLECT)
    for i,g in enumerate(channels):
        add(g,'mean_raw_'+str(i))
        dx=cv2.Sobel(g,-1,1,0,ksize=3)/8
        dy=cv2.Sobel(g,-1,0,1,ksize=3)/8
        grad=np.sqrt(dx*dx+dy*dy)
        lap=cv2.Laplacian(g,-1,ksize=1)
        residual=g-cv2.GaussianBlur(g,(0,0),1)
        median=cv2.medianBlur(np.clip(g+128 if i else g,0,255).astype(np.uint8),3).astype(np.float32)
        med=g-(median-128 if i else median)
        for k in [5,11,23,47]:
            mean=local(g,k)
            variance=np.maximum(local(g*g,k)-mean*mean,0)
            add(mean,f'mean_{i}_{k}')
            add(np.log1p(variance),f'variance_{i}_{k}')
            add(np.log1p(local(grad,k)),f'gradient_{i}_{k}')
            add(np.log1p(local(abs(lap),k)),f'laplacian_{i}_{k}')
            add(np.log1p(local(residual*residual,k)),f'noise_{i}_{k}')
            add(local(np.minimum(abs(lap),5),k),f'lap_clip_{i}_{k}')
            add(local(np.minimum(abs(med),5),k),f'median_clip_{i}_{k}')
            add(local((abs(lap)<1.5).astype(np.float32),k),f'flat_{i}_{k}')
            add(np.log1p(local(residual*residual,k)/(1+local(grad,k)**2)),f'noise_norm_{i}_{k}')
        if i==0:
            for q in [70,80,90,95,98]:
                encoded=cv2.imencode('.jpg',image,[cv2.IMWRITE_JPEG_QUALITY,q])[1]
                again=cv2.imdecode(encoded,1).astype(np.float32)
                delta=abs(a-again).mean(2)
                for k in [7,19,41]: add(np.log1p(local(delta,k)),f'ela_{q}_{k}')
    global NAMES
    NAMES=names
    return np.stack(rows,axis=-1).astype(np.float32)

def inside(image):
    d=np.max(abs(image.astype(np.int16)-np.array([38,36,34])),axis=2)
    m=cv2.morphologyEx((d>30).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(m)
    result=np.zeros(m.shape,np.uint8);boxes=[]
    for x,y,w,h,area in stats[1:]:
        if w>120 and h>120:
            result[y+18:y+h-18,x+18:x+w-18]=1
            boxes.append([int(x),int(y),int(w),int(h)])
    return result,boxes
