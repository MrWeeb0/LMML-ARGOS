import json,math,traceback
from pathlib import Path
import numpy as np
from lab.evolution import Lab
from lab.level import COIN_SITES

observed=Path('captures');observed.mkdir(exist_ok=True)

def plain(value):
 if isinstance(value,(str,int,bool,type(None))):return value
 if isinstance(value,float):return value if math.isfinite(value) else str(value)
 if isinstance(value,dict):return {str(k):plain(v) for k,v in value.items()}
 if isinstance(value,(list,tuple,set)):return [plain(v) for v in value]
 if hasattr(value,'tolist'):return plain(value.tolist())
 return str(value)

observed.joinpath('observer-installed.json').write_text(json.dumps({'coin_sites':plain(COIN_SITES)},indent=2))
original_finish=Lab.finish
observed_score=-float('inf')

def finish(self,*args,**kwargs):
 global observed_score
 try:
  champion=max(self.runners,key=lambda runner:runner.score)
  env=champion.env
  row={'generation':self.generation,'score':plain(champion.score),'state':{name:plain(getattr(env,name)) for name in ['coins_taken','coins_got','won','dead','x','y','max_x','steps'] if hasattr(env,name)}}
  with observed.joinpath('behavior.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
  if champion.score>observed_score:
   observed_score=champion.score
   np.save(observed/'trained-winner.npy',champion.brain.genome())
 except Exception:
  with observed.joinpath('observer-error.log').open('a') as stream:stream.write(traceback.format_exc())
 return original_finish(self,*args,**kwargs)

Lab.finish=finish
