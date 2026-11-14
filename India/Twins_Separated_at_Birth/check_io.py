import csv,io,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
import cv2,numpy as np

root=Path(__file__).resolve().parent
raw=cv2.imencode('.jpg',np.random.default_rng(7).integers(0,256,(160,200,3),dtype=np.uint8))[1].tobytes()
cases=[('empty',{},set()),('single',{'a.jpg':raw},set()),('three_identical',{'a.jpg':raw,'b.jpg':raw,'c.jpg':raw},{('a.jpg','b.jpg'),('a.jpg','c.jpg'),('b.jpg','c.jpg')}),('nested_names',{'folder/red,one.jpg':raw,'nested/image.jpg':raw,'notes.txt':b'x'},{('folder/red,one.jpg','nested/image.jpg')})]
if (root/'images'/'img_000008.jpg').exists():
 a=(root/'images'/'img_000008.jpg').read_bytes();b=(root/'images'/'img_000009.jpg').read_bytes();c=(root/'images'/'img_000010.jpg').read_bytes()
 cases.extend([('resized_pair',{'z.jpg':a,'a.jpg':b},{('a.jpg','z.jpg')}),('different_capture',{'first.jpg':a,'second.jpg':c},set())])
results=[]
for name,files,expected in cases:
 with tempfile.TemporaryDirectory() as tmp:
  with zipfile.ZipFile(Path(tmp)/'test-input.zip','w') as archive:
   for key,value in files.items():archive.writestr(key,value)
  subprocess.run([sys.executable,str(root/'main.py')],cwd=tmp,check=True,capture_output=True)
  rows=list(csv.reader(open(Path(tmp)/'output.csv',newline='',encoding='utf-8')))
  assert rows[0]==['image_a','image_b']
  pred={tuple(row) for row in rows[1:]}
  assert pred==expected,(name,pred,expected)
  assert len(rows)-1==len(pred) and all(a!=b for a,b in pred)
  results.append(dict(case=name,passed=True,pairs=len(pred)))
Path(root/'checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
