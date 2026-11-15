import hashlib,json,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gdown

root=Path(__file__).parent

def retrieve(item):
    target=root/'data'/item['path']
    for attempt in range(5):
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256']:return
        try:
            gdown.download(id=item['id'],output=str(target),quiet=True,use_cookies=False)
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Hash mismatch: '+item['path'])
            return
        except Exception as error:
            print('Download retry',attempt+1,item['path'],type(error).__name__,flush=True)
            if attempt==4:raise
            time.sleep(min(16,2**attempt))

if __name__=='__main__':
    entries=json.loads((root/'manifest.json').read_text())
    for folder in {(root/'data'/v['path']).parent for v in entries}:folder.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,_ in enumerate(pool.map(retrieve,entries),1):
            if i%20==0:print(i,'/',len(entries),flush=True)
