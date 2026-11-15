from pathlib import Path
import sys
import numpy as np
from PIL import Image
from scipy.fft import rfft2,irfft2
from scipy.ndimage import gaussian_filter,uniform_filter

root=Path(__file__).resolve().parent
data=Path(sys.argv[1]) if len(sys.argv)>1 else root/"dataset"
train=sorted(data.glob("credited/*/*.jpg"))
test=sorted(data.glob("anonymous/*.jpg"))
paths=train+test
labels=np.array([p.parent.name for p in train])
names=np.unique(labels)
weeks=np.array([int(p.name[1:3]) for p in train])
if len(train)!=108 or len(test)!=145:
    raise ValueError("Expected 108 credited and 145 anonymous JPEGs")
np.savez_compressed(root/"metadata.npz",labels=labels,names=names,weeks=weeks,
                    train=np.array([str(p) for p in train]),test=np.array([p.name for p in test]))
H,W=880,1248
y,x=slice(40,920),slice(16,1264)
radius=np.hypot(np.fft.fftfreq(H)[:,None],np.fft.rfftfreq(W)[None,:])

def load(p):
    im=Image.open(p)
    im.draft("YCbCr",im.size)
    im=np.array(im)[:,:,0].astype(np.float32)
    blurred=gaussian_filter(im,.95)
    detail=(im-blurred)[y,x].copy()
    sigma=np.sqrt(6.25+np.maximum(0,uniform_filter(detail*detail,13)))
    detail=np.clip(detail,-3*sigma,3*sigma)/sigma**1.65
    detail*=np.clip(blurred[y,x]/80,.15,1)*np.clip((255-blurred[y,x])/35,.05,1)
    detail-=detail.mean(axis=0)
    detail-=detail.mean(axis=1,keepdims=True)
    chunks=detail.reshape(H//8,8,W//8,8)
    chunks-=chunks.mean(axis=(0,2),keepdims=True)
    return detail/np.linalg.norm(detail)

spec=np.lib.format.open_memmap(root/"spectrum.npy",mode="w+",dtype=np.complex64,
                               shape=(len(paths),H,W//2+1))
pool=np.zeros(spec.shape[1:],np.float32)
for i,p in enumerate(paths):
    sample=rfft2(load(p),workers=2)
    spec[i]=sample
    pool+=np.abs(sample)**2
pool=gaussian_filter(pool/len(paths),6)
pool=(pool+pool[(-np.arange(H))%H])/2
cut=np.interp(radius,[0,.24,.28,.36,.38,.47,.49,.55,.69],[0,0,.3,.6,1,1,.6,.5,.25])
filt=np.sqrt(cut/np.maximum(.08,pool)).astype(np.float32)
A=np.lib.format.open_memmap(root/"vectors.npy",mode="w+",dtype=np.float32,shape=(len(paths),H,W))
for i,row in enumerate(spec):
    z=irfft2(row*filt,workers=2)
    A[i]=z/max(1e-9,np.linalg.norm(z))
A.flush()
del spec
F=A.reshape(len(paths),-1)
K=[]
for ds in ((1,1),(-1,-1),(1,-1),(-1,1)):
    out=np.zeros((len(A),len(A)),np.float32)
    for i in range(0,len(A),12):
        out[i:i+12]=A[i:i+12,::ds[0],::ds[1]].copy().reshape(-1,H*W)@F.T
    K.append((out+out.T)/2)
np.save(root/"kernel.npy",np.array(K))
print("Prepared",len(train),"credited and",len(test),"anonymous photos",flush=True)
