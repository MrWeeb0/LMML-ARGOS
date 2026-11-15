import os
os.environ['OPENBLAS_NUM_THREADS']='4'
os.environ['OMP_NUM_THREADS']='4'
import csv,hashlib,json,time
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen
from pathlib import Path
import numpy as np
from scipy import ndimage
import torch
from torch import nn
from torch.nn import functional as F
from PIL import Image,ImageDraw

torch.set_num_threads(4)
root=Path(__file__).parent
out=root/'analysis'
started=time.time()

class Block(nn.Module):
 def __init__(self,inside,outside,stride=1):
  super().__init__()
  self.conv1=nn.Conv2d(inside,outside,3,stride,1,bias=False);self.bn1=nn.BatchNorm2d(outside);self.relu=nn.ReLU(inplace=True)
  self.conv2=nn.Conv2d(outside,outside,3,1,1,bias=False);self.bn2=nn.BatchNorm2d(outside)
  self.downsample=nn.Sequential(nn.Conv2d(inside,outside,1,stride,bias=False),nn.BatchNorm2d(outside)) if stride!=1 or inside!=outside else None
 def forward(self,x):
  skip=x if self.downsample is None else self.downsample(x)
  x=self.relu(self.bn1(self.conv1(x)));x=self.bn2(self.conv2(x))
  return self.relu(x+skip)

class ResNet(nn.Module):
 def __init__(self):
  super().__init__()
  self.conv1=nn.Conv2d(3,64,7,2,3,bias=False);self.bn1=nn.BatchNorm2d(64);self.relu=nn.ReLU(inplace=True);self.maxpool=nn.MaxPool2d(3,2,1)
  self.layer1=nn.Sequential(Block(64,64),Block(64,64));self.layer2=nn.Sequential(Block(64,128,2),Block(128,128))
  self.layer3=nn.Sequential(Block(128,256,2),Block(256,256));self.layer4=nn.Sequential(Block(256,512,2),Block(512,512))
  self.avgpool=nn.AdaptiveAvgPool2d((1,1));self.fc=nn.Linear(512,1000)
 def forward(self,x):
  x=self.maxpool(self.relu(self.bn1(self.conv1(x))))
  a=self.layer1(x);b=self.layer2(a);c=self.layer3(b)
  return torch.cat([F.interpolate(v,size=(32,16),mode='bilinear',align_corners=False) for v in [a,b,c]],1)

out.mkdir(exist_ok=True)
if not (out/'aligned.npz').exists():
 from main import prepare
 paths=sorted((root/'images').glob('*.png'))
 with ThreadPoolExecutor(max_workers=8) as pool:prepared=list(pool.map(prepare,paths))
 np.savez_compressed(out/'aligned.npz',images=np.stack([p[0] for p in prepared]),masks=np.stack([p[1] for p in prepared]),names=np.array([p.name for p in paths]))
weights=root/'resnet18-f37072fd.pth'
if not weights.exists():
 with urlopen('https://download.pytorch.org/models/resnet18-f37072fd.pth',timeout=120) as response:weights.write_bytes(response.read())
if not hashlib.sha256(weights.read_bytes()).hexdigest().startswith('f37072fd'):raise ValueError('Unexpected pretrained weights')
data=np.load(out/'aligned.npz');images=data['images'];names=data['names'];masks=data['masks']
cache=out/'resnet-features.npz'
if cache.exists():
 feature=np.load(cache)['features']
else:
 model=ResNet()
 model.load_state_dict(torch.load(root/'resnet18-f37072fd.pth',map_location='cpu',weights_only=True))
 model.eval()
 channels=np.sort(np.random.default_rng(0).choice(448,48,replace=False))
 parts=[]
 with torch.inference_mode():
  for start in range(0,len(images),24):
   x=torch.from_numpy(images[start:start+24].transpose(0,3,1,2).copy()).float()/255
   x=(x-torch.tensor([.485,.456,.406])[None,:,None,None])/torch.tensor([.229,.224,.225])[None,:,None,None]
   parts.append(model(x)[:,channels].permute(0,2,3,1).numpy().reshape(len(x),512,48))
   if start%240==0:print('FEATURES',start,len(images),round(time.time()-started,1),flush=True)
 feature=np.concatenate(parts)
 np.savez_compressed(cache,features=feature,names=names,channels=channels)
valid=ndimage.zoom(np.mean(masks,0).astype(np.float32),(32/256,16/64),order=1)>.8
with (root/'scores.csv').open(newline='',encoding='utf-8') as stream:old=[{'file':Path(r['image']).name} for r in csv.DictReader(stream)]
exclude={r['file'] for r in old[:56]}
keep=np.array([i for i,name in enumerate(names) if name not in exclude])
feature=feature.astype(np.float64)
for iteration in range(3):
 center=np.median(feature[keep],axis=0)
 x=feature[keep]-center
 cov=np.matmul(x.transpose(1,2,0),x.transpose(1,0,2))/(len(keep)-1)
 cov+=np.eye(48)[None]*.01
 inverse=np.linalg.inv(cov)
 delta=feature-center
 value=np.sqrt(np.maximum(np.einsum('npd,pde,npe->np',delta,inverse,delta,optimize=True),0)).reshape(-1,32,16)
 value[:,~valid]=0
 smooth=ndimage.uniform_filter(value,size=(1,3,3))
 scores=np.mean(np.partition(smooth.reshape(len(names),-1),-4,axis=1)[:,-4:],axis=1)
 keep=np.argsort(scores)[:round(len(names)*.95)]
 order=np.argsort(scores)[::-1]
 print('ITERATION',iteration,'SECONDS',round(time.time()-started,1),'TOP',[(str(names[i]),round(float(scores[i]),2)) for i in order[:12]],flush=True)
results=[{'file':str(names[i]),'score':float(scores[i]),'rank':rank+1} for rank,i in enumerate(order)]
(out/'resnet-ranking.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
np.savez_compressed(out/'resnet-maps.npz',scores=scores,maps=value.astype(np.float32),names=names)
with (root/'scores.csv').open(newline='',encoding='utf-8') as stream:geometry={Path(r['image']).name:{'angle':float(r['angle']),'box':[int(r[k]) for k in ['x0','y0','x1','y1']]} for r in csv.DictReader(stream)}
baseline=set((root/'test-output.txt').read_text().splitlines())
for page in range(3):
 sheet=Image.new('RGB',(1040,1440),'white');draw=ImageDraw.Draw(sheet)
 for j,i in enumerate(order[page*40:(page+1)*40]):
  x=(j%10)*104;y=(j//10)*360;meta=geometry[str(names[i])]
  image=Image.open(root/'images'/str(names[i])).convert('RGB').rotate(meta['angle'],resample=Image.Resampling.BILINEAR)
  image=image.crop(meta['box']).resize((96,320));sheet.paste(image,(x,y))
  tag=' *' if 'images/'+str(names[i]) in baseline else ' NEW'
  draw.text((x+2,y+322),str(names[i])[6:10]+tag,fill='black')
  draw.text((x+2,y+338),str(round(float(scores[i]),2)),fill='black')
 sheet.save(out/f'resnet-{page+1}.jpg',quality=92)
print('DONE',round(time.time()-started,1),flush=True)
