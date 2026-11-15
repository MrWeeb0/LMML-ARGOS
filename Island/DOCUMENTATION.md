# Iceland (folderul Island) — documentație pentru prezentare

## Ce face programul

[main.py](main.py) curăță observații de temperatură dintr-un CSV cu preambul și duplicate. Repară anumite nume de stații cu diacritice corupte, convertește Fahrenheit în Celsius, rotunjește la o zecimală și alege pentru fiecare ID perechea temperatură–dată cea mai frecventă.

## Fișiere și dependențe

Codul se află în `Island/main.py`; numele țării în index rămâne Iceland. Programul folosește numai biblioteca standard Python: csv, io, collections și decimal. CSV-ul original, enunțul și evaluatorul nu sunt prezente în acest folder.

## Intrări și ieșiri

Intrare: `test-input.csv`, în directorul curent, UTF-8, separator `;`. Poate conține linii introductive înainte de antet. Coloanele folosite sunt `reading_id`, `station_name`, `temperature_raw`, `unit`, `reading_date`.

Ieșire: `test-output.csv`, UTF-8, separator virgulă, cu antetul `reading_id,station_name,temperature_c,reading_date`. Există un rând pentru fiecare ID cu cel puțin o observație acceptată, în ordine numerică. Temperatura este scrisă cu o zecimală, iar data este păstrată ca text.

## Algoritmul, pas cu pas

1. Citește întregul fișier și caută prima linie care, după strip și lower, începe cu reading_id. Dacă nu există, ridică ValueError.
2. Elimină preambulul și parsează restul prin DictReader cu separator punct și virgulă.
3. Ignoră rândurile fără ID întreg, fără nume de stație, fără dată sau fără temperatură parsabilă. Normalizează virgula zecimală la punct și unitatea la majuscule.
4. Încearcă repararea numelui prin `name.encode("latin-1").decode("utf-8")`. Dacă una dintre conversii eșuează, păstrează numele original.
5. Pentru unitatea F, calculează `(valoare − 32) × 5 / 9`; celelalte unități păstrează valoarea. Aplică `quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)` înainte de vot.
6. Grupează observațiile după ID și numără perechile `(temperatură rotunjită, dată)`. Alege perechea cu frecvența maximă; o egalitate favorizează prima pereche întâlnită. Nu este obligatorie o majoritate absolută.
7. Alege primul nume de stație asociat perechii câștigătoare și scrie rândurile în ordinea numerică a ID-urilor.

## Rulare

Din rădăcina repository-ului, după adăugarea CSV-ului în Island:

```bash
cd Island
python3 main.py
```

Căile sunt raportate la directorul curent. Rularea din rădăcină cu `python3 Island/main.py` ar căuta CSV-ul în rădăcină.

## Exemplu

```text
reading_id;station_name;temperature_raw;unit;reading_date
2;Akureyri;32;F;2026-01-02
1;Reykjavík;1,25;C;2026-01-01
1;Reykjavík;34.25;F;2026-01-01
```

Produce:

```csv
reading_id,station_name,temperature_c,reading_date
1,Reykjavík,1.3,2026-01-01
2,Akureyri,0.0,2026-01-02
```

Cele două observații ale ID-ului 1 ajung la aceeași temperatură înainte de vot. Numele stației nu face parte din cheia votului.

## Note, alegeri și limite

- Decimal evită conversia inițială în float. HALF_UP rotunjește egalitățile în sens opus lui zero: 1,25 → 1,3 și −1,25 → −1,3. Împărțirea la 9 folosește precizia contextului Decimal.
- Conversia numelor repară o singură interpretare Latin-1 greșită a octeților UTF-8. Nu este un detector general de codare și nu repară arbitrar coruperi repetate sau alte codări.
- Votul se face asupra perechii temperatură–dată, după conversie și rotunjire. Nu se votează independent fiecare coloană și nu se calculează media temperaturilor.
- Unitățile necunoscute sau goale sunt tratate de cod ca valori deja în Celsius. Datele nu sunt validate calendaristic. Documentarea păstrează acest comportament.
- Antetul este recunoscut tolerant, dar textul său nu este normalizat înainte de DictReader. Spațiile sau majusculele din numele coloanelor pot împiedica ulterior accesarea cheilor exacte.
- Decimal acceptă și valori speciale precum NaN și Infinity; codul nu verifică explicit finitudinea, iar unele valori pot provoca erori la quantize sau probleme la vot.
- Memoria este O(N): programul păstrează liniile, textul CSV, observațiile grupate și rezultatul. Costul obișnuit este O(N + G log G), unde G este numărul ID-urilor distincte.

## Ghid pentru întrebări despre o linie

Comentariile explicative sunt pe aceleași linii cu instrucțiunile, inclusiv continuările. Liniile goale și docstring-ul existent sunt păstrate, iar numerele de linie sunt neschimbate.

| Funcție | Linii | Rol |
| --- | --- | --- |
| fix_mojibake | 12–18 | Repararea limitată a numelor |
| find_header_index | 21–25 | Detectarea antetului după preambul |
| to_celsius | 28–31 | Conversia Fahrenheit–Celsius |
| main | 34–83 | Curățare, grupare, vot și scriere |

### Ce face linia 45?

`if not rid_raw:` verifică dacă ID-ul, după eliminarea spațiilor, este gol. Linia 46 ignoră rândul în acest caz. Verificarea că ID-ul este un întreg are loc separat, la liniile 47–50.

## Întrebări probabile și răspunsuri scurte

### De ce votăm după conversie și rotunjire?

Aceeași temperatură poate apărea în Celsius sau Fahrenheit și cu forme zecimale diferite. Normalizarea permite acestor observații să susțină aceeași pereche.

### Ce se întâmplă la egalitate?

Counter.most_common păstrează ordinea primei întâlniri pentru frecvențe egale. Apoi next alege primul nume de stație din observațiile perechii câștigătoare. Ordinea intrării poate influența astfel ieșirea.

### Este un vot majoritar al numelor de stații?

Nu. Numai temperatura și data participă la vot. Stația este luată din prima intrare care corespunde rezultatului.

### De ce folosim Decimal în loc de float?

Parsarea din text păstrează valorile zecimale fără reprezentarea binară intermediară. Regula explicită HALF_UP face rotunjirea reproductibilă pentru aceste valori.

## Rezultat și verificare

Codul original și varianta comentată au aceeași structură executabilă și același număr de linii. Verificarea funcțională folosește un CSV sintetic cu preambul, unități mixte, virgule zecimale, nume corupt, duplicate, egalități și rânduri invalide. Rezultatele challengeului și un eventual flag nu pot fi confirmate fără datele și evaluatorul originale.

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
