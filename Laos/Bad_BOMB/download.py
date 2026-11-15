import hashlib,json,re,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

root=Path(__file__).parent
images=root/'images';images.mkdir(exist_ok=True)
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))

def download(entry):
 name=entry['name']
 if not re.fullmatch(r'image_\d{4}\.png',name):raise ValueError('Invalid filename')
 target=images/name
 if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256']:return
 for attempt in range(3):
  try:
   with urlopen('https://drive.usercontent.google.com/download?id='+entry['id']+'&export=download',timeout=60) as response:data=response.read()
   if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Hash mismatch '+name)
   temporary=images/(name+'.part');temporary.write_bytes(data);temporary.replace(target)
   return
  except Exception:
   if attempt==2:raise
   time.sleep(attempt+1)

if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=8) as pool:
  for i,_ in enumerate(pool.map(download,manifest),1):
   if i%100==0 or i==len(manifest):print(i,'/',len(manifest),flush=True)
