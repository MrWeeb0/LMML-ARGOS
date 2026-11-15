import hashlib  # Importă hashlib
from pathlib import Path  # Importă Path din pathlib
from urllib.request import urlopen  # Importă urlopen din urllib.request

p=Path('douro_vineyard_data.csv')  # Stabilește calea locală a CSV-ului brut, în directorul curent.
if p.exists():data=p.read_bytes()  # Reutilizează octeții existenți dacă fișierul a fost deja descărcat.
else:  # Traitează cazul în care condiția precedentă este falsă.
 with urlopen('https://drive.google.com/uc?export=download&id=1L8BmLUtVP-Amp7ysujx1alTYtTRiFkeM',timeout=60) as response:data=response.read()  # Descarcă octeții din sursa configurată numai dacă fișierul local lipsește.
if hashlib.sha256(data).hexdigest()!='8c72d48fa0c17835269aca101e1ad1e997436e0c0fa25091518a1d8eda3dabc5':raise ValueError('Unexpected dataset')  # Execută ramura dacă hashlib.sha256(data).hexdigest() != '8c72d48fa0c17835269aca101e1ad1e997436e0c0fa25091518a1d8eda3dabc5'. Semnalează eroarea și întrerupe această cale de execuție: ValueError('Unexpected dataset').
p.write_bytes(data)  # Scrie octeții în fișierul indicat.
print('Dataset verified')  # Afișează valorile sau mesajul pentru verificare.
