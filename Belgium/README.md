Raport de Rezolvare: BELGIA — Fry-ndship
Analiza Geometrică și Decodificarea Reziduurilor în Setul de Date al Parcelelor de Cartofi
Acest document prezintă analiza detaliată a setului de date potato_fields.csv aferent taskului BELGIA — Fry-ndship disponibil pe Sigmoid Academy — Sarcini (cu fișierele stocate în folderul Drive Belgia).

Obiectivul principal constă în modelarea lungimii marginii (edge_m) pentru 3.869 de parcele de cartofi din regiunea Flandra și identificarea cuvântului ascuns sub formă de flag (SIGMOID_<WORD>), observat inițial de topografa Mariette în structura măsurătorilor.
1. Context și Obiectiv
Analiza se bazează pe setul de date potato_fields.csv, care conține înregistrări geografice, geometrice și administrative pentru 3.869 de parcele agricole. În cadrul fluxului operational al cooperativei, fermierii furnizează o serie de dimensiuni estimate ale terenurilor, urmând ca echipa de teren (reprezentată de topografa Mariette) să efectueze măsurători detaliate.

Obiectivul tehnic este dublu:

Construirea unui model predictiv precis pentru determinarea lungimii marginii parcelei (edge_m) folosind doar informațiile disponibile pre-măsurătoare.
Analiza distribuției erorilor (reziduurilor) modelului OLS (Ordinary Least Squares) pentru a extrage mesajul vizual criptat în date.
2. Selecția Caracteristicilor și Prevenirea Data Leakage
Pentru a asigura o evaluare riguroasă și realistă din punct de vedere operațional, datele din fișierul de intrare au fost clasificate riguros după sursă și momentul colectării.
Clasificarea Coloanelor după Sursă
Declarația Fermierului (Pre-măsurătoare): crop_code, crop, farm_type, lat, lon, area_ha, long_side_m, ditch_m.
Notat/Măsurat la fața locului (Mariette): hedge_m, edge_m.
Antreprenor (Post-măsurători): fence_quote_eur.
Prevenirea Scurgerii de Date (Data Leakage)
Exact ca în scenariul operațional al cooperativei, modelul trebuie să funcționeze exclusiv pe baza datelor declarate inițial de fermieri. Variabilele hedge_m (lungimea gardului viu) și fence_quote_eur (oferta de preț a antreprenorului) sunt generate ulterior măsurătorilor de teren. Includerea lor în etapa de antrenare ar reprezenta un caz clasic de scurgere de date (data leakage), alterând capacitatea de generalizare și mascând semnalul real din reziduuri.
Ingineria Caracteristicilor (Feature Engineering)
Pornind de la suprafața declarată în hectare (area_ha) și de la lungimea laturii lungi (long_side_m), s-a calculat geometric latura scurtă a parcelei exprimată în metri (short_side_m):

short_side_m = (area_ha * 10000) / long_side_mAstfel, setul final de caracteristici utilizat pentru modelare este format din: long_side_m, short_side_m și ditch_m.
3. Modelarea prin Regresie Liniară (OLS) și Analiza Reziduurilor
S-a ajustat un model de regresie liniară (Ordinary Least Squares) pentru a prezice edge_m pe baza variabilelor predictive selectate.
Performanța Modelului și Coeficienții
Modelul a obținut o potrivire aproape perfectă, indicând o relație fizică/matematică directă între dimensiunile parcelei și lungimea marginii:

Coeficient de determinare (R²): 0.999984
Root Mean Squared Error (RMSE): 0.9570 m

Variabilă (Predictor)
Coeficient OLS
Valoare Aproximată
Intercept
-0.001098
≈ 0.0
long_side_m
0.900019
≈ 0.9
short_side_m
0.900023
≈ 0.9
ditch_m
0.999980
≈ 1.0


Ecuația de regresie rezultată sugerează că lungimea marginii este o combinație liniară a perimetrului util și a șanțurilor de drenaj.
Analiza Vizuală a Reziduurilor
Calculând diferența dintre valorile reale și cele prezise de model:

reziduu = edge_m - edge_m_prezisGraficul de dispersie (scatterplot) al reziduurilor în funcție de valorile prezise (edge_m_prezis) elimină componenta principală a datelor și aduce în evidență zgomotul structurat introdus intenționat în setul de date. Punctele din grafic conturează clar cuvântul: SUPERVISION.
4. Capcana de Data Leakage (hedge_m)
Pentru a valida ipoteza scurgerii de date, s-a efectuat un experiment secundar în care s-a inclus și variabila hedge_m (măsurată la fața locului de Mariette) în matricea de caracteristici.

Rezultate metrice: Se obține un scor aparent superior, cu R² = 1.000000 și RMSE = 0.0575 m.
Efectul asupra reziduurilor: Plotarea reziduurilor acestui model supradimensionat relevă cuvântul-capcană PREDICTION.

Această diferență demonstrează un principiu esențial în știința datelor: optimizarea orb a metricilor prin utilizarea variabilelor contaminate/post-eveniment duce la concluzii eronate (un "fals flag") și anulează descoperirea modelului real subiacent.
5. Rezumat și Concluzii
Scenariu Model
Variabile Utilizate
Scor R²
RMSE (m)
Cuvânt Vizualizat în Reziduuri
Model Corect (Fără Leakage)
long_side_m, short_side_m, ditch_m
0.999984
0.9570
SUPERVISION
Model Capcană (Cu Data Leakage)
long_side_m, short_side_m, ditch_m, hedge_m
1.000000
0.0575
PREDICTION

Rezultat Final
Flag valid: SIGMOID_SUPERVISION
Fișiere generate pentru justificare:
Scriptul de analiză: solve_belgia.py
Vizualizarea grafică a reziduurilor: belgia_residuals.png

