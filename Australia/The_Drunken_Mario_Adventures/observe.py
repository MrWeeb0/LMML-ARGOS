import json,math,os,time,traceback
from pathlib import Path
import numpy as np
from lab.evolution import Lab
from lab.level import COIN_SITES
from lab import fitness

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
accelerated=False
probed=False

def record(self):
 global observed_score,probed
 try:
  champion=max(self.runners,key=lambda runner:runner.score)
  env=champion.env
  info=env.info() if callable(env.info) else env.info
  row={'generation':self.generation,'score':plain(champion.score),'info':plain(info),'state':{name:plain(getattr(env,name)) for name in ['coins','coins_taken','coins_got','won','dead','x','y','max_x','steps'] if hasattr(env,name)}}
  with observed.joinpath('behavior.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
  if not probed:
   probed=True
   functions={name:value for name,value in vars(fitness).items() if callable(value) and not name.startswith('_')}
   report={'info':plain(info),'functions':{name:str(getattr(value,'__code__',value)) for name,value in functions.items()}}
   fn=getattr(env,'reward_fn',None)
   if fn is None:
    fn=next((functions[name] for name in ['reward','fitness','score'] if name in functions),None)
   if fn is not None and isinstance(info,dict):
    baseline=dict(info);baseline['coins_taken']=()
    try:
     base=float(fn(baseline));payoffs=[]
     for site in COIN_SITES:
      trial=dict(baseline);trial['coins_taken']=(site,)
      payoffs.append(float(fn(trial))-base)
     report['coin_payoffs']=payoffs
    except Exception:report['probe_error']=traceback.format_exc()
   observed.joinpath('preferences.json').write_text(json.dumps(report,indent=2))
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
