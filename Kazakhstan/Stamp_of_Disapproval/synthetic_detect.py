import csv,json,time
from pathlib import Path
import numpy as np
import torch
from PIL import Image,ImageDraw
from features import cv2,inside
from pixel_model import PixelNet,pixel_features
from detect import overlays

root=Path(__file__).parent
torch.set_num_threads(2)

def main():
    model=PixelNet();model.load_state_dict(torch.load(root/'pixel-synthetic-detector.pt',map_location='cpu',weights_only=True));model.eval()
    output=root/'synthetic-output';output.mkdir(exist_ok=True)
    for name in ['heatmaps','detections']:(output/name).mkdir(exist_ok=True)
    rows=[];started=time.time()
    for path in sorted((root/'data/albums').glob('*/*.jpg')):
        image=cv2.imread(str(path));h,w=image.shape[:2];valid,stamps=inside(image)
        heat=np.zeros((h,w),np.float32)
        for x,y,bw,bh in stamps:
            x0=max(0,x-16);y0=max(0,y-16);x1=min(w,x+bw+16);y1=min(h,y+bh+16)
            f=pixel_features(image[y0:y1,x0:x1])
            with torch.inference_mode():p=model(torch.from_numpy(f)[None]).sigmoid()[0,0].numpy()
            p[valid[y0:y1,x0:x1]==0]=0
            np.maximum(heat[y0:y1,x0:x1],p,out=heat[y0:y1,x0:x1])
        score=cv2.GaussianBlur(heat,(0,0),7)
        cy,cx=np.unravel_index(score.argmax(),score.shape)
        candidates=[];remaining=cv2.resize(score,(400,300),interpolation=cv2.INTER_AREA);yy,xx=np.ogrid[:300,:400]
        for _ in range(12):
            y,x=np.unravel_index(remaining.argmax(),remaining.shape)
            candidates.append({'x':int(x*4+2),'y':int(y*4+2),'score':float(remaining[y,x])})
            remaining[(xx-x)**2+(yy-y)**2<15**2]=0
        x0=max(0,int(cx)-35);y0=max(0,int(cy)-35)
        row={'album':path.parent.name,'page':path.stem,'box':[x0,y0,70,70],'center':[int(cx),int(cy)],'score':float(score[cy,cx]),'candidates':candidates,'stamps':stamps}
        rows.append(row)
        np.savez_compressed(output/'heatmaps'/f'{path.parent.name}-{path.stem}.npz',heat=cv2.resize(heat,(400,300),interpolation=cv2.INTER_AREA).astype(np.float16))
        marked=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB));ImageDraw.Draw(marked).rectangle((x0,y0,x0+70,y0+70),outline='red',width=5)
        marked.thumbnail((800,600));marked.save(output/'detections'/f'{path.parent.name}-{path.stem}.jpg',quality=85)
        print('page',len(rows),row['album'],row['page'],round(row['score'],4),'seconds',round(time.time()-started),flush=True)
        if len(rows)%26==0:overlays(rows,output,'progress-overlay.png')
    (output/'detections.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (output/'boxes.csv').open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['album','page','x','y','w','h']);writer.writerows([r['album'],r['page'],*r['box']] for r in rows)
    overlays(rows,output)
    print('Completed detections:',len(rows),flush=True)

if __name__=='__main__':main()
