import csv,json,sys
from pathlib import Path
root=Path(__file__).parent
folder=root/'revision2';folder.mkdir(exist_ok=True)

def choose(rows):
 baseline=sorted(rows,key=lambda r:int(r['color_rank']))[:28]
 original={r['image'] for r in baseline}
 retained=[r['image'] for r in baseline[:26]]
 novel=sorted((r for r in rows if r['image'] not in original),key=lambda r:(int(r['neural_rank'])*int(r['shape_rank']),r['image']))[:2]
 return sorted(retained+[r['image'] for r in novel]),sorted(original),[r['image'] for r in novel]

def read():
 with (folder/'rankings.csv').open(newline='',encoding='utf-8') as stream:return list(csv.DictReader(stream))

def check():
 rows=read();selection,baseline,added=choose(rows)
 actual=(root/'test-output.txt').read_text(encoding='utf-8').splitlines()
 known={'images/'+x['name'] for x in json.loads((root/'manifest.json').read_text(encoding='utf-8'))}
 if len(actual)!=28 or len(set(actual))!=28 or sorted(actual)!=selection or not set(actual)<=known:raise ValueError('Invalid revised submission')
 print(json.dumps({'version':2,'unique_paths':28,'removed':sorted(set(baseline)-set(selection)),'added':sorted(added),'previous_matches':19,'previous_total':28,'revised_matches':None}))

def run(refresh=False):
 if refresh or not (folder/'rankings.csv').exists():
  with (root/'scores.csv').open(newline='',encoding='utf-8') as stream:color=list(csv.DictReader(stream))
  neural={r['file']:r for r in json.loads((root/'analysis/resnet-ranking.json').read_text())}
  shape={r['file']:r for r in json.loads((root/'analysis/shape-ranking.json').read_text())}
  with (folder/'rankings.csv').open('w',newline='',encoding='utf-8') as stream:
   writer=csv.writer(stream);writer.writerow(['image','color_rank','neural_rank','shape_rank','rank_product'])
   for r in color:
    name=Path(r['image']).name;n=neural[name]['rank'];s=shape[name]['rank']
    writer.writerow([r['image'],r['rank'],n,s,n*s])
 rows=read();selection,baseline,added=choose(rows)
 (root/'baseline-output.txt').write_bytes(('\n'.join(baseline)+'\n').encode())
 content=('\n'.join(selection)+'\n').encode()
 (root/'test-output.txt').write_bytes(content);(folder/'test-output.txt').write_bytes(content)
 report={'version':2,'method':'retain 26 strongest color candidates and add 2 novel candidates minimizing neural_rank * shape_rank','selection':selection,'removed':sorted(set(baseline)-set(selection)),'added':sorted(added),'previous_feedback':{'matched':19,'guesses':28,'source':'user-provided evaluator screenshot'},'revised_score':None,'flag_available':False}
 (root/'revision.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')

 summary_path=root/'summary.json'
 if summary_path.exists():
  summary=json.loads(summary_path.read_text(encoding='utf-8'))
  summary.update(method='chromaticity atlas with neural and silhouette rank refinement',selection=selection,revision=2,previous_matched=19,revised_matched=None)
  summary_path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
 check()

if __name__=='__main__':
 if '--check' in sys.argv:check()
 else:run('--refresh' in sys.argv)
