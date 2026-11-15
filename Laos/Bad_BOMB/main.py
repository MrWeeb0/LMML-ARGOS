import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import csv,json,re,sys,warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

root=Path(__file__).parent
warnings.filterwarnings('ignore',message='All-NaN slice encountered')

def prepare(path):
 a=np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
 r,g,b=a.transpose(2,0,1)
 mask=(g>r*1.08+2)&(g>b*1.08+2)
 mask[:,:100]=False;mask[:,412:]=False
 padded=np.pad(mask,((20,20),(5,5)))
 mask=ndimage.binary_closing(padded,structure=np.ones((35,7)))[20:-20,5:-5]
 labels,count=ndimage.label(mask)
 sizes=np.bincount(labels.ravel());sizes[0]=0
 mask=labels==sizes.argmax()
 mask=ndimage.binary_fill_holes(mask)
 y,x=np.nonzero(mask)
 if len(y)<1000:raise ValueError('No object '+str(path))
 v=np.linalg.eigh(np.cov(np.stack([x,y])))[1][:,-1]
 if v[1]<0:v=-v
 angle=-np.degrees(np.arctan2(v[0],v[1]))
 image=Image.fromarray(a.astype(np.uint8)).rotate(float(angle),resample=Image.Resampling.BILINEAR,fillcolor=(128,128,128))
 mask=np.asarray(Image.fromarray(mask).rotate(float(angle),resample=Image.Resampling.NEAREST))
 y,x=np.nonzero(mask)
 box=(max(0,int(x.min())-3),max(0,int(y.min())-3),min(512,int(x.max())+4),min(512,int(y.max())+4))
 crop=np.asarray(image.crop(box).resize((64,256),Image.Resampling.BILINEAR)).astype(np.float32)/255
 foreground=np.asarray(Image.fromarray(mask).crop(box).resize((64,256),Image.Resampling.NEAREST))
 scale=.27/max(float(np.median(crop[foreground,1])),.02)
 crop=np.clip(crop*scale,0,1);crop[~foreground]=.25
 return (crop*255).astype(np.uint8),foreground,{'file':path.name,'angle':float(angle),'box':box,'scale':scale}

def features(images,masks):
 a=images.astype(np.float32)/255
 r,g,b=a.transpose(3,0,1,2)
 u=(g-r)/(g+r+.01);v=(g-b)/(g+b+.01)
 core=ndimage.binary_erosion(masks,structure=np.ones((1,7,7)))
 profile=np.median(u[:,:,20:44],axis=2)
 band=(profile<.055)&(np.arange(256)[None,:]>180)&(np.arange(256)[None,:]<235)
 core&=~ndimage.binary_dilation(band,structure=np.ones((1,3)))[:,:,None]
 core[:,:5]=False;core[:,251:]=False
 return np.stack([u,v],axis=-1),core

def fit(values,core):
 median=np.nanmedian(np.where(core[:,:,:,None],values,np.nan),axis=0)
 spread=np.nanmedian(np.where(core[:,:,:,None],abs(values-median),np.nan),axis=0)
 return np.nan_to_num(median),np.nan_to_num(spread)

def score(values,core,median,spread):
 error=np.maximum(median-values-.025,0)/(spread+.025)
 error=np.nan_to_num(np.sqrt(np.sum(error*error,axis=3)))
 error[~core]=0
 patch=ndimage.uniform_filter(error,size=(1,5,5))
 return np.mean(np.partition(patch.reshape(len(values),-1),-12,axis=1)[:,-12:],axis=1)

def check():
 if (root/'revision.json').exists():
  from refine import check as revision_check
  return revision_check()
 manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
 names={v['name'] for v in manifest}
 lines=(root/'test-output.txt').read_text(encoding='utf-8').splitlines()
 if len(lines)!=28 or len(set(lines))!=28:raise ValueError('Expected 28 unique paths')
 if any(not re.fullmatch(r'images/image_\d{4}\.png',line) or line.split('/')[1] not in names for line in lines):raise ValueError('Invalid image path')
 with (root/'scores.csv').open(newline='',encoding='utf-8') as stream:ranking=list(csv.DictReader(stream))
 if len(ranking)!=len(names) or {r['image'] for r in ranking}!={'images/'+name for name in names}:raise ValueError('Ranking does not cover the manifest')
 if any(float(a['score'])<float(b['score']) for a,b in zip(ranking,ranking[1:])):raise ValueError('Ranking is not sorted')
 if set(lines)!={r['image'] for r in ranking[:28]}:raise ValueError('Output disagrees with ranking')
 model=np.load(root/'model.npz')
 if any(model[k].shape!=(256,64,2) or not np.isfinite(model[k]).all() for k in ['median','spread']):raise ValueError('Invalid trained model')
 print(json.dumps({'paths':len(lines),'unique':len(set(lines)),'known_images':len(names),'cutoff_score':float(ranking[27]['score']),'evaluation_score':None}))

def run(predict=False):
 paths=sorted((root/'images').glob('*.png'))
 if len(paths)<28:raise ValueError('Run download.py first')
 with ThreadPoolExecutor(max_workers=8) as pool:items=list(pool.map(prepare,paths))
 images=np.stack([v[0] for v in items]);masks=np.stack([v[1] for v in items])
 values,core=features(images,masks)
 if predict:
  model=np.load(root/'model.npz');median=model['median'];spread=model['spread']
 else:
  median,spread=fit(values,core)
  np.savez_compressed(root/'model.npz',median=median,spread=spread)
 scores=score(values,core,median,spread)
 order=np.argsort(scores)[::-1]
 selected=sorted('images/'+paths[i].name for i in order[:28])
 (root/'test-output.txt').write_bytes(('\n'.join(selected)+'\n').encode())
 with (root/'scores.csv').open('w',newline='',encoding='utf-8') as stream:
  writer=csv.writer(stream);writer.writerow(['rank','image','score','angle','x0','y0','x1','y1'])
  for rank,i in enumerate(order):writer.writerow([rank+1,'images/'+paths[i].name,float(scores[i]),items[i][2]['angle'],*items[i][2]['box']])
 summary={'method':'robust aligned chromaticity atlas','images':len(paths),'selected':len(selected),'selection':selected,'canonical_size':[64,256],'erosion_size':7,'patch_size':5,'top_patch_pixels':12,'model_fitted':not predict,'ground_truth_available':False,'flag_available':False}
 (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 if (root/'revision.json').exists():
  from refine import run as refine_run
  refine_run()
 else:check()

if __name__=='__main__':
 if '--check' in sys.argv:check()
 else:run('--predict' in sys.argv)
