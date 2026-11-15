from pathlib import Path
import csv,json,subprocess,sys
import requests

root=Path(__file__).resolve().parent
out=root/"seek-results"
out.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/"toorisugari.csv").open()))
batch=int(sys.argv[1])
selected=rows[batch*9:(batch+1)*9]
manifest={x["path"]:x for x in json.loads((root/"source_manifest.json").read_text())}
wordlist=out/"words.txt"
r=requests.get("https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt",timeout=90)
r.raise_for_status()
wordlist.write_bytes(r.content+b"\ntoorisugari\nToorisugari\nTOORISUGARI\njimaku\nJimaku\nJIMAKU\npasserby\nSIGMOID\n")
results=[]
for row in selected:
    item=manifest["anonymous/"+row["file"]]
    image=out/row["file"]
    r=requests.get("https://drive.usercontent.google.com/download",
                   params={"id":item["id"],"export":"download","confirm":"t"},timeout=60)
    r.raise_for_status()
    if len(r.content)!=item["size"] or not r.content.startswith(b"\xff\xd8"):
        raise ValueError("Original JPEG verification failed")
    image.write_bytes(r.content)
    for mode in ("crack","seed"):
        dest=out/(image.stem+"-"+mode+".out")
        command=["stegseek","--"+mode,str(image)]
        if mode=="crack":command.append(str(wordlist))
        command.extend([str(dest),"-f","-q","-n","-t","2"])
        try:
            p=subprocess.run(command,capture_output=True,timeout=180)
            log=(p.stdout+p.stderr).decode("utf-8",errors="replace")
            entry={"file":image.name,"mode":mode,"code":p.returncode,"log":log[-4000:]}
            if dest.exists():
                raw=dest.read_bytes()
                entry["payload_bytes"]=len(raw)
                entry["payload_start"]=repr(raw[:300])
                if b"SIGMOID" in raw.upper() or all(32<=b<127 or b in (9,10,13) for b in raw):
                    print("SEEK PAYLOAD",image.name,mode,repr(raw[:4000]),flush=True)
            print("SEEK RESULT",json.dumps(entry),flush=True)
            results.append(entry)
        except subprocess.TimeoutExpired:
            entry={"file":image.name,"mode":mode,"timeout":180}
            print("SEEK RESULT",json.dumps(entry),flush=True)
            results.append(entry)
        if dest.exists() and dest.stat().st_size and mode=="crack":
            break
    image.unlink()
wordlist.unlink()
(out/f"results-{batch}.json").write_text(json.dumps(results,indent=2))
