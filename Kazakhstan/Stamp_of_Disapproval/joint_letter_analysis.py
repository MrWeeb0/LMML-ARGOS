import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import json,time
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment,differential_evolution
from sklearn.cluster import KMeans
from features import cv2
from glyph_experiment import glyph

root=Path(__file__).parent

def points_for(letter):
    edge=(glyph(letter,160,200)>.5).astype(np.uint8);skeleton=np.zeros_like(edge)
    while edge.any():
        eroded=cv2.erode(edge,np.ones((3,3),np.uint8));opened=cv2.dilate(eroded,np.ones((3,3),np.uint8))
        skeleton|=edge-opened;edge=eroded
    y,x=np.where(skeleton>0)
    return KMeans(26,random_state=11,n_init=3).fit(np.column_stack([x/159,y/199])).cluster_centers_

def objective(params,points,maps,details=False):
    x,y,w,h=params
    if x+w>370 or y+h>290:return 1e4
    xy=np.rint(points*[w,h]+[x,y]).astype(int)
    values=maps[:,xy[:,1],xy[:,0]]
    a,b=linear_sum_assignment(-values);cost=-float(values[a,b].mean())
    return (cost,a,b,xy) if details else cost

def run(method,templates):
    results=[]
    for album in range(1,6):
        paths=sorted((root/method/'heatmaps').glob(f'album_{album}-*.npz'));maps=[]
        for path in paths:
            p=np.load(path)['heat'].astype(np.float32)
            p=cv2.GaussianBlur(p,(0,0),2);p/=p.max()+1e-8
            p=cv2.dilate(p,np.ones((11,11),np.uint8));p=cv2.GaussianBlur(p,(0,0),2)
            maps.append(np.log(np.maximum(p,1e-4)))
        maps=np.stack(maps);ranks=[]
        for letter,points in templates.items():
            best=(1e9,None)
            for w in [140,180,220,260]:
                for h in [160,200,240]:
                    for x in [50,80,110,140]:
                        for y in [20,50,80]:
                            if x+w>370 or y+h>290:continue
                            params=[x,y,w,h];v=objective(params,points,maps)
                            if v<best[0]:best=(v,params)
            ranks.append({'letter':letter,'cost':best[0],'box':best[1]})
        ranks.sort(key=lambda z:z['cost'])
        for candidate in ranks[:6]:
            bounds=[(max(lo,z-22),min(hi,z+22)) for z,lo,hi in zip(candidate['box'],[40,15,125,145],[155,100,275,255])]
            answer=differential_evolution(objective,bounds,args=(templates[candidate['letter']],maps),seed=12,popsize=6,maxiter=25,polish=False)
            candidate.update(cost=float(answer.fun),box=answer.x.tolist())
        ranks.sort(key=lambda z:z['cost']);winner=ranks[0]
        cost,a,b,xy=objective(winner['box'],templates[winner['letter']],maps,True)
        assignments=[{'page':paths[i].name,'template_point':(xy[j]*4+2).tolist(),'log_score':float(maps[i,xy[j,1],xy[j,0]])} for i,j in zip(a,b)]
        results.append({'album':album,'ranks':ranks,'assignments':assignments})
        print(method,'joint album',album,[(z['letter'],round(z['cost'],3)) for z in ranks[:6]],flush=True)
    return {'method':method,'albums':results,'leading_letters':''.join(z['ranks'][0]['letter'] for z in results),'verified_flag':None,'warning':'A fitted alphabet template does not prove the flag; all choices are exploratory and depend on the detector heatmaps.'}

if __name__=='__main__':
    templates={c:points_for(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}
    report=[run(name,templates) for name in ['pixel-output','synthetic-output']]
    (root/'joint-letter-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
