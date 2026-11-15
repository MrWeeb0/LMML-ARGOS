# Portugal — documentație pentru prezentare

## Ce face programul

Identifică variabila care explică un paradox Simpson în rezultatele recoltelor. Tratamentul are succes mai mare agregat, dar controlul câștigă separat în fiecare dintre două grupuri definite de un prag.

## Fișiere și dependențe

În `The_Douro_Paradox/`: `download.py` recuperează și verifică datele; `main.py` caută inversarea; `verify.py` confirmă cu fracții exacte; `solution.ipynb` le rulează. Rezultatele JSON/CSV și flag.txt sunt prezente. CSV-ul brut nu este inclus. Numai biblioteca standard Python este necesară pentru scripturi.

## Intrări și ieșiri

`douro_vineyard_data.csv`: exact 3.543 de parcele cu plot_id unic, treatment în {control,treatment}, harvest_success în {0,1}, plus variabilele candidate fără valori goale. download.py verifică SHA-256-ul așteptat.

## Algoritmul, pas cu pas

1. Numără vectorul [succese control, total control, succese tratament, total tratament] și confirmă avantajul agregat al tratamentului.
2. Exclude ID-ul, tratamentul și rezultatul din coloanele candidate. Încearcă interpretarea numerică a fiecărei coloane.
3. Pentru o coloană numerică, acumulează contoarele în ordinea valorilor și testează fiecare prag dintre niveluri observate. Cere avantaj strict pentru control pe ambele părți.
4. Pentru categorii, verifică dacă fiecare categorie produce avantajul controlului. Cere un singur candidat final și ca acesta să fie numeric.
5. Alege cel mai mare prag valid, construiește cele două grupuri și scrie result.json, rates.csv și flag.txt, inclusiv explicația ponderilor.
6. verify.py recalculează ratele cu Fraction, verifică inegalitățile, contoarele și partiția completă; scrie verification.json.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
cd Portugal/The_Douro_Paradox
../../.venv/bin/python download.py
../../.venv/bin/python main.py
../../.venv/bin/python verify.py
```

## Rezultat și dovezi

Raportul existent identifică `distance_from_porto_km`, prag 104 km, flag `SIGMOID_DISTANCE_FROM_PORTO_KM`. Agregat: control 447/1653, tratament 585/1890. ≤104 km: 312/1233 față de 36/144; >104 km: 135/420 față de 549/1746.

## Note, alegeri și limite

Există mai multe praguri valide între 102,9 și 104,0; regula implementată alege maximul observat, nu susține unicitatea pragului. Tratamentul are o pondere mai mare în grupul cu rată generală de succes mai mare, ceea ce inversează comparația agregată. Inegalitățile prin produse încrucișate evită erorile de rotunjire. Screeningul numeric costă aproximativ O(C × N log N). Asocierea observată nu dovedește singură un efect cauzal.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [The_Douro_Paradox/download.py](The_Douro_Paradox/download.py) | Flux executat la nivelul modulului, de sus în jos. |
| [The_Douro_Paradox/main.py](The_Douro_Paradox/main.py) | `counts`: 5–9; `reversal`: 11–12; `rates`: 14–15; `screen`: 17–33; `main`: 35–58 |
| [The_Douro_Paradox/verify.py](The_Douro_Paradox/verify.py) | `main`: 5–21 |

Notebookul `The_Douro_Paradox/solution.ipynb` are comentarii și în cele trei celule de cod. El execută aceleași scripturi, nu implementează un algoritm separat.

## Întrebări probabile și răspunsuri scurte

### Cum poate pierde tratamentul în ambele grupuri și câștiga global?

Ratele agregate folosesc ponderi diferite ale grupurilor pentru control și tratament.

### De ce 104 km?

Este cel mai mare prag observat care satisface regula strictă în ambele grupuri; alte praguri din interval sunt și ele valide.

### De ce Fraction în verificare?

Compară exact ratele raționale, fără efecte de rotunjire în virgulă mobilă.

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
