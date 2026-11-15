import csv,json
from pathlib import Path
from PIL import Image,ImageDraw

root=Path(__file__).parent
selected=set((root/'test-output.txt').read_text().splitlines())
revision=json.loads((root/'revision.json').read_text()) if (root/'revision.json').exists() else {'added':[]}
with (root/'scores.csv').open(newline='',encoding='utf-8') as stream:rows=[r for r in csv.DictReader(stream) if r['image'] in selected]
sheet=Image.new('RGB',(728,1440),'white');draw=ImageDraw.Draw(sheet)
for i,row in enumerate(rows):
 x=(i%7)*104;y=(i//7)*360
 image=Image.open(root/row['image']).convert('RGB')
 image=image.rotate(float(row['angle']),resample=Image.Resampling.BILINEAR)
 image=image.crop(tuple(int(row[k]) for k in ['x0','y0','x1','y1'])).resize((96,320))
 sheet.paste(image,(x,y))
 draw.text((x+2,y+322),Path(row['image']).stem[-4:]+' '+str(round(float(row['score']),2)),fill='black')
sheet.save(root/'review.jpg',quality=92)
print(root/'review.jpg')
