# Switzerland — documentație pentru prezentare

## Ce face programul

Antrenează un arbore de decizie pentru slab_released și reconstruiește un cuvânt din inițialele caracteristicilor folosite în splituri, parcurse în preordine.

## Fișiere și dependențe

`main.py`, `data/train-input.csv`, `data/train-output.txt` și README.md. Scriptul caută efectiv `test-input.csv` în directorul curent și scrie `test-output.txt`; acest nume de intrare nu există în checkout. Dependențe: pandas și scikit-learn.

## Intrări și ieșiri

DataFrame cu ținta slab_released și caracteristicile numerice. Fișierul de antrenare local poate fi folosit direct apelând recover_word; main.py nu are argument pentru calea de intrare.

## Algoritmul, pas cu pas

1. Elimină slab_released din caracteristici și păstrează coloana ca etichetă.
2. Antrenează DecisionTreeClassifier(random_state=0), fără limită explicită de adâncime.
3. Pornește vizitarea din nodul zero, rădăcina.
4. Ignoră frunzele, identificate prin indicele negativ al caracteristicii.
5. Pentru un nod intern, adaugă numele caracteristicii, apoi vizitează stânga și dreapta.
6. Concatenează prima literă cu majusculă a fiecărui nume, păstrând repetițiile, și adaugă prefixul SIGMOID_.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
# Reproduce pe datele disponibile fără schimbarea căilor din main.py:
.venv/bin/python - <<'PYCODE'
import ast
from pathlib import Path
import pandas as pd
source = ast.parse(Path("Switzerland/main.py").read_text())
# Încarcă importurile și funcția, fără codul de la nivelul modulului care citește test-input.csv.
source.body = [n for n in source.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
ns = {}
exec(compile(source, "Switzerland/main.py", "exec"), ns)
table = pd.read_csv("Switzerland/data/train-input.csv")
print("SIGMOID_" + ns["recover_word"](table))
PYCODE
```

## Rezultat și dovezi

Cuvântul depinde de arborele ajustat pe tabelul primit. `data/train-output.txt` oferă materialul de comparație local. Apelul verificat pe train-input.csv produce `SIGMOID_DEMO`, identic cu ieșirea locală de referință. Documentația evidențiază diferența dintre calea efectivă test-input.csv și fișierul disponibil.

## Note, alegeri și limite

Aceasta este o citire a structurii arborelui, nu doar o problemă de acuratețe. DFS este preordine: nod, stânga, dreapta. Frunzele nu au caracteristică de split. Repetițiile sunt semnificative și nu trebuie eliminate cu set. Ordinea coloanelor, datele și versiunea scikit-learn pot influența arborele; seed-ul fixează aleatorul, fără a garanta aceeași structură în orice versiune.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [main.py](main.py) | `recover_word`: 5–25; `visit`: 16–22 |

## Întrebări probabile și răspunsuri scurte

### De ce feature < 0 indică frunză?

Structura scikit-learn folosește un sentinel negativ când nodul nu mai separă după o caracteristică.

### De ce păstrăm caracteristicile repetate?

Fiecare nod intern contribuie o literă; același predictor poate produce mai multe litere.

### De ce preordine?

Ordinea nod–stânga–dreapta stabilește ordinea literelor; altă traversare poate forma alt cuvânt.

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
