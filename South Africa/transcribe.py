from pathlib import Path
import os
os.environ['HF_HUB_OFFLINE']='1'
import torch,numpy as np
from scipy.io import wavfile
from transformers import AutoProcessor,AutoModelForCTC
HERE=Path(__file__).resolve().parent
torch.set_num_threads(4)
name='uctnlp/omniASR-CTC-300m-v2-Zulu-Baseline'
p=AutoProcessor.from_pretrained(name,local_files_only=True)
m=AutoModelForCTC.from_pretrained(name,local_files_only=True).eval()
import sys
filename=sys.argv[1] if len(sys.argv)>1 else 'notched.wav'
sr,a=wavfile.read(HERE/filename);a=a.astype(np.float32)/32768
with (HERE/(Path(filename).stem+'_transcript.txt')).open('w') as out:
 for st in range(int(sys.argv[2]) if len(sys.argv)>2 else 0,int(sys.argv[3]) if len(sys.argv)>3 else 630,15):
  end=min(630,st+20)
  inp=p(a[st*sr:end*sr],sampling_rate=sr,return_tensors='pt')
  with torch.inference_mode(): logits=m(**inp).logits
  text=p.batch_decode(logits.argmax(-1))[0]
  line=f'{st:03d}-{end:03d}: {text}'
  print(line,flush=True);out.write(line+'\n');out.flush()
