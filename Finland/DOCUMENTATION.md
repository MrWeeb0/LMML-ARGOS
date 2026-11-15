# Finland — documentație pentru prezentare

## Ce face programul

Construiește un graf neorientat al rutelor dintre orașe finlandeze, unește variantele lingvistice ale numelor și extrage inițialele celor șapte orașe cu cele mai multe conexiuni.

## Fișiere și dependențe

`solve.py` și `routes.csv` sunt prezente. Folosește exclusiv biblioteca standard Python: csv, re, unicodedata, collections, pathlib.

## Intrări și ieșiri

`routes.csv`, coloanele `from_town` și `to_town`. Se citește UTF-8 cu toleranță la BOM. Calea este raportată la script.

## Algoritmul, pas cu pas

1. Încarcă toate rutele și colectează numele de la ambele capete.
2. Aplică dicționarul ALIASES după eliminarea punctelor/spațiilor și normalizarea literelor cu casefold.
3. Grupează suplimentar numele după eliminarea accentelor Unicode și alege un reprezentant prin ordonarea explicită din cod.
4. Reprezintă o conexiune prin perechea sortată a capetelor; mulțimea elimină rutele duplicate și inversele lor.
5. Numără contribuția fiecărei conexiuni la gradul celor două capete și verifică 116 orașe, 448 conexiuni.
6. Ordonează descrescător după grad și concatenează inițialele primelor șapte orașe.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
python3 Finland/solve.py
```

## Rezultat și dovezi

Scriptul afișează numărul orașelor/conexiunilor, primele șapte orașe cu gradele lor și flagul construit din inițiale. Execuția verificată a produs `SIGMOID_HOTLINE`, cu orașele Helsinki, Orivesi, Tornio, Lieksa, Imatra, Nokia, Eura. Cuvântul nu este o constantă din cod.

## Note, alegeri și limite

Normalizarea numelor este esențială: Helsinki și Helsingfors trebuie să fie același nod. Codul nu elimină explicit buclele unui oraș către el însuși; una ar incrementa de două ori gradul. Pentru grade egale, Counter păstrează ordinea întâlnirii, iar mulțimile pot influența ordinea; pe alte date ar fi preferabil un criteriu secundar explicit. Cost dominant: parcurgerea rutelor și sortarea orașelor.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [solve.py](solve.py) | `lookup_key`: 99–100; `remove_accents`: 103–108; `canonical_names`: 111–134; `main`: 137–165 |


Exemplu pentru „ce face linia 45?” în `solve.py`:

```python
"Kronoby": "Kruunupyy",  # Asociază varianta de nume cu numele canonic finlandez.
```

## Întrebări probabile și răspunsuri scurte

### De ce sortăm capetele rutei?

Pentru ca A–B și B–A să aibă aceeași reprezentare și să fie numărate o singură dată.

### De ce eliminăm accentele doar la comparare?

Unim ortografiile echivalente și păstrăm un nume reprezentativ pentru afișare.

### Ce reprezintă gradul?

Numărul conexiunilor incidente orașului după deduplicare.

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
