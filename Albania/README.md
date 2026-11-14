Detecție de Anomalii în Flux Streaming: Soluția detector.py
Documentație tehnică pentru taskul ALBANIA — Arată a anomalie! publicat pe Sigmoid Academy — Sarcini, bazată pe datele din folderul Drive Albania.
1. Context și Obiectiv
Sistemul implementat în detector.py este conceput pentru detecția în timp real (streaming) a anomaliilor dintr-un mediu industrial compartimentat în zone specifice de buncăr (bunker_zone). Procesul de achiziție al datelor monitorizează 6 senzori fizici:

temperature_c (temperatura exprimată în grade Celsius)
humidity_pct (umiditatea relativă procentuală)
vibration_g (nivelul de vibrații în unități g)
acoustic_db (nivelul de zgomot acustic în decibeli)
air_pressure_kpa (presiunea atmosferică locală în kPa)
co2_ppm (concentrația de dioxid de carbon în ppm)
Restricții de Operare
Regim Streaming Strict: Analiza se face pas cu pas (step-by-step). Algoritmul nu are acces la citirile viitoare și nu poate efectua treceri înapoi (look-ahead sau back-tracking).
Interfață: Clasa Detector primește câte un dicționar reading per pas prin apelarea metodei update(reading) și returnează un scor continuu în intervalul [0.0, 1.0].
Prag de Decizie: Un pas este clasificat ca anomalie dacă scorul returnat este mai mare sau egal cu 0.50.
Metrica de Evaluare și Pragul de Reușită
Performanța este evaluată folosind un scor agregat ponderat, definit prin relația:

Scor Evaluare = 100 × (0.80 × F1 + 0.05 × point_recall + 0.075 × drift_recall + 0.075 × collective_recall)Pentru ca soluția să fie validată, scorul obținut trebuie să atingă sau să depășească pragul minim de 70.00 / 100.
2. Analiza celor Trei Familii de Anomalii
Setul de date de antrenament (train-input.csv și train-output.csv) conține un număr total de 3.600 de citiri secvențiale. În urma analizei exploratory a datelor, au fost identificate trei tipologii distincte de manifestare a anomaliilor:
Anomalii Punctuale (point)
Frecvență: 7 evenimente izolate în tot setul de date.
Manifestare: Vârfuri extreme (spikes) de scurtă durată (1 pas), afectând de regulă un singur senzor per eveniment.
Amplitudine: Deviații masive față de comportamentul normal, variind între 15 și 26 de deviații standard.
Derive Graduale (drift)
Frecvență: 3 segmente distincte, fiecare având o durată continuă de 60 de pași.
Manifestare: Modificări lente și cumulative pe un singur senzor. Valoarea senzorului migrează progresiv de la nivelul bazal către valori anormale.
Amplitudine: Deviația crește treptat de la 0 la 5–8 deviații standard la punctul maxim al derivativei.
Anomalii Colective (collective)
Frecvență: 3 segmente distincte, având durate cuprinse între 30 și 35 de pași per segment.
Manifestare: Deviații moderate dar simultane pe mai mulți senzori (de exemplu, modificări concomitente pe vibration_g, acoustic_db și co2_ppm).
Amplitudine: Fiecare senzor individual prezintă deviații moderate (3.3–5.3 deviații standard), care privite separat ar putea fi considerate la granița normalității, însă devin evidente când sunt evaluate împreună.
3. Arhitectura Algoritmului din detector.py
Algoritmul combină estimarea robustă a statisticii de fond cu un mecanism de gating pentru prevenirea otrăvirii datelor și un modul combinat de scorare multi-familie.
Baseline Robust per Zonă (deque(maxlen=360) + Mediană / MAD)
Pentru a face față comportamentului diferit dintre diferitele zone ale buncărului (bunker_zone), detectorul menține structuri de date izolate per zonă:

Fereastră Alunecătoare: Fiecărei zone ii este asociat un buffer deque(maxlen=360) ce stochează doar ultimele 360 de citiri validate ca fiind normale.
Statistici Robuste: Centrul distribuției este estimat prin mediană, iar dispersia prin Deviația Mediană Absolută scalată (MAD × 1.4826). Aceasta este combinată convex cu deviația standard (0.75 × std) pentru a menține stabilitatea numerică.
Optimizare Computațională: Recalcularea statisticilor de fond pentru o zonă se efectuează la fiecare 10 pași noi procesați, asigurând o execuție extrem de rapidă.
Protecție Anti-Otrăvire a Baseline-ului (Gating Mechanism)
Cea mai critică componentă pentru tratarea derivatelor lente și a anomaliilor de durată este filtru de acces în baseline:

O citire curentă este adăugată în istoricul de stări normale al zonei doar dacă scorul ei final de anomalie calculat este sub pragul de siguranță: scor < 0.42.
Efect: Segmentele lungi de drift (60 pași) și cele colectiv (30–35 pași) nu pot altera media și deviația de referință. Astfel, baseline-ul rămâne „curat", prevenind adaptarea greșită a detectorului la valorile anomale prelungite.
Scorare Multi-Familie
Detectorul generează trei scoruri parțiale care reflectă direct cele trei tipuri de manifestare ale anomaliilor, selectând în final valoarea maximă: scor = max(s_point, s_coll, s_drift).
A. Scorul Punctual (s_point)
Răspunde rapid la vârfurile extreme izolate. Calculează deviația z-score maximă absolută dintre cei 6 senzori:

max_z = max(|x_i - med_i| / sd_i)
|---|
Dacă max_z >= 5.0, scorul atribuit depășește pragul de decizie (>= 0.50), atingând valoarea 1.0 la deviații majore.
B. Scorul Colectiv Instantaneu (s_coll)
Cuantifică deviația combinată pe toți senzorii folosind norma L2 a z-score-urilor trunchiate:

l2_z = sqrt(sum(min(z_i, 8.0)^2))Această abordare este sensibilă la perturbări moderate ce apar simultan pe mai multe canale paralele, unde z-score-urile individuale nu ar depăși pragul punctual de 5.0.
C. Scorul de Drift și Colectiv Peristent (s_drift)
Detectează modificările graduale prin urmărirea mediei z-score-urilor pe o fereastră scurtă temporală (ultimii 6 pași, recent_z).

Pentru a preveni fals alarmările și persistența scorului ridicat după ce procesul revine la starea normală, scorul de drift este activat doar dacă citirea curentă confirmă deviația (max_z >= 2.2 sau l2_z >= 3.3). În caz contrar, scorul scade rapid la zero.
Tratarea Sigură a Valorilor Lipsă (NaN / None)
Dacă în dicționarul de intrare reading sunt detectate valori lipsă (None sau np.nan), algoritmul le înlocuiește dinamic cu mediana calculată pe istoricul zonei respective la pasul curent, împiedicând propagarea erorilor numerice în calculul z-score-urilor.
4. Rezultate Validate pe Setul de Antrenament
Performanța algoritmului din detector.py a fost evaluată riguros pe întregul set de antrenament format din 3.600 de citiri consecutive.
Tabel Sumar al Performanței
Metrică / Indicator
Valoare Obținută
Prag Minim / Limită
Stare
Scor Final Evaluare
95.35 / 100
>= 70.00
Admis
Scor F1 Global
0.9459
-
Evaluat (Pondere 80%)
Precizie (Precision)
0.9180
-
280 TP / 25 FP
Sensibilitate Globală (Recall)
0.9756
-
280 TP / 7 FN
Recall Anomalii Punctuale
1.0000
-
7 / 7 detecții (Pondere 5%)
Recall Derive Graduale
0.9667
-
174 / 180 detecții (Pondere 7.5%)
Recall Anomalii Colective
0.9900
-
99 / 100 detecții (Pondere 7.5%)
Timp Total de Execuție
0.177 secunde
< 60.00 secunde
Optim

Concluzii și Observații
Soluția acoperă complet cerințele din specisificație. Prin utilizarea statisticii robuste (Mediană/MAD) izolată per zonă și a filtrului de protecție la actualizarea baseline-ului, modelul reușește să mențină un nivel minim de alarme false (doar 25 FP la 3.600 de pași), înregistrând în același timp un recall aproape perfect pe toate categoriile de anomalii. Timpul de rulare de sub 0.2 secunde confirmă eficiența pentru medii de producție în regim streaming.
