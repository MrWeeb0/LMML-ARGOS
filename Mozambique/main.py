
import sys,json,math

def paths(r):
 n=len(r);d=[[999]*n for _ in range(n)];nx=[[-1]*n for _ in range(n)]
 for i in range(n):
  d[i][i]=0
  for j,w in enumerate(r[i]):
   if w:d[i][j]=w;nx[i][j]=j
 for k in range(n):
  for i in range(n):
   for j in range(n):
    v=d[i][k]+d[k][j]
    if v<d[i][j]:d[i][j]=v;nx[i][j]=nx[i][k]
 return d,nx

def agent(o,m):
 own=o['own'];bo=own['boats'];wh=own['warehouses'];roles=o['map']['roles'];contracts=o['map']['contracts'];claims=o['claims'];rnd=o['round'];acts=o['legal_actions'];home=own['home'];seat=o['seat'];n=len(bo)
 if 'd' not in m:
  d,nx=paths(o['map']['routes']);m['d']=d;m['nx']=nx;m['phase']='opening';m['ct']={};m['fetch']={}
  factories=[i for i,r in enumerate(roles) if r==2];targets=[c['destination'] for c in contracts if c['good']==2]
  sources=[[i for i,r in enumerate(roles) if r==g] for g in (0,1)]
  m['factory']=min(factories,key=lambda f:3.3*d[home][f]+1.7*min(d[f][x] for x in sources[0])+1.5*min(d[f][x] for x in sources[1])+3.5*d[f][targets[0]]+1.8*d[f][targets[1]]+1.3*d[f][targets[2]]+1*d[f][targets[3]])
 d=m['d'];nx=m['nx'];f=m['factory'];fetch=m['fetch'];ct=m['ct']
 def find(op,i=None,good=None,qty=None,dest=None,c=None):
  for a in acts:
   if a['op']!=op:continue
   if i is not None and a.get('boat')!=i:continue
   if good is not None and a.get('good')!=good:continue
   if qty is not None and a.get('quantity')!=qty:continue
   if dest is not None and a.get('destination')!=dest:continue
   if c is not None and a.get('contract')!=c:continue
   return a
  return None
 def go(i,t):
  b=bo[i]
  if b['eta'] or b['position']==t:return None
  x=nx[b['position']][t]
  if x<0:return None
  return find('sail',i,dest=x)
 def load(i,g,q):
  for j in range(min(q,3-sum(bo[i]['cargo'])),0,-1):
   a=find('load',i,good=g,qty=j) or find('gather',i,good=g,qty=j)
   if a:return a
  return None
 def unload(i,g):
  for q in range(bo[i]['cargo'][g],0,-1):
   a=find('unload',i,good=g,qty=q)
   if a:return a
  return None
 avail=[(k,c) for k,c in enumerate(contracts) if c['good']==2 and claims[k]==-1 and c['deadline']>rnd]
 if m['phase']=='opening':
  if bo[0]['position']==home and not bo[0]['eta'] and bo[0]['cargo'][0]<3:
   a=load(0,0,3-bo[0]['cargo'][0]);
   if a:return a
  if bo[1]['position']==home and not bo[1]['eta'] and bo[1]['cargo'][0]<1:
   a=load(1,0,1-bo[1]['cargo'][0]);
   if a:return a
  if bo[1]['position']==home and not bo[1]['eta'] and bo[1]['cargo'][1]<2:
   a=load(1,1,2-bo[1]['cargo'][1]);
   if a:return a
  for i in range(2):
   if bo[i]['position']==f and not bo[i]['eta']:
    for g in (0,1):
     a=unload(i,g)
     if a:return a
  for i in range(2):
   a=find('build_workshop',i)
   if a:return a
  for i in range(2):
   a=find('craft',i)
   if a:m['phase']='normal';return a
  for i in range(2):
   if bo[i]['position']!=f and sum(bo[i]['cargo']) and not bo[i]['eta']:
    a=go(i,f)
    if a:return a
  return acts[0]
 for i,b in enumerate(bo):
  if b['eta']==0 and b['position']==f:
   for g in (0,1):
    a=unload(i,g)
    if a:return a
 if avail:
  inproc=sum(b['cargo'][2] for b in bo)+wh[f][2]+(1 if own['jobs'][f] else 0)
  if inproc<len(avail):
   for i in range(n):
    a=find('craft',i)
    if a:return a
  for i in range(n):
   a=find('build_workshop',i)
   if a:return a
 for i,b in enumerate(bo):
  if b['eta']==0 and b['position']==home and b['cargo'][0]>0 and b['cargo'][1]==0 and sum(b['cargo'])<=2 and wh[home][1]>0 and wh[f][1]<2:
   a=load(i,1,1)
   if a:return a
 for i,b in enumerate(bo):
  if b['eta']==0 and (b['cargo'][0] or b['cargo'][1]):
   if b['position']==f:
    for g in (0,1):
     a=unload(i,g)
     if a:return a
   else:
    a=go(i,f)
    if a:return a
 def delivery_key(i,k,c):
  b=bo[i];dest=c['destination'];arr=rnd+b['eta']+d[b['position']][dest]+1
  if arr>c['deadline']:return 99999
  return (k-4)*10 + d[b['position']][dest]*2.2 + max(0,arr-c['deadline']+4)*3
 for i,b in enumerate(bo):
  if b['cargo'][2] and not b['eta']:
   k=ct.get(str(i),-1)
   candidates=sorted(avail,key=lambda z:delivery_key(i,*z))
   if k not in [x for x,_ in avail] or delivery_key(i,k,contracts[k])>delivery_key(i,*candidates[0])+4 if candidates else True:
    if candidates:k=candidates[0][0];ct[str(i)]=k
   if k>=0 and k<len(contracts) and claims[k]==-1:
    c=contracts[k]
    a=find('deliver',i,c=k) if b['position']==c['destination'] else go(i,c['destination'])
    if a:return a
 if avail and wh[f][2]>0:
  for i in [1,0]+list(range(2,n)):
   b=bo[i]
   if b['eta'] or sum(b['cargo']):continue
   if b['position']==f:
    a=load(i,2,min(3,wh[f][2],len(avail)))
    if a:return a
 active=sum(b['cargo'][2] for b in bo)+wh[f][2]+(1 if own['jobs'][f] else 0)
 remaining=max(0,len(avail)-active)
 target=min(remaining,3)
 need=[max(0,2*target-wh[f][0]-sum(b['cargo'][0] for b in bo)),max(0,target-wh[f][1]-sum(b['cargo'][1] for b in bo))]
 for i,b in enumerate(bo):
  if b['cargo'][0] or b['cargo'][1] or b['eta']:continue
  t=fetch.get(str(i))
  if t is not None:
   g,s=t
   if need[g]<=0 or (o['stocks'][s]==0 and roles[s]==g and wh[s][g]==0):fetch.pop(str(i),None)
 for i,b in enumerate(bo):
  if b['eta'] or sum(b['cargo']):continue
  t=fetch.get(str(i))
  if t is not None:
   g,s=t
   if b['position']==s:
    a=load(i,g,min(3,need[g]))
    if a:fetch.pop(str(i),None);return a
   else:
    a=go(i,s)
    if a:return a
 picks=[]
 for i,b in enumerate(bo):
  if b['eta'] or sum(b['cargo']) or str(i) in fetch:continue
  if not avail:continue
  if i==1 and b['position']==f and own['jobs'][f]>0:continue
  for g in (0,1):
   if need[g]<=0:continue
   for s in range(len(roles)):
    if s==f:continue
    quantity=wh[s][g] if wh[s][g]>0 else (o['stocks'][s] if roles[s]==g else 0)
    if quantity is None:quantity=3
    if quantity<=0:continue
    q=min(3,need[g],quantity)
    urgency=(2-wh[f][0] if g==0 else 1-wh[f][1])>0
    cost=(d[b['position']][s]+d[s][f]+2.0)/(max(1,q)**0.58)
    if urgency:cost*=0.6
    if i==1:cost*=1.2
    if i==1 and own['jobs'][f] and own['jobs'][f]<=d[b['position']][f]+2:cost*=3
    picks.append((cost,i,g,s))
 if picks:
  _,i,g,s=min(picks)
  fetch[str(i)]=[g,s]
  if bo[i]['position']==s:
   a=load(i,g,min(3,need[g]));
   if a:fetch.pop(str(i),None);return a
  a=go(i,s)
  if a:return a
 if avail and (wh[f][2] or own['jobs'][f]):
  for i in [1,0]+list(range(2,n)):
   b=bo[i]
   if b['eta']==0 and not sum(b['cargo']) and b['position']!=f:
    a=go(i,f)
    if a:return a
 return raw_only(o,m,acts,d,nx) if not avail else acts[0]

def raw_only(o,m,acts,d,nx):
 boats=o['own']['boats'];wh=o['own']['warehouses'];roles=o['map']['roles'];contracts=o['map']['contracts'];claims=o['claims'];rnd=o['round']
 for i,b in enumerate(boats):
  if b['eta']:continue
  p=b['position'];cargo=b['cargo']
  options=[]
  for k,c in enumerate(contracts):
   if c['good']==2 or claims[k]!=-1:continue
   g=c['good'];q=c['quantity'];dest=c['destination']
   if cargo[2] or sum(cargo)-cargo[g]>0 or q>3:continue
   if cargo[g]>=q:t=d[p][dest]+1;src=-1
   else:
    sources=[j for j,r in enumerate(roles) if r==g]+[j for j,x in enumerate(wh) if x[g]>=q-cargo[g]]
    if not sources:continue
    src=min(sources,key=lambda j:d[p][j]+d[j][dest]);t=d[p][src]+d[src][dest]+3
   if rnd+t>c['deadline']:continue
   options.append((t+0.005*c['deadline'],k,src))
  if not options:continue
  _,k,src=min(options);c=contracts[k]
  if cargo[c['good']]>=c['quantity']:
   for a in acts:
    if a['op']=='deliver' and a.get('boat')==i and a.get('contract')==k:return a
   goal=c['destination']
  elif src==p:
   for a in acts:
    if a['op'] in ('load','gather') and a.get('boat')==i and a.get('good')==c['good'] and a.get('quantity')==c['quantity']-cargo[c['good']]:return a
   goal=src
  else:goal=src
  if goal!=p:
   for a in acts:
    if a['op']=='sail' and a.get('boat')==i and a.get('destination')==nx[p][goal]:return a
 return acts[0]

def serve():
 out=sys.stdout;sys.stdout=sys.stderr;mem={}
 for line in sys.stdin:
  try:
   o=json.loads(line)['observation']
   if o['round']==0:mem={}
   action=agent(o,mem)
   out.write(json.dumps(action)+'\n');out.flush()
  except Exception as e:
   print('ERR',str(e),file=sys.stderr)
   out.write('{"op":"wait"}\n');out.flush()

if __name__=='__main__':serve()
