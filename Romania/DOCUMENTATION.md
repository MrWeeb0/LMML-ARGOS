# Romania — documentație pentru prezentare

## Ce face programul

Clasifică înregistrări seismice printr-un detector cu trei rute. Separă un grup cu semnal radial, unul cu relație liniară și unul cu structură de paritate; trimite predicțiile finale evaluatorului challengeului.

## Fișiere și dependențe

`solve.py` — soluția finală; `baseline_solution.py` — comparație inițială; `evaluation_script.py` — evaluator cu comentarii adăugate, cu aceeași logică; `evaluation_script.original.txt` — octeții originali pentru verificarea hashului. Datele train/sealed/vault, requirements.txt și rezultatele de validare sunt prezente.

## Intrări și ieșiri

train.csv conține 48 de canale c01…c48 și ținta vrancea. sealed.csv conține aceleași canale și record_id. Evaluatorul cere câte o predicție 0/1 pentru fiecare ID sealed.

## Algoritmul, pas cu pas

1. Separă stratificat 75% pentru antrenare și 25% pentru validare, seed 42. Toate transformările detectorului se învață numai în partea de antrenare.
2. Standardizează cele 48 de canale și ajustează un GaussianMixture cu două componente și covarianțe diagonale. Componenta cu suma varianțelor mai mică definește ruta radială.
3. Pe ruta radială, selectează canalele cu varianță standardizată >0,5 și antrenează regresie logistică pe caracteristici polinomiale de gradul doi.
4. Pe restul datelor, un arbore explorator învață praguri pe c13; mediana lor definește poarta. Peste prag antrenează regresie logistică, iar sub prag un arbore de adâncime trei pe c35/c38/c43.
5. Evaluează detectorul pe holdout și salvează predicțiile și scorurile pe rute. Opțional, --compare rulează și modelele de referință.
6. Reantrenează pe toate datele etichetate, prezice sealed și salvează predictions.csv. Reîncarcă prin alinierea oficială a ID-urilor, cere flagul și oprește cu eroare dacă nu este acceptat.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
.venv/bin/python Romania/solve.py
# Comparațiile suplimentare sunt mai lente:
.venv/bin/python Romania/solve.py --compare
.venv/bin/python Romania/evaluation_script.py Romania/predictions.csv
```

## Rezultat și dovezi

Rezultatele existente raportează 94,83% pe holdout și acceptarea `SIGMOID_CONVOLUTION`. Evaluatorul folosește n=5000, k=4252 și cere acord pe cel puțin 4626 de puncte (92,52%). El dezvăluie flagul, fără acuratețea exactă pe sealed.

## Note, alegeri și limite

Rutarea selectează un model pentru fiecare rând, fără medierea probabilităților. Holdout-ul a fost folosit în dezvoltare, deci scorul nu este o estimare complet neatinsă. Evaluatorul operează cu polinoame modulo un număr prim, interpolează punctele selectate de predicții, aplică decodificare Gao și verifică o cheie SHA-256 înainte de decriptarea cuvântului. Vault este folosit pentru verificare, nu ca țintă de antrenare. Comentariile schimbă hashul fișierului evaluatorului, nu arborele său sintactic; copia originală păstrează hashul documentat anterior.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [baseline_solution.py](baseline_solution.py) | Flux executat la nivelul modulului, de sus în jos. |
| [evaluation_script.py](evaluation_script.py) | `_trim`: 24–26; `_divmod`: 29–40; `_mul`: 43–52; `_sub`: 55–59; `_interpolate`: 62–83; `_decode`: 86–106; `_evaluate`: 109–113; `_word`: 116–123; `flag_for`: 127–145; `load_predictions`: 148–160; `main`: 163–170 |
| [solve.py](solve.py) | `RoutedDetector`: 31–81; `main`: 84–141; `fit`: 32–69; `predict_with_routes`: 71–81 |


Exemplu pentru „ce face linia 45?” în `baseline_solution.py`:

Linia 45 este goală: separă blocurile și nu execută nicio operație.

## Întrebări probabile și răspunsuri scurte

### De ce trei modele?

Grupurile au relații diferite între canale și țintă; un singur clasificator global le reprezintă mai slab.

### Cum prevenim leakage în validare?

Scalerul, GMM, canalele, pragul și clasificatoarele sunt ajustate exclusiv pe subsetul de antrenare.

### Ce verifică evaluatorul?

Aliniază ID-urile, selectează valori din vault după predicții și încearcă recuperarea unui polinom cu suficient acord; cheia validă deblochează cuvântul.

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
