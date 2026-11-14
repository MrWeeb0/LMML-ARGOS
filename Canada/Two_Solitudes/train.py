import csv,re,collections
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression
from featurize import featurize,tokens
from open_vault import CLASSES

patterns=[
 r'flood|inond|\bcrue|embâcle|overflow|crested|water levels|montée des eaux|débord|submerg',
 r'tornado|tornad|hurricane|ouragan|cyclon|thunderstorm|orage|grêle|hail|storm surge|onde de tempête|post-tropical|tropical storm|tempête tropicale|violent storm|windstorm|tempête de vent|rafales',
 r'blizzard|snowstorm|snowfall|heavy snow|snow and|winter|hivernal|vergla|grésil|poudrerie|chutes? de neige|tempête de neige|\bfroid|\bcold|ice storm|freez|glace|\bice\b',
 r'wildfire|forest fire|brush fire|bush fire|grass fire|feu.{0,20}forêt|incendie.{0,20}forêt|feux.{0,20}forêt|hectare|timber',
 r'drought|sécheresse|heat wave|heatwave|vague de chaleur|canicule|dry growing|crop|récolt|grain production|rendement|bétail|livestock|soil drift|dust storm|grasshopp|sauterell|low rainfall',
 r'avalanche|landslide|mudslide|rockslide|earthquake|tsunami|séisme|tremblement|glissement|éboulement|coulée de boue|aftershock|réplique|richter|hillside.{0,15}fail',
 r'explosion|explod|explos|spill|déversement|fuite|factory|usine|warehouse|entrepôt|hotel|hôtel|apartment|immeuble|nursing home|business district|quartier des affaires|downtown|\bmine\b|colliery|houillère|silo|pipeline|raffinerie|refinery|chlorine|chlore|chemical|chimique',
 r'crash|collision|collid|derail|dérail|écras|heurt|percute|naufrag|\bsank\b|\bsunk\b|capsiz|chavir|founder|\bcoule|\bsombre|\baccident',
 r'epidem|épidém|outbreak|éclos|polio|typh|influenza|grippe|variole|smallpox|cholera|choléra|dipht|disease|maladie|infect|vaccin|quarant|gastroent|\bcas\b|\bcases\b'
]
rx=[re.compile(p,re.I) for p in patterns]
def label(t):
 a={i for i,p in enumerate(rx) if p.search(t)}
 if 5 in a and re.search('avalanche',t,re.I):a.discard(2)
 if 0 in a and re.search('embâcle|ice jam',t,re.I):a.discard(2)
 if 6 not in a and 3 not in a and re.search(r'\bfire\b|\bincendie\b|\bfeu\b',t,re.I):a.add(6)
 return next(iter(a)) if len(a)==1 else -1
def fr(t):return sum(w in {'le','la','les','des','une','un','du','dans','sont','est','de'} for w in tokens(t))>1
r=list(csv.DictReader(open('corpus.csv',encoding='utf-8')))
d=[]
for v in r:
 for t in re.split(r'(?<=[.!?;])\s+',v['text']):
  c=label(t)
  if c>=0:d.append((t,c))
y=np.array([c for t,c in d])
X=csr_matrix(featurize([t for t,c in d]))
g=[(c,fr(t)) for t,c in d]
counts=collections.Counter(g)
sw=np.array([len(y)/(18*counts[k]) for k in g])
m=LogisticRegression(C=10,max_iter=2000).fit(X,y,sample_weight=sw)
W=np.zeros((9,4096))
b=np.zeros(9)
W[m.classes_],b[m.classes_]=m.coef_,m.intercept_
np.savez('model.npz',W=W,b=b)
print('Synthetic sentences:',len(d))
