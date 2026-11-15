import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from features import cv2

root=Path(__file__).parent
for method in ['output','context-output']:
    for mode in ['power','equal','peak','contrast']:
        panels=[]
        for ai in range(1,6):
            maps=[];opportunities=[]
            for path in sorted((root/method/'heatmaps').glob(f'album_{ai}-*.npz')):
                a=np.load(path)['heat'];inside=a>0
                a=cv2.GaussianBlur(a,(0,0),2)
                if mode=='power':a=a**3/(np.max(a)**3+1e-8)
                if mode=='equal':a=np.maximum(a-np.quantile(a[inside],.8),0)/(a.max()+1e-8)
                if mode=='peak':a=np.exp((a-a.max())/.07)*inside
                if mode=='contrast':a=np.maximum(a-cv2.GaussianBlur(a,(0,0),12),0)/(a.max()+1e-8)
                a/=a.sum()+1e-8
                maps.append(a);opportunities.append(inside.astype(float))
            combined=cv2.GaussianBlur(np.sum(maps,axis=0),(0,0),3)
            combined/=np.maximum(4,cv2.GaussianBlur(np.sum(opportunities,axis=0),(0,0),5))**.5
            p=np.clip(combined/np.quantile(combined,.998),0,1)
            panel=Image.fromarray((255*(1-p)).astype(np.uint8)).convert('RGB')
            panels.append(panel)
        canvas=Image.new('RGB',(2000,330),'white')
        for i,p in enumerate(panels):canvas.paste(p,(i*400,30));ImageDraw.Draw(canvas).text((i*400+10,5),f'{method} {mode} album {i+1}',fill='black')
        canvas.save(root/method/(mode+'-density.png'))
