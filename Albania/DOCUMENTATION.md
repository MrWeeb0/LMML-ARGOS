# Albania — documentație pentru prezentare

## Ce face programul

Detector streaming de anomalii pentru șase senzori industriali. Fiecare citire este comparată cu istoricul propriei zone, iar `Detector.update(reading)` returnează un scor între 0 și 1. Pragul de clasificare al challengeului este 0,50; funcția returnează scorul, nu o etichetă.

## Fișiere și dependențe

`detector.py` — clasa trimisă evaluatorului. Nu sunt prezente aici CSV-urile de antrenare sau evaluatorul extern. Dependență: NumPy.

## Intrări și ieșiri

Dicționar cu `bunker_zone` și `temperature_c`, `humidity_pct`, `vibration_g`, `acoustic_db`, `air_pressure_kpa`, `co2_ppm`. Zona absentă devine `default`. Valorile lipsă sunt înlocuite cu mediana memorată sau cu zero înainte de existența statisticilor.

## Algoritmul, pas cu pas

1. Inițializează pentru fiecare zonă o coadă de maximum 360 de citiri normale și una cu ultimele șase vectori de deviații.
2. Primele 20 de citiri ale unei zone intră în istoric și primesc scor zero; aceasta este perioada de încălzire.
3. Calculează mediana și scara `max(1,4826 × MAD, 0,75 × std, 0,0001)`. Recalculează la prima utilizare și când contorul zonei este multiplu de zece.
4. Calculează deviațiile absolute standardizate. Scorul punctual folosește maximul lor; cel colectiv folosește norma L2, cu fiecare deviație limitată la 8.
5. Calculează scorul de persistență din media ultimelor șase vectori de deviații absolute, numai dacă citirea curentă confirmă abaterea: maxim ≥ 2,2 sau normă L2 ≥ 3,3.
6. Returnează maximul celor trei scoruri, trunchiat la [0, 1]. Adaugă citirea în istoricul normal numai dacă scorul este sub 0,42.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```python
from Albania.detector import Detector

detector = Detector()
score = detector.update({"bunker_zone": "A", "temperature_c": 22.0,
    "humidity_pct": 45.0, "vibration_g": 0.1, "acoustic_db": 40.0,
    "air_pressure_kpa": 101.3, "co2_ppm": 450.0})
print(score)  # 0.0 în perioada de încălzire
```

## Rezultat și dovezi

README-ul existent raportează 95,35/100 și F1 = 0,9459 pe datele originale. Aceste valori sunt rezultate istorice, nereproduse aici deoarece datele și evaluatorul lipsesc.

## Note, alegeri și limite

Scara este maximul a trei estimatori, nu o medie ponderată. `recent_z` conține valori absolute, deci persistența nu ține cont de semnul derivei. Încălzirea poate absorbi anomalii timpurii; înlocuirea cu zero poate influența referința inițială. Cu fereastra fixă, memoria este proporțională cu numărul de zone, iar costul pe citire rămâne mărginit pentru o zonă.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [detector.py](detector.py) | `Detector`: 20–89; `__init__`: 21–25; `_get_stats`: 27–33; `update`: 35–89 |


Exemplu pentru „ce face linia 45?” în `detector.py`:

Linia 45 este goală: separă blocurile și nu execută nicio operație.

## Întrebări probabile și răspunsuri scurte

### De ce mediană și MAD?

Sunt mai puțin sensibile la valori extreme decât media și deviația standard; maximul cu 0,75 × std stabilizează scara.

### De ce două praguri, 0,42 și 0,50?

0,50 decide anomalia în evaluare; 0,42 este o regulă mai strictă pentru acceptarea în istoricul normal și protejează referința.

### Folosește valori din viitor?

Nu. Fiecare scor folosește citirea curentă și starea acumulată până la ea.

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
