import csv,json,math,hashlib
from pathlib import Path
from collections import Counter,defaultdict

def read(name):
 with open(name,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def distance(a,b):
 a,b,c,d=map(math.radians,(*a,*b))
 h=math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2
 return 12742*math.asin(math.sqrt(min(1,h)))

def consensus(rows):
 votes=[Counter(r['ring_read'][i] for r in rows if r['ring_read'][i]!='?') for i in range(6)]
 if any(not c or len(c)>1 and c.most_common(2)[0][1]==c.most_common(2)[1][1] for c in votes):raise ValueError('Ambiguous ring')
 return ''.join(c.most_common(1)[0][0] for c in votes),[dict(sorted(c.items())) for c in votes]

def recover(observations,register):
 species='Ciconia ciconia'
 homes=[(float(r['ringed_latitude']),float(r['ringed_longitude'])) for r in register if r['species']==species]
 rows=[r for r in observations if r['species']==species and r['ring_read']]
 groups=defaultdict(list)
 for r in rows:
  if len(r['ring_read'])!=6 or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ?' for c in r['ring_read']):raise ValueError('Invalid reading')
  groups[r['locality_id']].append(r)
 ranked=sorted((min(distance((float(r['latitude']),float(r['longitude'])),h) for r in v for h in homes),k,v) for k,v in groups.items())[::-1]
 gap,locality,selected=ranked[0]
 if len(selected)<3 or gap<=10 or len(ranked)>1 and gap<=10*ranked[1][0]:raise ValueError('No isolated candidate')
 ring,votes=consensus(selected)
 if ring in {r['ring'] for r in register}:raise ValueError('Ring is registered')
 result={'ring':ring,'flag':'SIGMOID_'+ring,'observation_rows':len(observations),'register_rows':len(register),'registered_storks':len(homes),'stork_readings':len(rows),'stork_localities':len(groups),'locality_id':locality,'district':selected[0]['district'],'candidate_readings':len(selected),'checklists':len({r['checklist_id'] for r in selected}),'dates':len({r['date'] for r in selected}),'observers':len({x for r in selected for x in r['observers'].split('|')}),'first_date':min(r['date'] for r in selected),'last_date':max(r['date'] for r in selected),'nearest_registered_stork_km':gap,'next_locality_distance_km':ranked[1][0],'votes':votes,'ranked_localities':[{'locality_id':k,'readings':len(v),'nearest_registered_stork_km':d} for d,k,v in ranked]}
 return result,selected

def main():
 names=['observations.csv','ring_register.csv']
 result,selected=recover(*(read(n) for n in names))
 result['sha256']={n:hashlib.sha256(Path(n).read_bytes()).hexdigest() for n in names}
 Path('result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 Path('flag.txt').write_text(result['flag']+'\n',encoding='utf-8')
 with open('evidence.csv','w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(sorted(selected,key=lambda r:(r['date'],r['checklist_id'])))
 print(result['flag'])

if __name__=='__main__':main()
