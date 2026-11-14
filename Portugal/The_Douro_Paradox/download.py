import hashlib
from pathlib import Path
from urllib.request import urlopen

p=Path('douro_vineyard_data.csv')
if p.exists():data=p.read_bytes()
else:
 with urlopen('https://drive.google.com/uc?export=download&id=1L8BmLUtVP-Amp7ysujx1alTYtTRiFkeM',timeout=60) as response:data=response.read()
if hashlib.sha256(data).hexdigest()!='8c72d48fa0c17835269aca101e1ad1e997436e0c0fa25091518a1d8eda3dabc5':raise ValueError('Unexpected dataset')
p.write_bytes(data)
print('Dataset verified')
