import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import csv,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment,differential_evolution
from sklearn.cluster import KMeans
from PIL import Image,ImageDraw
from features import cv2

root=Path(__file__).parent
STROKES={
'A':[[(0,1),(.5,0),(1,1)],[(.25,.5),(.75,.5)]],
'B':[[(0,1),(0,0),(.75,0),(1,.2),(1,.35),(.75,.5),(0,.5)],[(0,.5),(.75,.5),(1,.7),(1,.85),(.75,1),(0,1)]],
'C':[[(1,0),(0,0),(0,1),(1,1)]],
'D':[[(0,0),(0,1),(.65,1),(1,.75),(1,.25),(.65,0),(0,0)]],
'E':[[(1,0),(0,0),(0,1),(1,1)],[(0,.5),(.8,.5)]],
'F':[[(0,1),(0,0),(1,0)],[(0,.5),(.8,.5)]],
'G':[[(1,0),(0,0),(0,1),(1,1),(1,.5),(.55,.5)]],
'H':[[(0,0),(0,1)],[(1,0),(1,1)],[(0,.5),(1,.5)]],
'I':[[(0,0),(1,0)],[(.5,0),(.5,1)],[(0,1),(1,1)]],
'J':[[(0,0),(1,0),(1,.8),(.8,1),(.2,1),(0,.8)]],
'K':[[(0,0),(0,1)],[(1,0),(0,.5),(1,1)]],
'L':[[(0,0),(0,1),(1,1)]],
'M':[[(0,1),(0,0),(.5,.5),(1,0),(1,1)]],
'N':[[(0,1),(0,0),(1,1),(1,0)]],
'O':[[ (.2,0),(.8,0),(1,.2),(1,.8),(.8,1),(.2,1),(0,.8),(0,.2),(.2,0)]],
'P':[[(0,1),(0,0),(1,0),(1,.5),(0,.5)]],
'Q':[[ (.2,0),(.8,0),(1,.2),(1,.8),(.8,1),(.2,1),(0,.8),(0,.2),(.2,0)],[(.6,.65),(1,1)]],
'R':[[(0,1),(0,0),(1,0),(1,.5),(0,.5)],[(.5,.5),(1,1)]],
'S':[[(1,0),(0,0),(0,.5),(1,.5),(1,1),(0,1)]],
'T':[[(0,0),(1,0)],[(.5,0),(.5,1)]],
'U':[[(0,0),(0,.8),(.2,1),(.8,1),(1,.8),(1,0)]],
'V':[[(0,0),(.5,1),(1,0)]],
'W':[[(0,0),(.2,1),(.5,.5),(.8,1),(1,0)]],
'X':[[(0,0),(1,1)],[(1,0),(0,1)]],
'Y':[[(0,0),(.5,.5),(1,0)],[(.5,.5),(.5,1)]],
'Z':[[(0,0),(1,0),(0,1),(1,1)]]
}

def anchors(strokes):
    values=[]
    for line in strokes:
        for a,b in zip(line,line[1:]):
            a=np.array(a);b=np.array(b);n=max(3,round(np.linalg.norm(a-b)*200))
            values.append(a[None]+np.linspace(0,1,n)[:,None]*(b-a)[None])
    return KMeans(26,random_state=7,n_init=3).fit(np.concatenate(values)).cluster_centers_

def letter_cost(params,points,maps,details=False):
    x,y,w,h=params
    xy=np.rint(points*[w,h]+[x,y]).astype(int)
    values=maps[:,xy[:,1],xy[:,0]]
    a,b=linear_sum_assignment(-values);cost=-float(values[a,b].mean())
    return (cost,a,b,xy) if details else cost

def global_cost(params,templates,groups,details=False):
    x,y,w,h=params
    if x<30 or y<10 or x+w>370 or y+h>290:return 1e4
    ranks=[]
    for maps in groups:
        table=sorted([{'letter':c,'cost':letter_cost(params,p,maps)} for c,p in templates.items()],key=lambda z:z['cost'])
        ranks.append(table)
    score=float(np.mean([v[0]['cost'] for v in ranks]))
    return (score,ranks) if details else score

def run(method,templates):
    groups=[];raw_groups=[];path_groups=[]
    for album in range(1,6):
        paths=sorted((root/method/'heatmaps').glob(f'album_{album}-*.npz'));maps=[];raw=[]
        for path in paths:
            p=np.load(path)['heat'].astype(np.float32)
            p=cv2.GaussianBlur(p,(0,0),2);p/=p.max()+1e-8;raw.append(p)
            p=cv2.dilate(p,np.ones((11,11),np.uint8));p=cv2.GaussianBlur(p,(0,0),2)
            maps.append(np.log(np.maximum(p,1e-4)))
        groups.append(np.stack(maps));raw_groups.append(np.stack(raw));path_groups.append(paths)
    best=(1e9,None)
    for w in [140,170,200,230,260]:
        for h in [160,190,220,250]:
            for dx in [-30,0,30]:
                for dy in [-20,0,20]:
                    params=[(400-w)/2+dx,(300-h)/2+dy,w,h]
                    cost=global_cost(params,templates,groups)
                    if cost<best[0]:best=(cost,params)
    bounds=[(max(lo,z-24),min(hi,z+24)) for z,lo,hi in zip(best[1],[30,10,120,140],[160,100,280,260])]
    fitted=differential_evolution(global_cost,bounds,args=(templates,groups),seed=8,popsize=6,maxiter=25,polish=False)
    params=fitted.x.tolist();cost,ranks=global_cost(params,templates,groups,True)
    word=''.join(r[0]['letter'] for r in ranks)
    print('shared layout',method,'letters',word,'cost',round(cost,4),'box',params,flush=True)
    canvas=Image.new('RGB',(2000,340),'white');draw=ImageDraw.Draw(canvas);assignments=[]
    for ai,(maps,raw,paths,table) in enumerate(zip(groups,raw_groups,path_groups,ranks)):
        letter=table[0]['letter'];_,a,b,xy=letter_cost(params,templates[letter],maps,True)
        draw.text((ai*400+8,8),f'album {ai+1}: fitted {letter}',fill='black')
        x,y,w,h=params
        for line in STROKES[letter]:
            draw.line([(ai*400+x+u*w,30+y+v*h) for u,v in line],fill=(190,190,190),width=2)
        for i,j in zip(a,b):
            px,py=map(int,xy[j]);x0=max(0,px-11);x1=min(400,px+12);y0=max(0,py-11);y1=min(300,py+12)
            crop=raw[i,y0:y1,x0:x1];dy,dx=np.unravel_index(crop.argmax(),crop.shape);cx,cy=int(x0+dx),int(y0+dy)
            ry,rx=np.unravel_index(raw[i].argmax(),raw[i].shape)
            draw.ellipse((ai*400+rx-2,30+ry-2,ai*400+rx+2,30+ry+2),fill=(120,120,120))
            draw.ellipse((ai*400+cx-3,30+cy-3,ai*400+cx+3,30+cy+3),fill=(20,70,200))
            assignments.append({'album':f'album_{ai+1}','page':paths[i].name,'center':[cx*4+2,cy*4+2],'detector_relative_score':float(raw[i,cy,cx]),'template_point':(xy[j]*4+2).tolist()})
    output=root/'shared-geometry';output.mkdir(exist_ok=True)
    canvas.save(output/(method+'.png'))
    (output/(method+'-assignments.json')).write_text(json.dumps(assignments,indent=2)+'\n')
    return {'method':method,'common_box':params,'average_cost':cost,'leading_letters':word,'albums':[{'album':i+1,'ranks':v} for i,v in enumerate(ranks)],'verified_flag':None,'caution':'Alphabet fitting is a structured hypothesis, not verification of the flag. Raw detections and geometric adjustments are preserved separately.'}

if __name__=='__main__':
    templates={c:anchors(v) for c,v in STROKES.items()}
    results=[run(name,templates) for name in ['pixel-output','synthetic-output']]
    (root/'shared-geometry/results.json').write_text(json.dumps(results,indent=2)+'\n')
