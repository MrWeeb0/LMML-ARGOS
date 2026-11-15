# UK — documentație pentru prezentare

## Ce face programul

Compară câștigătorii după BLEU cu cei aleși printr-un scor euristic de onestitate. Penalizează repetițiile, trigramele fără sprijin în referințe și omiterea atributelor consensuale, apoi decodează locurile câștigătoare în litere.

## Fișiere și dependențe

`solve_uk.py` și README.md sunt prezente. Lipsesc bleu.py/uk_bleu.py și dataset/references.csv, dataset/panel.csv. Există și o cale alternativă hardcodata din mediul inițial /working_dir/.../downloads. Dependențe: NumPy, pandas, Matplotlib și implementarea BLEU originală.

## Intrări și ieșiri

Referințe cu round, card, reference; răspunsuri cu round, seat, card, text. Codul se bazează pe locurile 1, 2, 3 și grupează câte trei runde pentru fiecare literă.

## Algoritmul, pas cu pas

1. Încarcă tokenizerul și corpus_bleu din modulul original; grupează referințele pe rundă/cartonaș.
2. Construiește frecvențele trigramelor din toate referințele, incluzând marcatori de început și sfârșit.
3. Pentru fiecare participant din fiecare rundă calculează BLEU pe pachetul său de texte.
4. Normalizează sinonimele și atributele. Pentru fiecare cartonaș, consensul include tokenuri apărute în minimum trei referințe și care nu sunt stopwords; măsoară acoperirea lor.
5. Calculează proporția trigramelor nevăzute și excesul de 4-grame repetate. Agregă cele mai slabe opt acoperiri și cele mai mari opt rate de trigrame nevăzute.
6. Scorul este bot8_cov − 0,35 × top8_u3 − 0,05 × max(0, rep4_sum−2). Alege maximul pe rundă, ordonează rundele și decodează câte trei locuri în baza trei; desenează comparația scorurilor.

## Rulare

Comenzile pornesc din rădăcina repository-ului, exceptând schimbările de director explicite. Mediul `.venv` trebuie să conțină dependențele proiectului.

```bash
.venv/bin/python UK/solve_uk.py
```

## Rezultat și dovezi

Afișează separat `BLEU word`, `Honest word`, lista locurilor oneste și salvează `honesty_separation.png`. Fără fișierele lipsă nu se poate reproduce sau confirma cuvântul final.

## Note, alegeri și limite

Pentru locuri s1,s2,s3, cifrele sunt d=s−1, iar litera are codul A + 9d1 + 3d2 + d3. Numărul rundelor trebuie să fie multiplu de trei; combinația 333 produce caracterul de după Z dacă apare. Scorul de onestitate este o euristică cu ponderi fixe, nu un clasificator antrenat. Trigramele sunt numărate global din referințe, consensul semantic local pe cartonaș. Normalizarea pe mulțimi pierde ordinea și poate pierde negații; nu dovedește corectitudine semantică generală.

## Ghid pentru întrebări despre o linie

Comentariile sunt pe aceeași linie cu instrucțiunile, inclusiv liniile de continuare. Numerele de linii Python au fost păstrate. Liniile goale separă blocuri; comentariile și docstring-urile existente sunt deja text explicativ și nu execută algoritmul. Pentru o întrebare, identifică **fișierul**, citește comentariul și explică intrarea, transformarea, ieșirea și motivul folosirii operației.

| Fișier | Puncte de orientare |
| --- | --- |
| [solve_uk.py](solve_uk.py) | `norm_sem`: 62–77; `decode`: 80–85; `main`: 88–169 |


Exemplu pentru „ce face linia 45?” în `solve_uk.py`:

```python
"excellent": "HIGH", "great": "HIGH", "5": "HIGH", "five": "HIGH", "top": "HIGH",  # Configurează echivalențele semantice pentru tokenurile din această linie.
```

## Întrebări probabile și răspunsuri scurte

### De ce BLEU singur poate induce în eroare?

Suprapunerea de n-grame și lungimea pot favoriza texte repetitive sau texte care omit informații dificile.

### De ce cele mai slabe opt acoperiri?

Scorul urmărește omisiunile concentrate pe o parte a cartonașelor, care pot fi mascate de o medie globală bună.

### Cum se obține o literă din trei runde?

Locurile 1…3 devin cifrele 0…2; 9d1+3d2+d3 este indicele literei pornind de la A.

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
