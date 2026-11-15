import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from features import cv2

root=Path(__file__).parent

def glyph(letter,width,height):
    mask=np.zeros((220,220),np.uint8)
    cv2.putText(mask,letter,(10,180),cv2.FONT_HERSHEY_SIMPLEX,5,255,6,cv2.LINE_AA)
    ys,xs=np.where(mask>0);mask=mask[ys.min():ys.max()+1,xs.min():xs.max()+1]
    return cv2.resize(mask,(width,height),interpolation=cv2.INTER_AREA).astype(np.float32)/255

if __name__=='__main__':
    results=[];canvas=Image.new('RGB',(2000,380),'white');draw=ImageDraw.Draw(canvas)
    for method in ['output','context-output','context-aug-output']:
        ranks=[]
        for ai in range(1,6):
            maps=[]
            for path in sorted((root/method/'heatmaps').glob(f'album_{ai}-*.npz')):
                p=np.load(path)['heat'];valid=p>0
                p=cv2.GaussianBlur(p,(0,0),2)
                p=np.exp((p-p.max())/.12)*valid
                p/=p.sum()+1e-8
                maps.append(p)
            field=cv2.GaussianBlur(np.sum(maps,axis=0),(0,0),3)
            field/=field.std()+1e-8
            scores=[]
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                best=(-1,None)
                for width in [140,180,220,260]:
                    for height in [160,200,240]:
                        template=glyph(letter,width,height)
                        template=(template-template.mean())/(np.linalg.norm(template-template.mean())+1e-8)
                        response=cv2.matchTemplate(field,template,cv2.TM_CCORR)
                        allowed=response.copy()
                        yy,xx=np.mgrid[:response.shape[0],:response.shape[1]]
                        allowed[(xx<50)|(xx+width>350)|(yy<20)|(yy+height>290)]=-1e6
                        y,x=np.unravel_index(allowed.argmax(),allowed.shape)
                        value=float(allowed[y,x])
                        if value>best[0]:best=(value,[int(x),int(y),width,height])
                scores.append({'letter':letter,'score':best[0],'box':best[1]})
            scores.sort(key=lambda x:-x['score']);ranks.append(scores)
            print(method,'album',ai,[(x['letter'],round(x['score'],2)) for x in scores[:6]],flush=True)
        results.append({'method':method,'albums':ranks})
    (root/'glyph-experiments.json').write_text(json.dumps(results,indent=2)+'\n')
