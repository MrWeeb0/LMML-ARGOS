import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from urllib.request import urlopen
from PIL import ImageGrab

root=Path(__file__).resolve().parent
out=root/'captures';out.mkdir(exist_ok=True)
os.environ['DISPLAY']=':99'
os.environ['SDL_AUDIODRIVER']='dummy'

def snap(name):
 path=out/(name+'.png')
 ImageGrab.grab(xdisplay=':99').save(path)
 print(path.name,flush=True)

def start():
 binary=root/'marathon-lab-linux-x86_64'
 if not binary.exists():
  with urlopen('https://www.dropbox.com/scl/fi/6vzyji3zk8le8i95yc35r/marathon-lab-linux-x86_64?dl=1&rlkey=ssw73nzuor6qbjiy8bscy23jm&st=17adwv90',timeout=90) as response:binary.write_bytes(response.read())
 digest=hashlib.sha256(binary.read_bytes()).hexdigest()
 if digest!='569dd52d9a4ff551798caff32c7eb3a1f5e462e14225d93f55a42dff25f2eca4':raise ValueError('Unexpected Linux build')
 binary.chmod(0o755)
 with open(out/'display.log','w') as log:display=subprocess.Popen(['Xvfb',':99','-screen','0','1920x1080x24','-nolisten','tcp'],stdout=log,stderr=log,start_new_session=True)
 time.sleep(2)
 if (root/'observe.so').exists():
  os.environ['LD_PRELOAD']=str(root/'observe.so')
  os.environ['MARATHON_OBSERVER']=str(root/'observe.py')
 with open(out/'application.log','w') as log:app=subprocess.Popen([str(binary)],cwd=root,stdout=log,stderr=log,start_new_session=True)
 state={'pid':app.pid,'display_pid':display.pid,'started':time.time(),'sha256':digest}
 (out/'run.json').write_text(json.dumps(state,indent=2))
 time.sleep(8)
 if app.poll() is not None:raise RuntimeError((out/'application.log').read_text())
 snap('initial')

def watch(seconds):
 state=json.loads((out/'run.json').read_text())
 until=time.time()+seconds
 while time.time()<until:
  time.sleep(min(30,until-time.time()))
  os.kill(state['pid'],0)
  snap(f"elapsed-{round(time.time()-state['started']):04d}")

if __name__=='__main__':
 if sys.argv[1]=='start':start()
 else:watch(int(sys.argv[2]))
