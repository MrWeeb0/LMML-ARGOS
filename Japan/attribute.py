import csv
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.linalg import eigh

root=Path(__file__).resolve().parent
pack=np.load(root/"metadata.npz")
K=np.load(root/"kernel.npy").astype(float)
names,labels,week,files=(pack[f] for f in ("names","labels","weeks","test"))
n=len(labels)
m=len(files)
N=n+m
r0=(K[0]+K[0].T)/2
r1=(K[1]+K[1].T)/2
raw=r0-r1
max2=K[:2].max(axis=0)
for p in (r0,r1,raw,max2):
    np.fill_diagonal(p,0)

def train(active,query,o_v=0,smooth=.3,repeat=0):
    a=np.zeros((N,len(names)))
    d=np.zeros_like(a,dtype=int)
    for j,h in enumerate(names):
        match=active[labels[active]==h]
        _,vec=eigh(raw[np.ix_(match,match)])
        x=vec[:,-1]
        d[match,j]=(x<0)^(x[0]<0)
        a[match,j]=1
        base=max2[np.ix_(match,match)].mean(axis=0)
        if smooth:
            a[match,j]=1-smooth+smooth*np.clip((base/np.mean(base))**1.5,.05,3)
    a_old=a.copy()
    for it in range(repeat+1):
        scores=[]
        ori=[]
        for j,h in enumerate(names):
            take=np.flatnonzero(a[:,j])
            x=a[take,j]
            v=d[take,j]
            comparison=K[np.bitwise_xor(np.arange(2)[:,None],v[None,:])[:,None,:],
                         query[None,:,None],take[None,None,:]].copy()
            comparison[:,query[:,None]==take[None,:]]=0
            pc=comparison@x/(x.sum()-a[query,j])
            if o_v:
                second=np.maximum(0,comparison-.0018)**2@x/(x.sum()-a[query,j])
                pc+=o_v*np.sqrt(second)
            scores.append(pc.max(axis=0))
            ori.append(pc.argmax(axis=0))
        scores=np.array(scores).T
        ori=np.array(ori).T
        if it==repeat:
            return scores,ori
        best=scores.argmax(axis=1)
        gap=np.sort(scores,axis=1)[:,-1]-np.sort(scores,axis=1)[:,-2]
        gate=np.flatnonzero((gap>.00065)&(scores.max(axis=1)>.0013))
        a=a_old.copy()
        a[query[gate],best[gate]]=np.clip(gap[gate]*130,.02,.55)
        d[query[gate],best[gate]]=ori[gate,best[gate]]

methods=((0,0,0),(0,.3,0),(0,.3,3),(.2,.3,3),(.4,.3,3),(.7,.3,3),(0,.6,3))
best_count,best_method=0,0
for k,pars in enumerate(methods):
    S=np.zeros((n,len(names)))
    for w in np.unique(week):
        query=np.flatnonzero(week==w)
        score,_=train(np.flatnonzero(week!=w),np.r_[query,np.arange(n,N)],*pars)
        S[query]=score[:len(query)]
    pred=names[S.argmax(axis=1)]
    count=int((pred==labels).sum())
    print("validation",k,pars,count,"/",n,flush=True)
    if count>best_count:
        best_count,best_method=count,k
print("Selected method",best_method,"validation",best_count,"/",n,flush=True)
s,orientation=train(np.arange(n),np.arange(n,N),*methods[best_method])
print("Unconstrained predictions",dict(Counter(names[s.argmax(axis=1)])),flush=True)
out=np.full(m,-1)
for w in range(8,13):
    take=np.flatnonzero([int(f[1:3])==w for f in files])
    slots=np.repeat(np.arange(len(names)),[9 if h=="toorisugari" else 4 for h in names])
    a,b=linear_sum_assignment(-s[np.ix_(take,slots)])
    out[take[a]]=slots[b]
with (root/"attribution.csv").open("w",newline="") as stream:
    writer=csv.writer(stream)
    writer.writerow(["file","camera","assigned","orientation",*names])
    for i in range(m):
        j=s[i].argmax()
        writer.writerow([files[i],names[j],names[out[i]],orientation[i,out[i]],*s[i]])
with (root/"toorisugari.csv").open("w",newline="") as stream:
    writer=csv.writer(stream)
    writer.writerow(["file","week","orientation"])
    for i in range(m):
        if names[out[i]]=="toorisugari":
            writer.writerow([files[i],int(files[i][1:3]),orientation[i,out[i]]])
            print(files[i],"rotation",180*orientation[i,out[i]],flush=True)
print("Flag not recovered",flush=True)
