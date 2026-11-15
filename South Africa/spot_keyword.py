import os
os.environ['HF_HUB_OFFLINE']='1'
from pathlib import Path
import torch,numpy as np,json
from scipy.io import wavfile
from transformers import AutoProcessor,AutoModelForCTC
h=Path(__file__).resolve().parent;torch.set_num_threads(3)
p=AutoProcessor.from_pretrained('uctnlp/omniASR-CTC-300m-v2-Zulu-Baseline',local_files_only=True);m=AutoModelForCTC.from_pretrained('uctnlp/omniASR-CTC-300m-v2-Zulu-Baseline',local_files_only=True).eval()
sr,a=wavfile.read(h/'notched.wav');a=a.astype(np.float32)/32768
v=p.tokenizer.get_vocab();blank=v['<pad>'];ids=[v[c] for c in 'ikhodi'];ext=[blank]+sum(([t,blank] for t in ids),[])
rows=[]
for st in range(0,630,15):
 q=a[st*sr:min(len(a),(st+20)*sr)]
 with torch.inference_mode():lp=m(**p(q,sampling_rate=sr,return_tensors='pt')).logits[0].log_softmax(-1).numpy()
 lp-=lp.max(axis=1,keepdims=True);n=len(lp);dp=np.full(len(ext),-1e8);starts=np.zeros(len(ext),int);hits=[]
 for t in range(n):
  nxt=np.full_like(dp,-1e8);ns=starts.copy();nxt[0]=0;ns[0]=t
  for j in range(1,len(ext)):
   src=[j,j-1]
   if j>1 and ext[j]!=blank and ext[j]!=ext[j-2]:src+=[j-2]
   k=max(src,key=lambda k:dp[k]);nxt[j]=dp[k]+lp[t,ext[j]];ns[j]=starts[k]
  dp,starts=nxt,ns
  if t-starts[-2]>8:hits.append((float(dp[-2]),st+starts[-2]*len(q)/sr/n,st+t*len(q)/sr/n))
 hits.sort(reverse=True)
 chosen=[]
 for z in hits:
  if not any(abs(z[2]-v[2])<1 for v in chosen):chosen.append(z)
  if len(chosen)>=3:break
 text=p.batch_decode(torch.tensor(lp).argmax(-1)[None])[0]
 rows.extend(chosen);print(st,chosen,text,flush=True)
 (h/'keyword_candidates.json').write_text(json.dumps(sorted(rows,reverse=True),indent=2))
