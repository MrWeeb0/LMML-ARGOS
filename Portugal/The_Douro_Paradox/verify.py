import csv,json
from pathlib import Path
from fractions import Fraction

def main():
 result=json.loads(Path('result.json').read_text())
 with open('douro_vineyard_data.csv',encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 key=result['column'];cut=result['threshold'];cells={}
 for label,subset in [('Overall',rows),(f'<= {cut:g} km',[r for r in rows if float(r[key])<=cut]),(f'> {cut:g} km',[r for r in rows if float(r[key])>cut])]:
  arms={a:[int(r['harvest_success']) for r in subset if r['treatment']==a] for a in ['control','treatment']}
  rates={a:Fraction(sum(v),len(v)) for a,v in arms.items()}
  assert rates['treatment']>rates['control'] if label=='Overall' else rates['control']>rates['treatment']
  saved=result['overall'] if label=='Overall' else result['groups'][label]
  for a,v in arms.items():assert saved[a]['successes']==sum(v) and saved[a]['plots']==len(v)
  cells[label]={a:{'fraction':str(rate),'percent':float(rate)*100} for a,rate in rates.items()}
 for a in ['control','treatment']:
  for field in ['successes','plots']:assert sum(t[a][field] for t in result['groups'].values())==result['overall'][a][field]
 check={'passed':True,'rows':len(rows),'complete_partition':sum(t[a]['plots'] for t in result['groups'].values() for a in t)==len(rows),'exact_rates':cells}
 assert check['complete_partition']
 Path('verification.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
 print('Exact-fraction verification passed')

if __name__=='__main__':main()
