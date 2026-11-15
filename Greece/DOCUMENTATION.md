# Greece — documentație pentru prezentare

## Ce face programul

Compară trei clasificatoare PyTorch de amenințări mitologice și selectează modelul cu recall maxim pentru amenințările catastrofale, la pragul de probabilitate 0,50.

## Fișiere și dependențe

`main.py` este prezent. Lipsesc `model.py` (arhitectura și FEATURE_COLUMNS), `test_dataset.csv`, `test_labels.csv` și cele trei fișiere `models/model_*.pth`. Dependențe: NumPy, pandas, PyTorch, scikit-learn.

## Intrări și ieșiri

Date cu `encounter_id` și coloanele din FEATURE_COLUMNS; etichete cu `encounter_id`, `is_catastrophic_threat`. Scriptul cere aceeași ordine a ID-urilor în ambele CSV-uri.

## Algoritmul, pas cu pas

1. Citește datele și etichetele din directorul curent și verifică alinierea encounter_id.
2. Construiește tensorul float32 cu caracteristicile în ordinea cerută de model.
3. Pentru ares, athena și apollo, instanțiază arhitectura și încarcă ponderile pe CPU.
4. Activează eval și no_grad; transformă logiturile în probabilități prin sigmoid.
5. Aplică pragul 0,50 și calculează accuracy, recall, precision, F1 și TN/FP/FN/TP.
6. Rotunjește tabelul la patru zecimale, selectează recall-ul maxim și afișează numele modelului în flag.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
cd Greece
../.venv/bin/python main.py
```

## Rezultat și dovezi

Formatul ieșirii este un tabel comparativ și `SIGMOID_<NUMELE_MODELULUI>`. Modelul câștigător nu poate fi stabilit din main.py fără date, arhitectură și checkpointuri.

## Note, alegeri și limite

Recall = TP/(TP+FN), precision = TP/(TP+FP). Alegerea favorizează evitarea amenințărilor ratate. `idxmax` operează după rotunjirea la patru zecimale; o egalitate astfel creată favorizează primul model. Codul presupune ieșiri compatibile cu un vector de etichete și prezența ambelor clase pentru ravel() pe matricea de confuzie. eval nu dezactivează gradientul; no_grad îndeplinește acest rol.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [main.py](main.py) | Flux executat la nivelul modulului, de sus în jos. |

## Întrebări probabile și răspunsuri scurte

### De ce sigmoid?

Modelul întoarce logituri, iar sigmoid le transformă în probabilități înaintea pragului.

### De ce recall și nu accuracy?

Criteriul din soluție acordă prioritate reducerii falselor negative.

### De ce verificăm ID-urile?

Fără aliniere am compara predicția unui exemplu cu eticheta altuia.

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
