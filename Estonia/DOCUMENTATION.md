# Estonia — documentație pentru prezentare

## Ce face programul

Auditează evaluarea unui clasificator de fraudă pentru e-Residency. Demonstrează că împărțirea pe rânduri permite apariția aceleiași identități atât la antrenare, cât și la test; evaluarea corectată exclude toate aplicațiile identității testate.

## Fișiere și dependențe

`estonia-fraud-audit/project_pipeline.py` reproduce evaluarea inițială; `audit.py` compară controalele; `corrected_pipeline.py` reproduce soluția finală. `applications.csv`, `results.json` și documentația tehnică originală sunt prezente. Fișierul `Estonia` de la rădăcina țării este gol. Dependențele sunt în `estonia-fraud-audit/requirements.txt`.

## Intrări și ieșiri

1.971 de aplicații. Ținta este `label`; caracteristicile sunt cele șase coloane numerice după eliminarea `submission_id`, `date_of_birth`, `citizenship`, `label`. Cheia `date_of_birth|citizenship` este folosită numai pentru gruparea evaluării.

## Algoritmul, pas cu pas

1. Reproduce împărțirea inițială 80%/20%, seed 1137, cu scaler învățat pe întregul set.
2. Mută scalerul în pipeline și compară împărțirea simplă și cea stratificată pe rânduri.
3. Măsoară câte identități din test apar deja în antrenare și separă performanța pe identități văzute/nevăzute.
4. Compară LeaveOneOut pe rânduri cu LeaveOneGroupOut pe cheia identității. În fiecare fold, scalerul și 1-NN sunt reînvățate numai pe celelalte grupuri.
5. Agregă o singură predicție out-of-fold pentru fiecare rând și calculează acuratețea; rotunjește procentul pentru flag. Salvează raportul comparativ în `results.json`.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
.venv/bin/python Estonia/estonia-fraud-audit/corrected_pipeline.py
.venv/bin/python Estonia/estonia-fraud-audit/audit.py
# Pentru pipeline-ul original, directorul curent trebuie să conțină CSV-ul:
cd Estonia/estonia-fraud-audit
../../.venv/bin/python project_pipeline.py
```

## Rezultat și dovezi

Raportul existent: 1.511/1.971 corecte, acuratețe 0,7666159309994927, flag `SIGMOID_77`. Există 900 de grupuri de identitate; 308 dintre cele 395 de rânduri din testul inițial au identitatea prezentă în antrenare.

## Note, alegeri și limite

Data nașterii și cetățenia sunt doar un proxy de identitate; două persoane distincte pot împărți aceeași cheie. LeaveOneOut pe rânduri nu rezolvă identitățile repetate. Cele 900 de folduri presupun multe ajustări 1-NN; auditul este mai lent decât un singur holdout. Documentația detaliată în engleză este păstrată în subfolder.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [estonia-fraud-audit/audit.py](estonia-fraud-audit/audit.py) | `model`: 29–30 |
| [estonia-fraud-audit/corrected_pipeline.py](estonia-fraud-audit/corrected_pipeline.py) | Flux executat la nivelul modulului, de sus în jos. |
| [estonia-fraud-audit/project_pipeline.py](estonia-fraud-audit/project_pipeline.py) | Flux executat la nivelul modulului, de sus în jos. |


Exemplu pentru „ce face linia 45?” în `estonia-fraud-audit/audit.py`:

```python
accuracy = accuracy_score(y, group_loo)  # Stabilește accuracy: proporția predicțiilor corecte în evaluarea pe identități.
```

## Întrebări probabile și răspunsuri scurte

### Dacă eliminăm identitatea din X, de ce mai există leakage?

Alte semnale ale aplicațiilor repetate rămân foarte similare, iar 1-NN poate recunoaște vecinii aceleiași identități.

### De ce scalerul este în pipeline?

Fiecare fold învață media și scara exclusiv din antrenare.

### De ce 77 și nu 76?

Flagul folosește procentul rotunjit, iar 76,661593% se rotunjește la 77.

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
