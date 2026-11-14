import json,re,struct,sys
from pathlib import Path
import numpy as np

def load(path):
 raw=Path(path).read_bytes()
 n=struct.unpack('<Q',raw[:8])[0]
 header=json.loads(raw[8:8+n])
 tensors={}
 for name,entry in header.items():
  if name=='__metadata__':continue
  start,end=entry['data_offsets'];count=int(np.prod(entry['shape']))
  if entry['dtype']!='F32' or end-start!=4*count or 8+n+end>len(raw):raise ValueError('Invalid F32 tensor')
  tensors[name]=np.frombuffer(raw,dtype='<f4',offset=8+n+start,count=count).reshape(entry['shape'])
 return raw,header,tensors,8+n

def extract(model):
 raw,header,tensors,base=model
 embedding=tensors['embedding.weight'];width=embedding.shape[1]
 values=embedding[128:].ravel().astype(np.float64)*1024+128
 mask=np.isfinite(values)&(values==np.rint(values))&(values>=32)&(values<=126)
 bounds=np.flatnonzero(np.diff(np.r_[False,mask,False])).reshape(-1,2)
 found=[]
 for start,end in bounds:
  text=bytes(values[start:end].astype(np.uint8)).decode('ascii')
  if re.fullmatch(r'SIGMOID_[A-Z]+',text):
   index=128*width+int(start);row,column=divmod(index,width)
   found.append({'flag':text,'tensor':'embedding.weight','row':row,'column':column,'length':int(end-start),'byte_offset':base+header['embedding.weight']['data_offsets'][0]+4*index,'byte_length':4*int(end-start),'scale':1024,'offset':128,'ascii_codes':values[start:end].astype(int).tolist(),'raw_flag_present':text.encode() in raw})
 if len(found)!=1:raise ValueError('Expected one encoded flag')
 return found[0]

if __name__=='__main__':
 print(extract(load(sys.argv[1] if len(sys.argv)>1 else Path(__file__).with_name('model.safetensors')))['flag'])
