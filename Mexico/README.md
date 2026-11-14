MEXIC — Ruta de las Identidades

Soluție pentru sarcina Ruta de las Identidades de pe Sigmoid Academy, care identifică toate perechile de înregistrări ce aparțin aceleiași persoane în bazele de date regionale ale programului Ruta de Lectura.

Descrierea problemei

Datele de intrare (train-input.csv) conțin înregistrări din trei tabele sursă (a, b, c) cu coloanele:

source_table

record_id

first_name

last_name

address

Același cititor poate apărea în mai multe tabele cu variații de formatare:

Nume: inversare first_name ↔ last_name, inițiale (N. vs. Nadia), porecle (Pepe vs. José), lipsă de diacritice și erori de tastare.

Adrese: ordine diferită a numărului stradal, punctuație, lipsă de diacritice și abrevieri stradale (C. vs. Calle, Av. vs. Avenida, C.jón vs. Callejón, Int. vs. Interior, Edif. vs. Edificio, Depto. vs. Departamento, Ret. vs. Retorno etc.).

Cum funcționează soluția (main.py)

Normalizarea canonică a adresei (normalise_address):

Elimină diacriticele (NFKD), punctele și semnele de punctuație.

Expandează 21 de abrevieri poștale mexicane la forma lor completă (c → calle, av → avenida, blvd → boulevard, cjon → callejon, int → interior, edif → edificio, depto → departamento etc.).

Sortează alfabetic tokenii rezultați într-un tuplu canonic, devenind invariantă la ordinea cuvintelor.

Cheia numerică și compatibilitatea numelor (address_numbers + names_compatible):

Extrage și sortează numerele din adresă (număr stradă, bloc, apartament, cod poștal) și verifică compatibilitatea numelor pentru a acoperi eventuale abrevieri neobișnuite.

Închiderea tranzitivă (componente conexe):

Construiește graful de potriviri și generează toate perechile unice din fiecare componentă conexă (de exemplu, pentru 3 înregistrări ale aceleiași persoane: [a, b], [a, c], [b, c]).

Utilizare

python3 main.py input.csv output.json


Scriptul suportă și flag-uri explicite (-i / --input, -o / --output), variabile de mediu (INPUT_CSV, OUTPUT_JSON) sau citire din stdin.

Formatul fișierului JSON generat:

{"matches": [["a0002", "c0002"], ["a0003", "b0002"]]}


Validare

Testat pe setul public de antrenament (train-input.csv — 19.520 de înregistrări):

Perechi identificate: 12.038 / 12.038

Fals pozitive (FP): 0

Fals negative (FN): 0

Acuratețe: 100% (potrivire exactă)
