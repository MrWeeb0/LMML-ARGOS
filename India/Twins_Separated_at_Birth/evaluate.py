import csv,json,sys
def pairs(path):
 with open(path,newline='',encoding='utf-8') as stream:
  rows=csv.DictReader(stream)
  if rows.fieldnames!=['image_a','image_b']:raise ValueError('Invalid CSV header')
  return {tuple(sorted((r['image_a'],r['image_b']))) for r in rows}
truth=pairs(sys.argv[1] if len(sys.argv)>1 else 'train-output.csv')
pred=pairs(sys.argv[2] if len(sys.argv)>2 else 'output.csv')
tp=len(truth&pred)
r=dict(expected=len(truth),predicted=len(pred),true_positives=tp,false_positives=len(pred-truth),false_negatives=len(truth-pred),self_pairs=sum(a==b for a,b in pred),precision=tp/len(pred) if pred else 0,recall=tp/len(truth) if truth else 0,f1=2*tp/(len(truth)+len(pred)) if truth or pred else 0)
print(json.dumps(r,indent=2))
