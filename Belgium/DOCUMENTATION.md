# Belgium — documentație pentru prezentare

## Ce face programul

Estimează `edge_m` prin regresie liniară pe dimensiunile declarate de fermieri. Reziduurile sunt desenate în funcție de predicții pentru citirea unui cuvânt ascuns.

## Fișiere și dependențe

`solve_belgia.py` — calcul OLS și grafic. `Code_Generated_Image.png` și README-ul sunt materiale existente. `potato_fields.csv` nu este prezent. Dependențe: NumPy, pandas, Matplotlib.

## Intrări și ieșiri

CSV cu cel puțin `area_ha`, `long_side_m`, `ditch_m`, `edge_m`. Lungimea laturii lungi trebuie să fie nenulă. Fișierul este căutat în directorul curent.

## Algoritmul, pas cu pas

1. Convertește suprafața din hectare în m², înmulțind cu 10.000.
2. Deduce latura scurtă: suprafață / latura lungă.
3. Construiește matricea cu patru coloane: unu pentru intercept, latura lungă, latura scurtă, șanț.
4. Rezolvă OLS cu `np.linalg.lstsq`, apoi calculează predicțiile, reziduurile, R² și RMSE.
5. Desenează reziduurile față de lungimile prezise și salvează `belgia_residuals.png`; deschide și fereastra grafică.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
cd Belgium
../.venv/bin/python solve_belgia.py
```

## Rezultat și dovezi

README-ul raportează R² ≈ 0,999984, RMSE ≈ 0,9570 m și lectura vizuală `SIGMOID_SUPERVISION`. Scriptul afișează coeficienți și metrici; nu recunoaște automat literele și nu tipărește flagul.

## Note, alegeri și limite

`hedge_m` și `fence_quote_eur` sunt excluse deoarece sunt informații apărute după măsurarea țintei. Metricile sunt calculate pe aceleași date pe care este ajustat OLS, nu pe un set de test separat. Un R² mare nu garantează alegerea corectă a caracteristicilor. Costul OLS este liniar în numărul de rânduri pentru cele patru coloane fixe.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [solve_belgia.py](solve_belgia.py) | `main`: 10–44 |


Exemplu pentru „ce face linia 45?” în `solve_belgia.py`:

Linia 45 este goală: separă blocurile și nu execută nicio operație.

## Întrebări probabile și răspunsuri scurte

### De ce există o coloană de unu?

Coeficientul ei este interceptul regresiei.

### De ce nu folosim hedge_m?

Este măsurată ulterior și poate produce leakage; README-ul descrie chiar un cuvânt-capcană când este inclusă.

### De ce desenăm erorile?

Scădem relația geometrică dominantă, iar structura ascunsă din abateri devine vizibilă.

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
