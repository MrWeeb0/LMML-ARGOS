from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,time
import requests
from PIL import Image

root=Path(__file__).resolve().parent
entries=json.loads((root/"source_manifest.json").read_text())

def download(item):
    path=root/"dataset"/item["path"]
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size==item["size"]:
        return item["path"]
    error=None
    for attempt in range(3):
        try:
            r=requests.get("https://drive.usercontent.google.com/download",
                           params={"id":item["id"],"export":"download","confirm":"t"},timeout=45)
            r.raise_for_status()
            if len(r.content)!=item["size"] or not r.content.startswith(b"\xff\xd8"):
                raise ValueError("Download did not match original JPEG")
            path.write_bytes(r.content)
            with Image.open(path) as im:
                im.verify()
            return item["path"]
        except Exception as ex:
            error=ex
            time.sleep(attempt+1)
    raise RuntimeError(item["path"]) from error

with ThreadPoolExecutor(max_workers=4) as pool:
    futures=[pool.submit(download,item) for item in entries]
    for i,future in enumerate(as_completed(futures),1):
        name=future.result()
        if i%25==0 or i==len(entries):
            print("Downloaded",i,"/",len(entries),name,flush=True)
