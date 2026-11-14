import csv,json,hashlib
from pathlib import Path
from collections import defaultdict

def counts(rows):
 v=[0,0,0,0]
 for r in rows:
  i=2*(r['treatment']=='treatment');v[i]+=int(r['harvest_success']);v[i+1]+=1
 return v

def reversal(v):
 return v[1]>0 and v[3]>0 and v[0]*v[3]>v[2]*v[1]

def rates(v):
 return {a:{'successes':v[i],'plots':v[i+1],'rate':v[i]/v[i+1]} for a,i in [('control',0),('treatment',2)]}

def screen(rows):
 results=[]
 for column in rows[0]:
  if column in ['plot_id','treatment','harvest_success']:continue
  try:values={r[column]:float(r[column]) for r in rows};numeric=True
  except ValueError:values={r[column]:r[column] for r in rows};numeric=False
  groups=defaultdict(lambda:[0,0,0,0])
  for r in rows:
   v=groups[values[r[column]]];i=2*(r['treatment']=='treatment');v[i]+=int(r['harvest_success']);v[i+1]+=1
  if numeric:
   total=counts(rows);left=[0,0,0,0];cuts=[]
   for value in sorted(groups)[:-1]:
    left=[a+b for a,b in zip(left,groups[value])];right=[a-b for a,b in zip(total,left)]
    if reversal(left) and reversal(right):cuts.append(value)
   results.append({'column':column,'kind':'numeric','levels':len(groups),'reversing_thresholds':cuts,'complete_reversal':bool(cuts)})
  else:results.append({'column':column,'kind':'categorical','levels':len(groups),'complete_reversal':all(reversal(v) for v in groups.values())})
 return results

def main():
 path=Path('douro_vineyard_data.csv')
 with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 assert len(rows)==3543 and len({r['plot_id'] for r in rows})==len(rows)
 assert all(r['treatment'] in ['control','treatment'] and r['harvest_success'] in ['0','1'] and all(r.values()) for r in rows)
 overall=counts(rows);assert overall[2]*overall[1]>overall[0]*overall[3]
 scanned=screen(rows);found=[r for r in scanned if r['complete_reversal']]
 assert len(found)==1 and found[0]['kind']=='numeric'
 column=found[0]['column'];cut=max(found[0]['reversing_thresholds'])
 groups={label:[r for r in rows if (float(r[column])<=cut)==side] for label,side in [(f'<= {cut:g} km',True),(f'> {cut:g} km',False)]}
 assert sum(map(len,groups.values()))==len(rows) and all(reversal(counts(g)) for g in groups.values())
 flag='SIGMOID_'+column.upper()
 result={'flag':flag,'column':column,'threshold':cut,'rows':len(rows),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'overall':rates(overall),'groups':{k:rates(counts(g)) for k,g in groups.items()},'screening':scanned,'threshold_selection':'largest observed numeric boundary producing a strict reversal in both groups'}
 easier=max(result['groups'],key=lambda k:sum(v['successes'] for v in result['groups'][k].values())/sum(v['plots'] for v in result['groups'][k].values()))
 weights={a:result['groups'][easier][a]['plots']/result['overall'][a]['plots'] for a in ['control','treatment']}
 result['pooling_explanation']=f"Treatment has {weights['treatment']:.2%} of its plots in the higher-success {easier} group, versus {weights['control']:.2%} for control; pooling these differently weighted groups puts treatment ahead despite its lower success rate within both groups."
 Path('result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 Path('flag.txt').write_text(flag+'\n',encoding='utf-8')
 with open('rates.csv','w',encoding='utf-8',newline='') as f:
  w=csv.writer(f);w.writerow(['group','treatment','successes','plots','success_rate'])
  for label,table in [('Overall',result['overall']),*result['groups'].items()]:
   for arm,v in table.items():w.writerow([label,arm,v['successes'],v['plots'],v['rate']])
 print(flag)
 print(json.dumps({k:result[k] for k in ['overall','groups']},indent=2))

if __name__=='__main__':main()
