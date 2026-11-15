# Germany — documentație pentru prezentare

## Ce face programul

Identifică o funcție deterministă cu cinci intrări printr-un număr limitat de întrebări adresate oracolului. Modelul presupune efecte liniare centrate, un singur produs între două variabile și un salt activat de un semispațiu.

## Fișiere și dependențe

`BlackBox.py` exportă `solve(oracle, points)`. `README` descrie rezultatul istoric. Oracolul și evaluatorul nu sunt incluse. Dependență: NumPy.

## Intrări și ieșiri

Obiect cu `ask(p, phase=...)` și `remaining`, plus o matrice de puncte cu cinci coloane. Evaluatorul gestionează bugetul; codul folosește toate interogările prin funcția internă ask și le memorează.

## Algoritmul, pas cu pas

1. Interoghează 32 de combinații locale la nivelurile 0,375/0,625 și ajustează constanta, cinci efecte și zece produse perechi.
2. Interoghează cele 32 de colțuri globale. Dacă ajustarea locală este contaminată de salt sau nu are exact un produs, caută prin consens familia cu un singur produs.
3. Separă reziduurile de la colțuri în două niveluri și identifică muchiile pe care nivelul se schimbă; variabilele acelor muchii formează poarta.
4. Alege traversări diverse geometric și localizează frontiera prin bisecții, lăsând buget pentru verificare.
5. Estimează planul prin SVD, îi orientează normala către nivelul superior și normalizează coeficienții.
6. Adaugă până la zece probe independente și reajustează modelul pe puncte la distanță > 0,002 de frontieră. Returnează variabile relevante, produs, discontinuitate, expresie și predicții.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
# Apel din evaluatorul challengeului, care furnizează oracle și points:
from Germany.BlackBox import solve
result = solve(oracle, points)
```

## Rezultat și dovezi

README-ul raportează 130/150 interogări, eroare maximă ≈ 10⁻⁶, interacțiune −4 × (x3−0,5)(x5−0,5), poartă x1+x4 ≥ 1,7 și salt +1,5. Valorile sunt învățate de cod, nu fixate în solver; rezultatul real depinde de oracol.

## Note, alegeri și limite

Modelul nu acoperă orice funcție cu cinci intrări. Presupune exact familia descrisă și suficientă geometrie pentru recuperarea planului. Primele 64 de interogări sunt necondiționate; bugetul inițial trebuie să le permită. Probele numite verification sunt apoi folosite și la reajustare; codul nu produce o metrică independentă de validare.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [BlackBox.py](BlackBox.py) | `solve`: 5–164; `ask`: 10–15; `features`: 17–20; `diversity`: 83–90 |


Exemplu pentru „ce face linia 45?” în `BlackBox.py`:

```python
b = np.linalg.solve(B[ix], y[ix])  # Rezolvă exact sistemul de șapte ecuații; un sistem singular este ignorat.
```

## Întrebări probabile și răspunsuri scurte

### De ce nu schimbăm o singură variabilă odată?

Produsul centrat dispare dacă unul dintre factori rămâne la 0,5; experimentul factorial îl face observabil.

### De ce SVD?

Punctele frontierei satisfac aproximativ n·x−t=0; vectorul singular corespunzător valorii minime estimează coeficienții planului.

### De ce excludem vecinătatea frontierei la reajustare?

O mică eroare a planului poate atribui greșit saltul unor puncte foarte apropiate de el.

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
