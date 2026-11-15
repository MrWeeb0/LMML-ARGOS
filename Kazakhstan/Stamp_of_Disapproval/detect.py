import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import csv,json,time
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import numpy as np
import joblib
from PIL import Image,ImageDraw
from features import cv2,extract,inside

root=Path(__file__).parent

def locate(path,model,output):
    image=cv2.imread(str(path));h,w=image.shape[:2]
    valid,stamps=inside(image)
    heat=np.zeros((h//4,w//4),np.float32)
    for x,y,bw,bh in stamps:
        x0=max(0,(x-16)//8*8);y0=max(0,(y-16)//8*8)
        x1=min(w,((x+bw+23)//8)*8);y1=min(h,((y+bh+23)//8)*8)
        f=extract(image[y0:y1,x0:x1])
        keep=valid[y0+2:y1:4,x0+2:x1:4]>0
        p=np.zeros(keep.shape,np.float32)
        p[keep]=model.predict_proba(f[keep])[:,1]
        target=heat[y0//4:y0//4+p.shape[0],x0//4:x0//4+p.shape[1]]
        np.maximum(target,p,out=target)
    np.savez_compressed(output/'heatmaps'/f'{path.parent.name}-{path.stem}.npz',heat=heat)
    smooth=cv2.GaussianBlur(heat,(0,0),2.5)
    candidates=[]
    remaining=smooth.copy()
    for i in range(12):
        cy,cx=np.unravel_index(remaining.argmax(),remaining.shape)
        candidates.append({'x':int(cx*4+2),'y':int(cy*4+2),'score':float(remaining[cy,cx])})
        yy,xx=np.ogrid[:remaining.shape[0],:remaining.shape[1]]
        remaining[(xx-cx)**2+(yy-cy)**2<15**2]=0
    best=candidates[0];cx,cy=best['x']//4,best['y']//4
    threshold=max(.1,best['score']*.55)
    _,labels,stats,_=cv2.connectedComponentsWithStats((smooth>=threshold).astype(np.uint8))
    label=labels[cy,cx]
    if label:
        x,y,bw,bh,_=stats[label]
        box=[max(0,int(x*4-4)),max(0,int(y*4-4)),int(bw*4+8),int(bh*4+8)]
    else:box=[best['x']-25,best['y']-25,50,50]
    marked=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    draw=ImageDraw.Draw(marked);x,y,bw,bh=box
    draw.rectangle((x,y,x+bw,y+bh),outline='red',width=4)
    draw.text((20,20),f'{path.parent.name}/{path.name}   detector score {best["score"]:.3f}',fill='yellow')
    marked.thumbnail((800,600));marked.save(output/'detections'/f'{path.parent.name}-{path.stem}.jpg',quality=88)
    return {'album':path.parent.name,'page':path.stem,'box':box,'center':[best['x'],best['y']],'score':best['score'],'candidates':candidates,'stamps':stamps}

def overlays(rows,output,name='album-overlays.png'):
    canvas=Image.new('RGB',(2000,340),'white');draw=ImageDraw.Draw(canvas)
    for ai in range(5):
        x=ai*400
        draw.text((x+12,8),f'album_{ai+1}',fill='black')
        draw.rectangle((x+1,30,x+399,329),outline='gray')
        for row in rows:
            if row['album']!=f'album_{ai+1}':continue
            cx,cy=row['center'];xx=x+cx/4;yy=30+cy/4
            draw.ellipse((xx-4,yy-4,xx+4,yy+4),fill='black')
    canvas.save(output/name)

def main():
    output=root/'output';output.mkdir(exist_ok=True)
    for name in ['detections','heatmaps']: (output/name).mkdir(exist_ok=True)
    model=joblib.load(root/'detector.joblib');model.n_jobs=1
    paths=sorted((root/'data/albums').glob('*/*.jpg'))
    rows=[];started=time.time()
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(locate,p,model,output):p for p in paths}
        for future in as_completed(jobs):
            row=future.result();rows.append(row)
            print(row['album'],row['page'],'score',round(row['score'],3),'count',len(rows),'seconds',round(time.time()-started),flush=True)
            (output/'progress.json').write_text(json.dumps(rows,indent=2))
            if len(rows)%10==0:overlays(rows,output,'progress-overlay.png')
    rows.sort(key=lambda r:(r['album'],r['page']))
    (output/'detections.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (output/'boxes.csv').open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['album','page','x','y','w','h'])
        writer.writerows([r['album'],r['page'],*r['box']] for r in rows)
    overlays(rows,output)
    print('DONE',len(rows),flush=True)

if __name__=='__main__':main()
