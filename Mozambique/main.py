
import sys,json,math,heapq

def path(r):
 n=len(r);d=[[9999]*n for _ in range(n)];nx=[[-1]*n for _ in range(n)]
 for i in range(n):
  d[i][i]=0
  for j,w in enumerate(r[i]):
   if w:d[i][j]=w;nx[i][j]=j
 for k in range(n):
  for i in range(n):
   for j in range(n):
    z=d[i][k]+d[k][j]
    if z<d[i][j]:d[i][j]=z;nx[i][j]=nx[i][k]
 return d,nx

def agent(o,m):
 own=o['own'];boats=own['boats'];wh=own['warehouses'];roles=o['map']['roles'];contracts=o['map']['contracts'];claims=o['claims'];rnd=o['round'];acts=o['legal_actions'];home=own['home'];mfg=[i for i,r in enumerate(roles) if r==2]
 if 'd' not in m:
  d,nx=path(o['map']['routes']);m['d']=d;m['nx']=nx
  opponent=o['map']['homes'][1-o['seat']]
  m['factory']=min(mfg,key=lambda x:d[home][x]*2+min(d[x][j] for j,r in enumerate(roles) if r==1)*2+min(d[x][j] for j,r in enumerate(roles) if r==0)*1)
  m['init']=True;m['start']=0;m['made']=0;m['task']={}
 d=m['d'];nx=m['nx'];f=m['factory'];task=m['task']
 actions={tuple(sorted(a.items())):a for a in acts}
 def a(op,i=None,g=None,q=None,dest=None,c=None):
  t={'op':op}
  if i is not None:t['boat']=i
  if g is not None:t['good']=g
  if q is not None:t['quantity']=q
  if dest is not None:t['destination']=dest
  if c is not None:t['contract']=c
  return actions.get(tuple(sorted(t.items())))
 def goto(i,t):
  b=boats[i]
  if b['eta'] or b['position']==t:return None
  nxt=nx[b['position']][t]
  if nxt<0:return None
  return a('sail',i,dest=nxt)
 def pos(i):return boats[i]['destination'] if boats[i]['eta'] else boats[i]['position']
 def load(i,g,q):
  for z in range(q,0,-1):
   ac=a('load',i,g,z) or a('gather',i,g,z)
   if ac:return ac
  return None
 def unload(i,g):
  for z in range(boats[i]['cargo'][g],0,-1):
   ac=a('unload',i,g,z)
   if ac:return ac
  return None
 avail=[(i,c) for i,c in enumerate(contracts) if claims[i]==-1 and c['good']==2 and c['deadline']>=rnd+1]
 availraw=[(i,c) for i,c in enumerate(contracts) if claims[i]==-1 and c['good']!=2 and c['deadline']>=rnd+1]
 if m['init']:
  if boats[0]['position']==home and boats[0]['eta']==0 and boats[0]['cargo'][0]<3:
   ac=load(0,0,3-boats[0]['cargo'][0])
   if ac:return ac
  if boats[1]['position']==home and boats[1]['eta']==0 and boats[1]['cargo'][0]<1:
   ac=load(1,0,1-boats[1]['cargo'][0])
   if ac:return ac
  if boats[1]['position']==home and boats[1]['eta']==0 and boats[1]['cargo'][1]<2:
   ac=load(1,1,2-boats[1]['cargo'][1])
   if ac:return ac
  for i in range(2):
   if boats[i]['eta']==0 and boats[i]['position']==f:
    for g in (0,1):
     ac=unload(i,g)
     if ac:return ac
  if not own['workshops'][f]:
   for i in range(2):
    ac=a('build_workshop',i)
    if ac and boats[i]['position']==f:return ac
  if own['workshops'][f]:
   for i in range(2):
    ac=a('craft',i)
    if ac and boats[i]['position']==f:
     m['made']+=1;m['init']=False;return ac
  for i in range(2):
   if sum(boats[i]['cargo']) and boats[i]['eta']==0 and boats[i]['position']!=f:
    ac=goto(i,f)
    if ac:return ac
  if not any(b['eta'] for b in boats):m['init']=False
  else:return acts[0]

 if not avail:
  return raw_only(o,m,acts,d,nx) if availraw else acts[0]

 for i,b in enumerate(boats):
  if b['eta']==0 and b['position']==f and b['cargo'][0]+b['cargo'][1]>0:
   for g in (0,1):
    ac=unload(i,g)
    if ac:return ac
 for i,b in enumerate(boats):
  ac=a('build_workshop',i)
  if ac and b['position']==f:return ac
 pending=sum(b['cargo'][2] for b in boats)+wh[f][2]+own['jobs'][f]
 if len(avail)>pending:
  for i,b in enumerate(boats):
   ac=a('craft',i)
   if ac and b['position']==f:
    m['made']+=1;return ac

 def dest_score(i,k,c):
  p=pos(i);dest=c['destination'];arr=rnd+boats[i]['eta']+d[p][dest]+1
  slack=c['deadline']-arr
  if slack<0:return 1e5
  oppstart=32 if c['deadline']<=40 else (43 if c['deadline']<=72 else 57)
  oppstart+=0.5*d[o['map']['homes'][1-o['seat']]][dest]
  return 2.1*d[p][dest]+max(0,arr-oppstart+4)*6+0.028*c['deadline']+0.25*d[dest][f]-min(10,c['deadline']-arr)*0.02
 for i,b in enumerate(boats):
  if b['eta']==0 and b['cargo'][2]:
   candidates=sorted(avail,key=lambda z:dest_score(i,*z))
   if candidates and dest_score(i,*candidates[0])<1e5:
    k,c=candidates[0]
    ac=a('deliver',i,c=k) if b['position']==c['destination'] else goto(i,c['destination'])
    if ac:return ac

 if wh[f][2]:
  candidates=[]
  for i,b in enumerate(boats):
   if b['eta']==0 and sum(b['cargo'])==0:
    proximity=d[b['position']][f]
    candidates.append((proximity,i))
  if candidates:
   _,i=min(candidates)
   if boats[i]['position']==f:
    return load(i,2,min(3,wh[f][2])) or acts[0]
   if i==1 or own['jobs'][f]==0:
    ac=goto(i,f)
    if ac:return ac

 reserved=None
 empty=[i for i,b in enumerate(boats) if sum(b['cargo'])==0]
 if (own['jobs'][f] or wh[f][2]) and empty:
  reserved=min(empty,key=lambda i:(d[pos(i)][f]+boats[i]['eta'],i))
  if boats[reserved]['eta']==0 and boats[reserved]['position']!=f and (own['jobs'][f] <= d[pos(reserved)][f]+1 or wh[f][2]):
   ac=goto(reserved,f)
   if ac:return ac

 active=sum(b['cargo'][2] for b in boats)+wh[f][2]+own['jobs'][f]
 needb=max(0,min(2,len(avail)-active))
 needed=[2*needb+ (0 if own['workshops'][f] else 2),needb+(0 if own['workshops'][f] else 1)]
 stock=[wh[f][0],wh[f][1]]
 carried=[sum(b['cargo'][g] for b in boats) for g in (0,1)]
 shortage=[max(0,needed[g]-stock[g]-carried[g]) for g in (0,1)]
 for i,b in enumerate(boats):
  if b['eta'] or sum(b['cargo'])==0 or b['cargo'][2]:continue
  p=b['position'];free=3-sum(b['cargo'])
  if p==home and free:
   pick=[(max(0,shortage[g]),g) for g in (0,1) if wh[home][g]>0]
   for _,g in sorted(pick,reverse=True):
    if shortage[g] and wh[home][g]>0:
     ac=load(i,g,min(free,shortage[g],wh[home][g]))
     if ac:return ac
  if roles[p] in (0,1) and free:
   g=roles[p]
   if shortage[g] and (o['stocks'][p] or 0):
    ac=load(i,g,min(free,shortage[g],o['stocks'][p]))
    if ac:return ac
  ac=goto(i,f)
  if ac:return ac

 candidates=[]
 for i,b in enumerate(boats):
  if b['eta'] or sum(b['cargo']):continue
  if i==reserved and (own['jobs'][f] or wh[f][2]):continue
  p=b['position']
  for g in (0,1):
   if shortage[g]<=0:continue
   srcs=[z for z,r in enumerate(roles) if r==g and (o['stocks'][z] is None or o['stocks'][z]>0)]
   srcs +=[z for z,w in enumerate(wh) if w[g]>0 and z not in srcs]
   for src in srcs:
    if src==f:continue
    qty=min(3,shortage[g],wh[src][g] if wh[src][g]>0 else (o['stocks'][src] if o['stocks'][src] is not None else 3))
    if qty<=0:continue
    penalty=d[p][src]+d[src][f]+2
    urgency=2.3 if stock[g]<[2,1][g] else 1
    if shortage[g]>=2 and g==0:urgency+=0.2
    score=penalty/(math.sqrt(qty)*urgency)+(1.1 if i==1 else 0)
    candidates.append((score,i,g,src))
 if candidates:
  _,i,g,src=min(candidates)
  ac=load(i,g,min(3,shortage[g])) if boats[i]['position']==src else goto(i,src)
  if ac:return ac

 if wh[f][2] or own['jobs'][f]:
  for i,b in enumerate(boats):
   if sum(b['cargo'])==0 and b['eta']==0:
    ac=goto(i,f)
    if ac:return ac
 return raw_only(o,m,acts,d,nx) if availraw else acts[0]

def raw_only(o,m,acts,d,nx):
 boats=o['own']['boats'];contracts=o['map']['contracts'];claims=o['claims'];roles=o['map']['roles'];wh=o['own']['warehouses'];home=o['own']['home'];rnd=o['round']
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
   for ac in acts:
    if ac['op']=='deliver' and ac.get('boat')==i and ac.get('contract')==k:return ac
   goal=c['destination']
  elif src==p:
   for ac in acts:
    if ac['op'] in ('load','gather') and ac.get('boat')==i and ac.get('good')==c['good'] and ac.get('quantity')==c['quantity']-cargo[c['good']]:return ac
   goal=src
  else:goal=src
  if goal!=p:
   for ac in acts:
    if ac['op']=='sail' and ac.get('boat')==i and ac['destination']==nx[p][goal]:return ac
 return acts[0]

def serve():
 protocol=sys.stdout;sys.stdout=sys.stderr;mem={}
 for line in sys.stdin:
  try:
   o=json.loads(line)['observation']
   if o['round']==0:mem={}
   ans=agent(o,mem)
   protocol.write(json.dumps(ans)+'\n');protocol.flush()
  except Exception as e:
   print('ERROR',repr(e),file=sys.stderr)
   protocol.write('{"op":"wait"}\n');protocol.flush()

if __name__=='__main__':serve()
