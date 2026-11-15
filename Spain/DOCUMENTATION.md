# Spain — documentație pentru prezentare

## Ce face programul

Transformă cumpărăturile la preț corect într-o imagine binară cu produse pe rânduri și piloți pe coloane. Imaginea permite citirea vizuală a mesajului.

## Fișiere și dependențe

`solution.py`, `data/office_price_guide.csv`, `data/purchases.csv`, `board.png` și enunțul `¡Feliz Navidad!.md`. Dependențe: NumPy și Matplotlib; citirea CSV folosește biblioteca standard.

## Intrări și ieșiri

Ghid: Product, Fair_min_eur, Fair_max_eur, List_no. Cumpărături: Product, Total_paid_eur, Quantity, Pilot_no. Cantitatea trebuie să fie nenulă; produsul trebuie să existe în ghid.

## Algoritmul, pas cu pas

1. Încarcă ghidul într-un dicționar indexat după Product.
2. Inițializează cu zero o matrice cu câte un rând per produs și 21 de coloane.
3. Pentru fiecare cumpărătură calculează prețul unitar: Total_paid_eur / Quantity.
4. Acceptă tranzacția dacă prețul este între limitele corecte, inclusiv capetele intervalului.
5. Setează celula [List_no−1, Pilot_no−1] la unu pentru cumpărăturile acceptate.
6. Desenează matricea cu tonuri de gri și grilă, etichetează axele și scrie board.png.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
MPLBACKEND=Agg .venv/bin/python Spain/solution.py
```

## Rezultat și dovezi

Ieșirea programului este `Spain/board.png`. Scriptul nu tipărește flagul și nu recunoaște automat literele; rezultatul trebuie citit din desen.

## Note, alegeri și limite

Indicele începe de la zero în matrice, dar de la unu în CSV. Celula rămâne 1 dacă măcar o cumpărătură a perechii produs–pilot este corectă; o cumpărătură ulterioară incorectă nu o șterge. Axele presupun șase produse și 21 de piloți; alte date cer adaptarea constantelor. Ordinea etichetelor verticale presupune că ghidul este ordonat după List_no. Cost O(număr de cumpărături + număr de produse).

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [solution.py](solution.py) | Flux executat la nivelul modulului, de sus în jos. |

## Întrebări probabile și răspunsuri scurte

### De ce împărțim la Quantity?

Intervalele din ghid se referă la un produs, nu la valoarea totală a tranzacției.

### De ce scădem unu?

Convertim numerotarea din documente la indicii matricei Python.

### Ce înseamnă o celulă neagră?

Există cel puțin o cumpărătură la preț corect pentru acel produs și pilot.

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
