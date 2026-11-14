import csv,hashlib,json,sys
from itertools import permutations
from pathlib import Path
import numpy as np
from main import extract,load

def audit(root):
 root=Path(root);model=load(root/'model.safetensors');t=model[2]
 rows=list(csv.DictReader((root/'corpus.csv').open(encoding='utf-8',newline='')))
 if len(rows)!=2400 or any(len(r['text'])!=64 for r in rows):raise ValueError('Unexpected corpus')
 ids=np.array([list(r['text'].encode('ascii')) for r in rows],dtype=np.uint8)
 embedding=t['embedding.weight'];weight=t['classifier.weight'];bias=t['classifier.bias']
 logits=embedding[ids].mean(1)@weight.T+bias
 prediction=logits.argmax(1)
 names=sorted({r['register'] for r in rows})
 labels=np.array([r['register'] for r in rows])
 order=max(permutations(names),key=lambda p:sum(p[i]==label for i,label in zip(prediction,labels)))
 confusion=[[int(np.sum((labels==name)&(prediction==i))) for i in range(3)] for name in order]
 correct=sum(confusion[i][i] for i in range(3))
 changed=embedding.copy()
 changed[128:]=np.random.default_rng(0).normal(0,1000,size=changed[128:].shape)
 altered=changed[ids].mean(1)@weight.T+bias
 if not np.array_equal(logits,altered):raise ValueError('Unused rows affected logits')
 result={'extraction':extract(model),'model_sha256':hashlib.sha256(model[0]).hexdigest(),'corpus_sha256':hashlib.sha256((root/'corpus.csv').read_bytes()).hexdigest(),'tensor_shapes':{k:list(v.shape) for k,v in t.items()},'records':len(rows),'record_length':64,'largest_observed_byte':int(ids.max()),'output_labels':list(order),'class_counts':{name:int(np.sum(labels==name)) for name in names},'correct':correct,'accuracy':correct/len(rows),'confusion_matrix':confusion,'unused_rows':[128,256],'logits_identical_after_unused_rows_changed':True,'maximum_logit_change':float(np.max(np.abs(logits-altered)))}
 return result

if __name__=='__main__':
 root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
 result=audit(root)
 (root/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,indent=2))
