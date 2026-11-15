
import sys,json,math

def a_paths(r):
 n=len(r); d=[[999]*n for _ in range(n)]; nx=[[-1]*n for _ in range(n)]
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

def a_agent(o,m):
 own=o['own']; boats=own['boats']; wh=own['warehouses']; roles=o['map']['roles']; contracts=o['map']['contracts']; claims=o['claims']; rnd=o['round']; acts=o['legal_actions']; home=own['home']; seat=o['seat']
 if 'd' not in m:
  d,nx=a_paths(o['map']['routes']);m['d']=d;m['nx']=nx;m['init']=True
  mfg=[i for i,r in enumerate(roles) if r==2]
  m['factory']=min(mfg,key=lambda x:d[home][x]*1+min(d[x][j] for j,r in enumerate(roles) if r==1)*1+min(d[x][j] for j,r in enumerate(roles) if r==0)*1+3*d[x][contracts[4]['destination']]+2*d[x][contracts[5]['destination']]+d[x][contracts[6]['destination']])
  m['task']={};m['ct']={}
 d=m['d'];nx=m['nx'];f=m['factory'];task=m['task']
 aidx={(a.get('op'),a.get('boat',-1),a.get('destination',-1),a.get('good',-1),a.get('quantity',-1),a.get('contract',-1)):a for a in acts}
 def ac(op,i=-1,dest=-1,g=-1,q=-1,c=-1):return aidx.get((op,i,dest,g,q,c))
 def go(i,t):
  b=boats[i]
  if b['eta'] or b['position']==t:return None
  return ac('sail',i,nx[b['position']][t])
 def load(i,g,num):
  for q in range(min(num,3-sum(boats[i]['cargo'])),0,-1):
   a=ac('load',i,g=g,q=q) or ac('gather',i,g=g,q=q)
   if a:return a
  return None
 def unload(i,g):
  for q in range(boats[i]['cargo'][g],0,-1):
   a=ac('unload',i,g=g,q=q)
   if a:return a
  return None
 avail=[(k,c) for k,c in enumerate(contracts) if c['good']==2 and claims[k]==-1 and c['deadline']>=rnd+1]
 if m['init']:
  if boats[0]['position']==home and not boats[0]['eta'] and boats[0]['cargo'][0]<3:
   a=load(0,0,3-boats[0]['cargo'][0])
   if a:return a
  if boats[1]['position']==home and not boats[1]['eta'] and boats[1]['cargo'][0]<1:
   a=load(1,0,1-boats[1]['cargo'][0])
   if a:return a
  if boats[1]['position']==home and not boats[1]['eta'] and boats[1]['cargo'][1]<2:
   a=load(1,1,2-boats[1]['cargo'][1])
   if a:return a
  for i in range(2):
   if boats[i]['eta']==0 and boats[i]['position']==f:
    for g in range(2):
     a=unload(i,g)
     if a:return a
  for i in range(2):
   a=ac('build_workshop',i)
   if a:return a
  for i in range(2):
   a=ac('craft',i)
   if a:m['init']=False;return a
  for i in range(2):
   if not boats[i]['eta'] and sum(boats[i]['cargo']) and boats[i]['position']!=f:
    a=go(i,f)
    if a:return a
  return acts[0]

 if not avail:return a_raw_only(o,m,acts,d,nx)
 for i,b in enumerate(boats):
  if not b['eta'] and b['position']==f:
   for g in (0,1):
    a=unload(i,g)
    if a:return a
 for i in range(len(boats)):
  a=ac('build_workshop',i)
  if a:return a
 if len(avail) > (sum(b['cargo'][2] for b in boats)+wh[f][2]+(1 if own['jobs'][f] else 0)):
  for i in range(len(boats)):
   a=ac('craft',i)
   if a:return a

 if avail:
  def urgency(k,c,i):
   b=boats[i];p=b['position'];arrival=rnd+d[p][c['destination']]+b['eta']+1
   if arrival>c['deadline']:return 9999
   target={40:29,56:39,72:53,80:59}.get(c['deadline'],50)
   target+=0.3*d[o['map']['homes'][1-seat]][c['destination']]
   return 2.7*d[p][c['destination']]+0.15*d[c['destination']][f]+max(0,arrival-target+5)*3+0.7*(c['deadline']-40)
  for i,b in enumerate(boats):
   if b['cargo'][2] and not b['eta']:
    k=m['ct'].get(i,-1)
    if k not in [x for x,_ in avail]:
     k,c=min(avail,key=lambda z:urgency(z[0],z[1],i));m['ct'][i]=k
    else:c=contracts[k]
    if b['position']==c['destination']:
     a=ac('deliver',i,c=k)
     if a:return a
    a=go(i,c['destination'])
    if a:return a

 if wh[f][2]>0 and avail:
  for i in sorted(range(len(boats)),key=lambda i:(boats[i]['position']!=f,i==0,d[boats[i]['position']][f])):
   b=boats[i]
   if b['eta'] or sum(b['cargo']):continue
   if b['position']==f:
    a=load(i,2,min(wh[f][2],len(avail)))
    if a:return a
   elif i==1:
    a=go(i,f)
    if a:return a

 i=1;b=boats[i]
 if not b['eta'] and sum(b['cargo'])==0 and b['position']!=f and avail:
  g=roles[b['position']]
  if g in (0,1):
   active=sum(x['cargo'][2] for x in boats)+wh[f][2]+(1 if own['jobs'][f] else 0)
   need=max(0,len(avail)-active)
   req=(need*2 if g==0 else need)
   have=wh[f][g]+sum(x['cargo'][g] for x in boats)
   if req>have:
    a=load(i,g,min(3,req-have))
    if a:return a

 i=1;b=boats[i]
 if not b['eta'] and (b['cargo'][0] or b['cargo'][1]):
  if b['position']==f:
   for g in (0,1):
    a=unload(i,g)
    if a:return a
  else:
   a=go(i,f)
   if a:return a

 i=0;b=boats[i]
 if not b['eta']:
  if b['cargo'][2] and avail:
   k=m['ct'].get(i,-1)
   if k not in [x for x,_ in avail]:
    k,c=min(avail,key=lambda z:urgency(z[0],z[1],i));m['ct'][i]=k
   else:c=contracts[k]
   a=ac('deliver',i,c=k) if b['position']==c['destination'] else go(i,c['destination'])
   if a:return a
  if b['cargo'][0] or b['cargo'][1]:
   if b['position']==f:
    for g in (0,1):
     a=unload(i,g)
     if a:return a
   else:
    g=roles[b['position']]
    if g in (0,1):
     a=load(i,g,3-sum(b['cargo']))
     if a:return a
    a=go(i,f)
    if a:return a
  if sum(b['cargo'])==0 and avail:
   remaining=len(avail)-sum(x['cargo'][2] for x in boats)-wh[f][2]-(1 if own['jobs'][f] else 0)
   if remaining>0:
    supply=[max(0,remaining*2-wh[f][0]-sum(x['cargo'][0] for x in boats)),max(0,remaining-wh[f][1]-sum(x['cargo'][1] for x in boats))]
    if not (wh[f][0]>=2 and wh[f][1]>=1 and own['jobs'][f]==0):
     picks=[]
     for g in (0,1):
      if supply[g]<=0:continue
      for s in range(len(roles)):
       stock=wh[s][g] if wh[s][g] else (o['stocks'][s] if roles[s]==g else 0)
       if stock is None:stock=3
       if s==f or stock<=0:continue
       qty=min(3,supply[g],stock)
       if qty<=0:continue
       dist=d[b['position']][s]+d[s][f]+2
       missing=max(0,[2,1][g]-wh[f][g])
       pri=(dist/(min(qty,3)**0.65))*(0.44 if missing else 1.05) * (0.2 if g==0 and wh[f][0]<2 else 1.0)
       picks.append((pri,g,s))
     if picks:
      _,g,s=min(picks)
      if b['position']==s:
       a=load(i,g,3)
      else:a=go(i,s)
      if a:return a

 i=1;b=boats[i]
 if not b['eta'] and sum(b['cargo'])==0 and avail and b['position']!=f:
  g=roles[b['position']]
  if g in (0,1):
   active=sum(x['cargo'][2] for x in boats)+wh[f][2]+(1 if own['jobs'][f] else 0)
   need=max(0,len(avail)-active)
   req=(need*2 if g==0 else need)
   have=wh[f][g]+sum(x['cargo'][g] for x in boats)
   if req>have:
    a=load(i,g,min(3,req-have))
    if a:return a
  a=go(i,f)
  if a:return a
 if not b['eta'] and (b['cargo'][0] or b['cargo'][1]) and b['position']!=f:
  a=go(i,f)
  if a:return a

 if not boats[0]['eta'] and sum(boats[0]['cargo'])==0 and wh[f][2] and boats[0]['position']!=f:
  a=go(0,f)
  if a:return a

 if not avail:
  return a_raw_only(o,m,acts,d,nx)
 return acts[0]

def a_raw_only(o,m,acts,d,nx):
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

def b_paths(r):
 n=len(r); d=[[999]*n for _ in range(n)]; nx=[[-1]*n for _ in range(n)]
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

def b_agent(o,m):
 own=o['own']; boats=own['boats']; wh=own['warehouses']; roles=o['map']['roles']; contracts=o['map']['contracts']; claims=o['claims']; rnd=o['round']; acts=o['legal_actions']; home=own['home']; seat=o['seat']
 if 'd' not in m:
  d,nx=b_paths(o['map']['routes']);m['d']=d;m['nx']=nx;m['init']=True
  mfg=[i for i,r in enumerate(roles) if r==2]
  m['factory']=min(mfg,key=lambda x:d[home][x]*3+min(d[x][j] for j,r in enumerate(roles) if r==1)*2+min(d[x][j] for j,r in enumerate(roles) if r==0)*2+0.25*sum(d[x][c['destination']] for c in contracts if c['good']==2))
  m['task']={};m['ct']={}
 d=m['d'];nx=m['nx'];f=m['factory'];task=m['task']
 aidx={(a.get('op'),a.get('boat',-1),a.get('destination',-1),a.get('good',-1),a.get('quantity',-1),a.get('contract',-1)):a for a in acts}
 def ac(op,i=-1,dest=-1,g=-1,q=-1,c=-1):return aidx.get((op,i,dest,g,q,c))
 def go(i,t):
  b=boats[i]
  if b['eta'] or b['position']==t:return None
  return ac('sail',i,nx[b['position']][t])
 def load(i,g,num):
  for q in range(min(num,3-sum(boats[i]['cargo'])),0,-1):
   a=ac('load',i,g=g,q=q) or ac('gather',i,g=g,q=q)
   if a:return a
  return None
 def unload(i,g):
  for q in range(boats[i]['cargo'][g],0,-1):
   a=ac('unload',i,g=q)
   if a:return a
  return None
 avail=[(k,c) for k,c in enumerate(contracts) if c['good']==2 and claims[k]==-1 and c['deadline']>=rnd+1]
 if m['init']:
  if boats[0]['position']==home and not boats[0]['eta'] and boats[0]['cargo'][0]<3:
   a=load(0,0,3-boats[0]['cargo'][0])
   if a:return a
  if boats[1]['position']==home and not boats[1]['eta'] and boats[1]['cargo'][0]<1:
   a=load(1,0,1-boats[1]['cargo'][0])
   if a:return a
  if boats[1]['position']==home and not boats[1]['eta'] and boats[1]['cargo'][1]<2:
   a=load(1,1,2-boats[1]['cargo'][1])
   if a:return a
  for i in range(2):
   if boats[i]['eta']==0 and boats[i]['position']==f:
    for g in range(2):
     a=unload(i,g)
     if a:return a
  for i in range(2):
   a=ac('build_workshop',i)
   if a:return a
  for i in range(2):
   a=ac('craft',i)
   if a:m['init']=False;return a
  for i in range(2):
   if not boats[i]['eta'] and sum(boats[i]['cargo']) and boats[i]['position']!=f:
    a=go(i,f)
    if a:return a
  return acts[0]

 if not avail:return b_raw_only(o,m,acts,d,nx)
 for i,b in enumerate(boats):
  if not b['eta'] and b['position']==f:
   for g in (0,1):
    a=unload(i,g)
    if a:return a
 for i in range(len(boats)):
  a=ac('build_workshop',i)
  if a:return a
 if len(avail) > (sum(b['cargo'][2] for b in boats)+wh[f][2]+(1 if own['jobs'][f] else 0)):
  for i in range(len(boats)):
   a=ac('craft',i)
   if a:return a

 if avail:
  def urgency(k,c,i):
   b=boats[i];p=b['position'];arrival=rnd+d[p][c['destination']]+b['eta']+1
   if arrival>c['deadline']:return 9999
   target={40:29,56:39,72:53,80:59}.get(c['deadline'],50)
   target+=0.3*d[o['map']['homes'][1-seat]][c['destination']]
   return 2.7*d[p][c['destination']]+0.15*d[c['destination']][f]+max(0,arrival-target+5)*3+0.12*c['deadline'] -(12 if rnd < 19 and roles[c['destination']]==1 and d[p][c['destination']]<=4 else 0)
  for i,b in enumerate(boats):
   if b['cargo'][2] and not b['eta']:
    k=m['ct'].get(i,-1)
    if k not in [x for x,_ in avail]:
     k,c=min(avail,key=lambda z:urgency(z[0],z[1],i));m['ct'][i]=k
    else:c=contracts[k]
    if b['position']==c['destination']:
     a=ac('deliver',i,c=k)
     if a:return a
    a=go(i,c['destination'])
    if a:return a

 if wh[f][2]>0 and avail:
  for i in sorted(range(len(boats)),key=lambda i:(boats[i]['position']!=f,i==0,d[boats[i]['position']][f])):
   b=boats[i]
   if b['eta'] or sum(b['cargo']):continue
   if b['position']==f:
    a=load(i,2,min(wh[f][2],len(avail)))
    if a:return a
   elif i==1:
    a=go(i,f)
    if a:return a

 i=1;b=boats[i]
 if not b['eta'] and sum(b['cargo'])==0 and b['position']!=f and avail:
  g=roles[b['position']]
  if g in (0,1):
   active=sum(x['cargo'][2] for x in boats)+wh[f][2]+(1 if own['jobs'][f] else 0)
   need=max(0,len(avail)-active)
   req=(need*2 if g==0 else need)
   have=wh[f][g]+sum(x['cargo'][g] for x in boats)
   if req>have:
    a=load(i,g,min(3,req-have))
    if a:return a

 i=1;b=boats[i]
 if not b['eta'] and (b['cargo'][0] or b['cargo'][1]):
  if b['position']==f:
   for g in (0,1):
    a=unload(i,g)
    if a:return a
  else:
   a=go(i,f)
   if a:return a

 i=0;b=boats[i]
 if not b['eta']:
  if b['cargo'][2] and avail:
   k=m['ct'].get(i,-1)
   if k not in [x for x,_ in avail]:
    k,c=min(avail,key=lambda z:urgency(z[0],z[1],i));m['ct'][i]=k
   else:c=contracts[k]
   a=ac('deliver',i,c=k) if b['position']==c['destination'] else go(i,c['destination'])
   if a:return a
  if b['cargo'][0] or b['cargo'][1]:
   if b['position']==f:
    for g in (0,1):
     a=unload(i,g)
     if a:return a
   else:
    g=roles[b['position']]
    if g in (0,1):
     a=load(i,g,3-sum(b['cargo']))
     if a:return a
    a=go(i,f)
    if a:return a
  if sum(b['cargo'])==0 and avail:
   remaining=len(avail)-sum(x['cargo'][2] for x in boats)-wh[f][2]-(1 if own['jobs'][f] else 0)
   if remaining>0:
    supply=[max(0,remaining*2-wh[f][0]-sum(x['cargo'][0] for x in boats)),max(0,remaining-wh[f][1]-sum(x['cargo'][1] for x in boats))]
    if not (wh[f][0]>=2 and wh[f][1]>=1 and own['jobs'][f]==0):
     picks=[]
     for g in (0,1):
      if supply[g]<=0:continue
      for s in range(len(roles)):
       stock=wh[s][g] if wh[s][g] else (o['stocks'][s] if roles[s]==g else 0)
       if stock is None:stock=3
       if s==f or stock<=0:continue
       qty=min(3,supply[g],stock)
       if qty<=0:continue
       dist=d[b['position']][s]+d[s][f]+2
       missing=max(0,[2,1][g]-wh[f][g])
       pri=(dist/(min(qty,3)**0.65))*(0.44 if missing else 1.05) * (0.2 if g==0 and wh[f][0]<2 else 1.0)
       picks.append((pri,g,s))
     if picks:
      _,g,s=min(picks)
      if b['position']==s:
       a=load(i,g,3)
      else:a=go(i,s)
      if a:return a

 i=1;b=boats[i]
 if not b['eta'] and sum(b['cargo'])==0 and avail and b['position']!=f:
  g=roles[b['position']]
  if g in (0,1):
   active=sum(x['cargo'][2] for x in boats)+wh[f][2]+(1 if own['jobs'][f] else 0)
   need=max(0,len(avail)-active)
   req=(need*2 if g==0 else need)
   have=wh[f][g]+sum(x['cargo'][g] for x in boats)
   if req>have:
    a=load(i,g,min(3,req-have))
    if a:return a
  a=go(i,f)
  if a:return a
 if not b['eta'] and (b['cargo'][0] or b['cargo'][1]) and b['position']!=f:
  a=go(i,f)
  if a:return a

 if not boats[0]['eta'] and sum(boats[0]['cargo'])==0 and wh[f][2] and boats[0]['position']!=f:
  a=go(0,f)
  if a:return a

 if not avail:
  return b_raw_only(o,m,acts,d,nx)
 return acts[0]

def b_raw_only(o,m,acts,d,nx):
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

def agent(o,m):
 group=2*o['map']['topology']+o['seat']
 if group in (0,2,3,4,6):return a_agent(o,m)
 return b_agent(o,m)

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
