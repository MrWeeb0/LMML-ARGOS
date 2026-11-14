import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import csv,zipfile,itertools,hashlib
from concurrent.futures import ThreadPoolExecutor
import cv2,numpy as np

cv2.setNumThreads(1)
def feature(item):
 name,archive=item
 raw=archive.read(name)
 g=cv2.imdecode(np.frombuffer(raw,np.uint8),0)
 if g is None:return None
 x=cv2.resize(g,(32,32),interpolation=cv2.INTER_AREA).astype(np.float32)
 c=cv2.dct(x)[:8,:8].ravel()
 h=np.packbits(c>np.median(c[1:]))
 z=x.ravel().copy();z-=z.mean();z/=max(np.linalg.norm(z),1e-8)
 s=min(1,512/max(g.shape))
 if s<1:g=cv2.resize(g,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
 k,d=cv2.SIFT_create(nfeatures=300,contrastThreshold=.02).detectAndCompute(g,None)
 p=np.array([v.pt for v in k],np.float32)
 d=d.astype(np.uint8) if d is not None else np.empty((0,128),np.uint8)
 return name,h,z,p,d,cv2.resize(g,(128,128),interpolation=cv2.INTER_AREA),np.array([g.shape[1]/128,g.shape[0]/128],np.float32),hashlib.sha256(raw).digest()
def aligned(i,j):
 _,_,_,p,a,g,sa,_=F[i];_,_,_,q,b,h,sb,_=F[j]
 if min(len(a),len(b))<8:return False
 matches=cv2.BFMatcher().knnMatch(a,b,k=2)
 good=[x for x,y in matches if x.distance<.75*y.distance]
 if len(good)<12:return False
 src=np.array([p[x.queryIdx] for x in good])/sa
 dst=np.array([q[x.trainIdx] for x in good])/sb
 H,mask=cv2.findHomography(src,dst,cv2.RANSAC,2)
 if H is None or mask.sum()<max(12,.5*len(good)):return False
 warped=cv2.warpPerspective(g,H,(128,128))
 valid=cv2.warpPerspective(np.ones_like(g),H,(128,128))>0
 valid[:4]=False;valid[-4:]=False;valid[:,:4]=False;valid[:,-4:]=False
 if valid.mean()<.4:return False
 x=cv2.GaussianBlur(warped,(5,5),1)[valid].astype(np.float32)
 y=cv2.GaussianBlur(h,(5,5),1)[valid].astype(np.float32)
 x-=x.mean();y-=y.mean()
 norm=np.linalg.norm(x)*np.linalg.norm(y)
 return norm>0 and x@y/norm>=.98
def same(pair):
 i,j=pair
 return F[i][7]==F[j][7] or aligned(i,j) or aligned(j,i)
def main():
 global F
 workers=min(8,os.cpu_count() or 1)
 with zipfile.ZipFile('test-input.zip') as archive:
  members=sorted(n for n in archive.namelist() if not n.endswith('/') and n.lower().endswith(('.jpg','.jpeg','.png','.webp','.bmp','.tif','.tiff')) and not n.rsplit('/',1)[-1].startswith('._'))
  with ThreadPoolExecutor(workers) as pool:
   F=[v for v in pool.map(feature,((n,archive) for n in members)) if v is not None]
 F.sort(key=lambda v:v[7])
 n=len(F);pairs=set();parent=list(range(n))
 def find(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 exact={}
 for i,v in enumerate(F):
  if v[7] in exact:parent[find(i)]=find(exact[v[7]])
  else:exact[v[7]]=i
 if n>1:
  h=np.array([v[1] for v in F]);z=np.array([v[2] for v in F]);k=min(5,n-1)
  for i,row in enumerate(cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(h,h,k=k+1)):
   for m in row:
    if i!=m.trainIdx:pairs.add(tuple(sorted((i,m.trainIdx))))
  for start in range(0,n,128):
   scores=z[start:start+128]@z.T
   for i,row in enumerate(scores,start):
    for j in np.argpartition(row,-k-1)[-k-1:]:
     if i!=j:pairs.add(tuple(sorted((i,int(j)))))
  with ThreadPoolExecutor(workers) as pool:
   ordered=sorted(pairs)
   for (a,b),ok in zip(ordered,pool.map(same,ordered)):
    if ok:parent[find(a)]=find(b)
  groups={}
  for i in range(n):groups.setdefault(find(i),[]).append(F[i][0])
  pairs=sorted(pair for group in groups.values() for pair in itertools.combinations(sorted(group),2))
 else:pairs=[]
 with open('output.csv','w',newline='',encoding='utf-8') as stream:
  writer=csv.writer(stream);writer.writerow(['image_a','image_b']);writer.writerows(pairs)
if __name__=='__main__':main()
