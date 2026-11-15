import json
from pathlib import Path
import numpy as np
from features import cv2,inside
from detect import overlays

root=Path(__file__).parent
def centers():
    result=[]
    for path in sorted((root/'data/exhibits').glob('*.jpg')):
        image=cv2.imread(str(path));m=cv2.imread(str(path.with_name(path.stem+'_mask.png')),0)>127
        yy,xx=np.where(m);mask,boxes=inside(image)
        box=max(boxes,key=lambda b:b[2]*b[3])
        x,y,w,h=box
        result.append([(xx.mean()-x)/w,(yy.mean()-y)/h])
    return np.array(result)

def prior(shape,boxes,points,sigma=.09):
    yy,xx=np.mgrid[:shape[0],:shape[1]];xx=xx*4+2;yy=yy*4+2
    density=np.zeros((128,128),np.float32)
    indices=np.clip(np.rint(points*127).astype(int),0,127)
    np.add.at(density,(indices[:,1],indices[:,0]),1)
    density=cv2.GaussianBlur(density,(0,0),sigma*127)
    p=np.zeros(shape,np.float32)
    for x,y,w,h in boxes:
        u=(xx-x)/w;v=(yy-y)/h
        q=cv2.remap(density,(u*127).astype(np.float32),(v*127).astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        q[(u<0)|(u>1)|(v<0)|(v>1)]=0
        p=np.maximum(p,q)
    return p

if __name__=='__main__':
    points=centers()
    (root/'spatial-prior.json').write_text(json.dumps(points.tolist(),indent=2))
    for method in ['output','context-output']:
        original=json.loads((root/method/'detections.json').read_text())
        for power in [.25,.5,1.,2.]:
            rows=[]
            for record in original:
                a=np.load(root/method/'heatmaps'/f'{record["album"]}-{record["page"]}.npz')['heat']
                p=prior(a.shape,record['stamps'],points)
                smooth=cv2.GaussianBlur(a,(0,0),2)*p**power
                cy,cx=np.unravel_index(smooth.argmax(),smooth.shape)
                rows.append({**record,'center':[int(cx*4+2),int(cy*4+2)],'score':float(smooth[cy,cx])})
            overlays(rows,root/method,f'prior-{power}.png')
            (root/method/f'prior-{power}.json').write_text(json.dumps(rows,indent=2))
