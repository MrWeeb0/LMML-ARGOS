import json,time,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import torch
from PIL import Image,ImageDraw
from features import cv2,extract,inside
from context_model import ContextNet,normalize
from detect import overlays

root=Path(__file__).parent
torch.set_num_threads(2)

def locate(path,model,pack,output):
    image=cv2.imread(str(path));h,w=image.shape[:2];valid,stamps=inside(image)
    heat=np.zeros((h//4,w//4),np.float32)
    for x,y,bw,bh in stamps:
        x0=max(0,(x-16)//8*8);y0=max(0,(y-16)//8*8)
        x1=min(w,((x+bw+23)//8)*8);y1=min(h,((y+bh+23)//8)*8)
        f=extract(image[y0:y1,x0:x1]);keep=valid[y0+2:y1:4,x0+2:x1:4]>0
        with torch.inference_mode():p=model(torch.from_numpy(normalize(f,pack['mean'],pack['scale']))[None]).sigmoid()[0,0].numpy()
        p[~keep]=0
        target=heat[y0//4:y0//4+p.shape[0],x0//4:x0//4+p.shape[1]]
        np.maximum(target,p,out=target)
    np.savez_compressed(output/'heatmaps'/f'{path.parent.name}-{path.stem}.npz',heat=heat)
    smooth=cv2.GaussianBlur(heat,(0,0),2)
    cy,cx=np.unravel_index(smooth.argmax(),smooth.shape)
    candidates=[];remaining=smooth.copy();yy,xx=np.ogrid[:smooth.shape[0],:smooth.shape[1]]
    for i in range(12):
        y,x=np.unravel_index(remaining.argmax(),remaining.shape)
        candidates.append({'x':int(x*4+2),'y':int(y*4+2),'score':float(remaining[y,x])})
        remaining[(xx-x)**2+(yy-y)**2<15**2]=0
    center=[int(cx*4+2),int(cy*4+2)]
    box=[max(0,center[0]-35),max(0,center[1]-35),70,70]
    marked=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB));draw=ImageDraw.Draw(marked)
    draw.rectangle((box[0],box[1],box[0]+70,box[1]+70),outline='red',width=4)
    marked.thumbnail((800,600));marked.save(output/'detections'/f'{path.parent.name}-{path.stem}.jpg',quality=88)
    return {'album':path.parent.name,'page':path.stem,'box':box,'center':center,'score':float(smooth[cy,cx]),'candidates':candidates,'stamps':stamps}

if __name__=='__main__':
    suffix='aug-' if '--aug' in sys.argv else ''
    pack=torch.load(root/f'context-{suffix}detector.pt',map_location='cpu',weights_only=False)
    model=ContextNet(len(pack['mean']));model.load_state_dict(pack['state_dict']);model.eval()
    output=root/('context-aug-output' if suffix else 'context-output');output.mkdir(exist_ok=True)
    for name in ['detections','heatmaps']:(output/name).mkdir(exist_ok=True)
    rows=[];started=time.time()
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs={pool.submit(locate,p,model,pack,output):p for p in sorted((root/'data/albums').glob('*/*.jpg'))}
        for future in as_completed(jobs):
            rows.append(future.result())
            if len(rows)%10==0:print('context pages',len(rows),'seconds',round(time.time()-started),flush=True)
            if len(rows)%26==0:overlays(rows,output,'progress-overlay.png')
    rows.sort(key=lambda r:(r['album'],r['page']))
    (output/'detections.json').write_text(json.dumps(rows,indent=2)+'\n');overlays(rows,output)
    print('context done',len(rows),flush=True)
