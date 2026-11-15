# France — documentație pentru prezentare

## Ce face programul

Separă anunțurile din sursa publică de punctele injectate în setul Paris, apoi grupează și proiectează candidații pentru a afișa șase litere. Lectura literelor și orientările de afișare sunt stabilite manual în cod.

## Fișiere și dependențe

`solve.py`, `paris_listings.csv`, `labels.csv`, `results.json`, `pointillist_clusters.png`. Referința locală `insideairbnb.csv.gz` lipsește. Dependențe: NumPy, pandas, Matplotlib și o versiune scikit-learn care exportă HDBSCAN.

## Intrări și ieșiri

CSV-ul intern și snapshotul public configurat în REFERENCE_URL. Comparația folosește toate coloanele interne în afară de listing_id. Clusteringul folosește longitude, latitude, price, availability_365.

## Algoritmul, pas cu pas

1. Uniformizează numele coloanelor, prețul, indicatorul superhost și precizia coordonatelor/scorurilor în referință.
2. Asociază rândurile după conținut, ignorând ID-urile înlocuite. Selectează rândurile fără potrivire în referință.
3. Standardizează cele patru caracteristici și aplică HDBSCAN: min_cluster_size=40, min_samples=6, metoda eom.
4. Exclude eticheta −1 (zgomot), sortează grupurile după prețul mediu și verifică existența a exact șase grupuri.
5. Proiectează separat fiecare grup prin standardizare și PCA cu două componente și whitening. Aplică rotațiile și reflexia manuală pentru lizibilitate.
6. Atribuie etichetele din constanta READING="NEURON" și scrie imaginea, etichetele pe rânduri și raportul JSON.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
.venv/bin/python France/solve.py --download-reference
# Dacă referința este deja disponibilă:
.venv/bin/python France/solve.py --reference /cale/catre/listings.csv.gz
```

## Rezultat și dovezi

`results.json` existent: 28.108 rânduri, 26.163 potriviri în referință, 1.945 de puncte în șase clustere; `SIGMOID_NEURON`. Nu s-a reverificat online snapshotul în această sarcină de documentare.

## Note, alegeri și limite

Scriptul nu execută OCR: NEURON este o interpretare vizuală introdusă explicit. Unghiurile și reflexia sunt pentru afișare. Alegerea snapshotului și rotunjirile sunt decisive pentru selecția candidaților; lipsa unei potriviri poate proveni și din diferențe de versiune, nu doar din injecție. HDBSCAN și comparația tabelară necesită păstrarea datelor în memorie.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [solve.py](solve.py) | `source_matches`: 31–55; `main`: 58–136 |


Exemplu pentru „ce face linia 45?” în `solve.py`:

```python
for column in ["latitude", "longitude"]:  # Parcurge ['latitude', 'longitude']; elementul curent este column.
```

## Întrebări probabile și răspunsuri scurte

### De ce ignorăm listing_id?

ID-urile pot fi înlocuite; potrivirea urmărește conținutul celorlalte coloane.

### De ce standardizăm înainte de clustering?

Prețul și disponibilitatea au scări diferite de coordonate; altfel ar domina distanțele.

### Sunt literele descoperite automat?

Grupurile și proiecțiile sunt calculate; numele literelor și orientările sunt configurate manual.

## Spațiu pentru întrebări la prezentare

Completați pentru fiecare întrebare fișierul și linia discutată. Spațiul de mai jos este lăsat intenționat pentru notițe.

### Întrebarea 1

**Fișier / linie:** ______________________________________________

**Întrebare:** __________________________________________________

Notițe: _________________________________________________________

**Răspuns / exemplu:** __________________________________________

Notițe: _________________________________________________________

Notițe: _________________________________________________________

### Întrebarea 2

**Fișier / linie:** ______________________________________________

**Întrebare:** __________________________________________________

Notițe: _________________________________________________________

**Răspuns / exemplu:** __________________________________________

Notițe: _________________________________________________________

Notițe: _________________________________________________________

### Întrebarea 3

**Fișier / linie:** ______________________________________________

**Întrebare:** __________________________________________________

Notițe: _________________________________________________________

**Răspuns / exemplu:** __________________________________________

Notițe: _________________________________________________________

Notițe: _________________________________________________________

### Întrebarea 4

**Fișier / linie:** ______________________________________________

**Întrebare:** __________________________________________________

Notițe: _________________________________________________________

**Răspuns / exemplu:** __________________________________________

Notițe: _________________________________________________________

Notițe: _________________________________________________________

### Întrebarea 5

**Fișier / linie:** ______________________________________________

**Întrebare:** __________________________________________________

Notițe: _________________________________________________________

**Răspuns / exemplu:** __________________________________________

Notițe: _________________________________________________________

Notițe: _________________________________________________________
