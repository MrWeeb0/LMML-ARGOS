import inspect,json,math,os,time,traceback
from pathlib import Path
import numpy as np
from lab.evolution import Lab
from lab.level import COIN_SITES

observed=Path('captures');observed.mkdir(exist_ok=True)
last_info={}
patched=set()

def plain(value):
 if isinstance(value,(str,int,bool,type(None))):return value
 if isinstance(value,float):return value if math.isfinite(value) else str(value)
 if isinstance(value,dict):return {str(k):plain(v) for k,v in value.items()}
 if isinstance(value,(list,tuple,set,frozenset)):return [plain(v) for v in value]
 if hasattr(value,'tolist'):return plain(value.tolist())
 return str(value)

observed.joinpath('observer-installed.json').write_text(json.dumps({'coin_sites':plain(COIN_SITES),'methods':{name:str(inspect.signature(getattr(Lab,name))) for name in ['step','finish','begin']}},indent=2))
original_finish=Lab.finish
observed_score=-float('inf')
accelerated=False

def install(env):
 cls=type(env)
 if cls in patched:return
 patched.add(cls)
 original_info=cls.info
 def info(self,*args,**kwargs):
  result=original_info(self,*args,**kwargs)
  last_info[id(self)]=plain(result)
  return result
 cls.info=info

def record(self):
 global observed_score
 try:
  champion=max(self.runners,key=lambda runner:runner.score)
  env=champion.env
  install(env)
  info=last_info.get(id(env),{})
  row={'generation':self.generation,'score':plain(champion.score),'info':info,'state':{name:plain(getattr(env,name)) for name in ['coins','coins_taken','coins_got','won','dead','x','y','max_x','steps'] if hasattr(env,name)}}
  with observed.joinpath('behavior.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
  if champion.score>observed_score:
   observed_score=champion.score
   np.save(observed/'trained-winner.npy',champion.brain.genome())
 except Exception:
  with observed.joinpath('observer-error.log').open('a') as stream:stream.write(traceback.format_exc())

def finish(self,*args,**kwargs):
 global accelerated
 record(self)
 result=original_finish(self,*args,**kwargs)
 generations=int(os.environ.get('MARATHON_FAST_GENERATIONS','0'))
 if not accelerated and generations:
  accelerated=True;goal=self.generation+generations;deadline=time.monotonic()+480
  try:
   while self.generation<goal and time.monotonic()<deadline:
    done=self.finished() if callable(self.finished) else self.finished
    if done:
     record(self);original_finish(self)
     if all(runner.done for runner in self.runners):self.begin()
    else:self.step()
  except Exception:
   with observed.joinpath('observer-error.log').open('a') as stream:stream.write(traceback.format_exc())
 return result

Lab.finish=finish
