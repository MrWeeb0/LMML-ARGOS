from pathlib import Path
import base64,io,re
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter

root=Path(__file__).resolve().parent
out=root/"phase-results"
out.mkdir(exist_ok=True)
dictionary=set()
try:
    import requests
    r=requests.get("https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english.txt",timeout=20)
    r.raise_for_status()
    dictionary={s.upper() for s in r.text.split() if len(s)>=5}
except Exception as ex:
    print("Dictionary unavailable",type(ex).__name__,flush=True)

def stretch(a,size=(256,256)):
    lo,hi=np.quantile(a,[.01,.99])
    x=np.uint8(np.clip((a-lo)*255/max(1e-12,hi-lo),0,255))
    return Image.fromarray(x).resize(size,Image.Resampling.NEAREST)

def publish(im,name):
    im.save(out/(name+".png"))
    buf=io.BytesIO()
    im.save(buf,format="JPEG",quality=78)
    print("JAPAN_IMAGE",name,base64.b64encode(buf.getvalue()).decode(),flush=True)

def decode(a,tag):
    for transform in range(8):
        image=np.rot90(a,transform%4)
        if transform>=4:image=image[:,::-1]
        for center in (0,1,2,3):
            value=image.copy()
            if center&1:value-=value.mean(axis=0)
            if center&2:value-=value.mean(axis=1,keepdims=True)
            for threshold in (0,np.median(value)):
                bits=(value>threshold).ravel().astype(np.uint8)
                for inv in (0,1):
                    for shift in range(8):
                        for order in ("big","little"):
                            raw=np.packbits(bits[shift:]^inv,bitorder=order).tobytes()
                            for match in re.finditer(br"[A-Z_]{5,}",raw):
                                s=match.group().decode()
                                if s in dictionary or "SIGMOID" in s:
                                    print("PHASE WORD",tag,transform,center,threshold,inv,shift,order,match.start(),s,flush=True)

for path in sorted((root/"remote-artifact"/"lab-results").glob("templates-*.npy")):
    data=np.load(path)
    for mode in (0,1):
        maps=[data[-1,mode],data[0,mode],data[-1,mode]-data[0,mode]]
        canvas=Image.new("RGB",(7*224,3*244))
        dr=ImageDraw.Draw(canvas)
        for row,value in enumerate(maps):
            for col,p in enumerate((4,8,16,32,64,128,256)):
                h,w=value.shape
                y=value[:h//p*p,:w//p*p].reshape(h//p,p,w//p,p).mean(axis=(0,2))
                decode(y,(path.name,mode,row,p))
                canvas.paste(stretch(y,(224,224)),(col*224,row*244))
                dr.text((col*224+2,row*244+225),f"map {row} period {p}",fill="white")
        publish(canvas,path.stem+"-phase-"+str(mode))
print("Phase analysis completed",flush=True)
