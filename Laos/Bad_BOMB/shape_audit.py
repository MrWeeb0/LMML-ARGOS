import os
os.environ['OPENBLAS_NUM_THREADS']='4'
import csv,json
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw

root=Path(__file__).parent
data=np.load(root/'analysis/aligned.npz');masks=data['masks'];names=data['names']
with (root/'scores.csv').open(newline='',encoding='utf-8') as stream:geometry={Path(r['image']).name:{'angle':float(r['angle']),'box':[int(r[k]) for k in ['x0','y0','x1','y1']]} for r in csv.DictReader(stream)}
left=np.argmax(masks,axis=2).astype(float)
right=63-np.argmax(masks[:,:,::-1],axis=2)
profile=np.concatenate([left,right],axis=1)
from sklearn.decomposition import PCA
model=PCA(12,random_state=0)
keep=np.arange(len(profile))
for repeat in range(3):
 model.fit(profile[keep])
 residual=profile-model.inverse_transform(model.transform(profile))
 median=np.median(residual[keep],0)
 spread=np.median(abs(residual[keep]-median),0)+.5
 error=abs(residual-median)/spread
 smooth=ndimage.uniform_filter1d(error,size=5,axis=1)
 scores=np.mean(np.partition(smooth,-8,axis=1)[:,-8:],axis=1)
 keep=np.argsort(scores)[:round(.95*len(scores))]
order=np.argsort(scores)[::-1]
results=[{'file':str(names[i]),'score':float(scores[i]),'rank':r+1} for r,i in enumerate(order)]
(root/'analysis/shape-ranking.json').write_text(json.dumps(results,indent=2))
baseline=set((root/'test-output.txt').read_text().splitlines())
sheet=Image.new('RGB',(1040,1440),'white');draw=ImageDraw.Draw(sheet)
for j,i in enumerate(order[:40]):
 x=j%10*104;y=j//10*360;g=geometry[str(names[i])]
 image=Image.open(root/'images'/str(names[i])).convert('RGB').rotate(g['angle'],resample=Image.Resampling.BILINEAR)
 sheet.paste(image.crop(g['box']).resize((96,320)),(x,y))
 draw.text((x+2,y+322),str(names[i])[6:10]+(' *' if 'images/'+str(names[i]) in baseline else ' NEW'),fill='black')
 draw.text((x+2,y+338),str(round(float(scores[i]),2)),fill='black')
sheet.save(root/'analysis/shape-1.jpg',quality=94)
print(json.dumps(results[:50]))
