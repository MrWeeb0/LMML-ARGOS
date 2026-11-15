from pathlib import Path
import base64,csv,io,json,subprocess,sys
import numpy as np
import pywt,cv2
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,uniform_filter
from scipy.linalg import eigh

root=Path(__file__).resolve().parent
out=root/"lab-results"
out.mkdir(exist_ok=True)
rows=list(csv.DictReader((root/"toorisugari.csv").open()))
files=sorted((root/"dataset"/"credited"/"toorisugari").glob("*.jpg"))
files.extend(root/"dataset"/"anonymous"/r["file"] for r in rows)
manifest=json.loads((root/"source_manifest.json").read_text())
dates={x["path"]:x["modified"] for x in manifest}
words=("","toorisugari","Toorisugari","TOORISUGARI","jimaku","Jimaku","passerby","SIGMOID")

def check_payload(path,tag):
    if not path.exists():
        return
    raw=path.read_bytes()
    print("RECOVERED PAYLOAD",tag,len(raw),repr(raw[:400]),flush=True)
    if b"SIGMOID" in raw.upper():
        print("FLAG CANDIDATE",tag,repr(raw),flush=True)

def stego():
    for i,path in enumerate(files):
        for key in words:
            dest=out/(path.stem+"-"+str(i)+"-payload")
            r=subprocess.run(["steghide","extract","-sf",str(path),"-p",key,"-xf",str(dest),"-f"],
                             capture_output=True,timeout=15)
            if r.returncode==0:
                check_payload(dest,("steghide",str(path),key))
            r=subprocess.run(["outguess","-k",key,"-r",str(path),str(dest)],
                             capture_output=True,timeout=15)
            if r.returncode==0 and dest.exists() and dest.stat().st_size:
                check_payload(dest,("outguess",str(path),key))
        if i%9==8:
            print("Stego scanned",i+1,"/",len(files),flush=True)

def ocr():
    with (out/"ocr.txt").open("w") as stream:
        for path in files:
            r=subprocess.run(["tesseract",str(path),"stdout","-l","eng+jpn","--psm","11"],
                             capture_output=True,timeout=40)
            text=r.stdout.decode("utf-8",errors="replace")
            stream.write(str(path)+"\n"+text+"\n")
            print("OCR",path.name,repr(text[:1200]),flush=True)

def noise(image,sigma):
    c=pywt.wavedec2(image,"db4",level=4)
    c[0]=np.zeros_like(c[0])
    for k in range(1,len(c)):
        details=[]
        for b in c[k]:
            variance=np.minimum.reduce([uniform_filter(b*b,s) for s in (3,5,7,9)])
            details.append(b*np.minimum(1,sigma*sigma/np.maximum(1e-8,variance)))
        c[k]=tuple(details)
    return pywt.waverec2(c,"db4")[:image.shape[0],:image.shape[1]]

def stretch(a,size=(384,288)):
    lo,hi=np.quantile(a,[.01,.99])
    return Image.fromarray(np.uint8(np.clip((a-lo)*255/max(hi-lo,1e-15),0,255))).resize(size)

def publish(im,name):
    im.save(out/(name+".jpg"),quality=93)
    buf=io.BytesIO()
    im.save(buf,format="JPEG",quality=80)
    print("JAPAN_IMAGE",name,base64.b64encode(buf.getvalue()).decode(),flush=True)
    data=np.array(im.convert("L"))
    try:
        decoded,_,_=cv2.QRCodeDetector().detectAndDecode(data)
        if decoded:
            print("QR CANDIDATE",name,repr(decoded),flush=True)
    except cv2.error:
        pass

def images():
    meta=np.load(root/"metadata.npz")
    K=np.load(root/"kernel.npy")
    ids=np.flatnonzero(meta["labels"]=="toorisugari")
    _,vec=eigh((K[0]-K[1])[np.ix_(ids,ids)])
    directions=list(((vec[:,-1]<0)^(vec[0,-1]<0)).astype(int))
    directions.extend(int(r["orientation"]) for r in rows)
    week=np.r_[np.zeros(len(ids),int),[int(r["week"]) for r in rows]]
    chronological=sorted(range(len(ids),len(files)),
                         key=lambda i:dates["anonymous/"+files[i].name])
    photos=[np.array(Image.open(p).convert("L"),np.float32) for p in files]
    contact=Image.new("RGB",(9*160,5*136))
    dr=ImageDraw.Draw(contact)
    for j,i in enumerate(chronological):
        contact.paste(Image.fromarray(np.uint8(photos[i])).resize((160,120)),(j%9*160,j//9*136))
        dr.text((j%9*160+2,j//9*136+121),files[i].name,fill="white")
    publish(contact,"chronological-contact")
    for sigma in (2,4,8):
        residual=np.stack([noise(im,sigma) for im in photos])
        mask=np.stack([np.clip(im/45,0,1)*np.clip((255-im)/30,0,1) for im in photos])
        for aligned in (False,True):
            R=residual.copy()
            P=np.stack(photos)
            M=mask.copy()
            if aligned:
                for i,d in enumerate(directions):
                    if d:
                        R[i]=R[i,::-1,::-1]
                        P[i]=P[i,::-1,::-1]
                        M[i]=M[i,::-1,::-1]
            local=np.sqrt(4+uniform_filter(R*R,(1,13,13)))
            features=np.clip(R,-3*local,3*local)*M/local**1.2
            templates=[]
            for w in (0,8,9,10,11,12,-1):
                take=week==w if w>=0 else week>0
                templates.append((features[take].sum(axis=0)/(M[take].sum(axis=0)+1e-9),
                                  (R[take]*P[take]*M[take]).sum(axis=0)/
                                  ((P[take]*P[take]*M[take]).sum(axis=0)+1e-9)))
            templates=np.array(templates)
            np.save(out/f"templates-{sigma}-{int(aligned)}.npy",templates)
            canvas=Image.new("RGB",(4*384,7*304))
            dr=ImageDraw.Draw(canvas)
            for row,w in enumerate((0,8,9,10,11,12,-1)):
                for col,(typ,blur) in enumerate(((0,0),(0,2),(1,2),(1,10))):
                    value=templates[row,typ]
                    value=gaussian_filter(value,blur)
                    value-=value.mean(axis=0)
                    value-=value.mean(axis=1,keepdims=True)
                    canvas.paste(stretch(value),(col*384,row*304))
                    dr.text((col*384+2,row*304+289),f"week {w} mode {typ} blur {blur}",fill="white")
            publish(canvas,f"db4-{sigma}-{int(aligned)}")
        del residual
    print("Image analysis completed",flush=True)

mode=sys.argv[1]
if mode=="stego":
    stego()
elif mode=="ocr":
    ocr()
elif mode=="images":
    images()
