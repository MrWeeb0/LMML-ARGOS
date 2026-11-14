import hashlib
from pathlib import Path
from urllib.request import urlopen

files={
 'observations.csv':('1xZ6iDwlN8cnm-DJVcQi5hs1SlMqk-JVb','6349db410983a430b7b74865a10a28cc9f6b38855098e1b9ec4eb49bf73545bb'),
 'ring_register.csv':('182-PGO0lZyrkCvQa6FXQZ_ibg0K1awLp','9f8b59266700ab4000b8c3a4d3561fb0c1a0458bb91a7e1c94a093219afe93c8')
}
for name,(file_id,expected) in files.items():
 p=Path(name)
 if p.exists():data=p.read_bytes()
 else:
  with urlopen('https://drive.google.com/uc?export=download&id='+file_id,timeout=60) as response:data=response.read()
 if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Unexpected data: '+name)
 p.write_bytes(data)
 print(name+' verified')
