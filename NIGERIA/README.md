Raport Tehnic: NIGERIA — Gânganul nu minte niciodată
Analiza steganografică audio și extragerea flag-ului ascuns
Această documentație prezintă metodologia completă și etapele tehnice parcurse pentru rezolvarea sarcinii NIGERIA — Gânganul nu minte niciodată din cadrul Sigmoid Academy — Sarcini, utilizând fișierele puse la dispoziție în folderul Drive Nigeria.


1. Context și obiectiv
Punctul de pornire în investigație este fișierul audio challenge.wav, descris în mod înșelător în fundalul sarcinii ca fiind un simplu „ton de test — de ignorat". Obiectivul principal constă în identificarea tehnicii de steganografie aplicate, decodificarea mesajului ascuns și structurarea acestuia în formatul standard de flag: SIGMOID_<WORD>.

Proprietățile tehnice primare ale fișierului de analizat sunt:

Dimensiune fișier: 448.556 bytes
Format: WAV PCM (16-bit, Mono)
Rată de eșantionare: 22.050 Hz
Număr total eșantioane: 224.256
Durată audio: ~10,17 secunde


2. Metodologia de investigație
Analiza a urmat o abordare riguroasă în trei etape principale, trecând de la inspecția structurii primare de date la tehnici avansate de procesare a semnalelor audio.
Verificarea header-ului și a șirurilor ASCII
Prima etapă a constat în inspecția binară a fișierului pentru a determina dacă datele text sau metadatele au fost introduse direct în structura RIFF/WAVE.

S-a extras conținutul binar brut și s-a analizat zona de header și eventualele chunk-uri suplimentare de tip INFO sau LIST.
S-a executat o căutare de șiruri ASCII lizibile pe întregul fișier.
Rezultat: Nu s-au găsit cadre de text sau comentarii ascunse direct în metadatele WAV, confirmând că datele utile sunt codificate direct în semnalul audio.
Verificarea steganografiei LSB (Least Significant Bit)
O tehnică frecventă în domeniul audio este steganografia spațială LSB, unde bitul cel mai puțin semnificativ al fiecărui eșantion PCM poartă biții mesajului secret.

S-au extras biții LSB din eșantioanele pe 16 biți ale semnalului.
Testarea s-a efectuat atât în ordine little-endian, cât și big-endian, verificând toate cele 8 aliniamente (decalaje de biți).
Rezultat: Entropia biților extrași a fost uniformă, neidentificându-se nicio structură de text sau antet cunoscut. S-a exclus steganografia de tip LSB.
Analiza spectrală (STFT — Short-Time Fourier Transform)
Limbajul și contextul sarcinii sugerează că mesajul ar putea fi transmis vizual prin intermediul domeniului de frecvență (steganografie spectrală sau audio-to-image).

S-a aplicat Transformata Fourier de Durată Scurtă (STFT) asupra semnalului audio pentru a converti domeniul temporal în domeniu frecvență-timp.
Parametrii de procesare utilizați:
Biblioteca: scipy.signal.spectrogram
Dimensiunea ferestrei (nperseg): 1024
Suprapunerea ferestrelor (noverlap): 768
Scalarea amplitudinii: Logaritmică (dB), calculată prin formula 10 * log10(Sxx + 1e-12)
S-a generat reprezentarea grafică a spectrogramei pentru inspecție vizuală.


3. Descoperirea și rezultatul final
În urma generării spectrogramei pe scala de frecvențe 0 – 11.025 Hz, s-a observat o modulație intenționată a amplitudinii pe o bandă îngustă.

Identificare vizuală: În intervalul cuprins între 3000 Hz și 3600 Hz, întins pe întreaga durată a celor 10,17 secunde ale înregistrării, apare un text desenat clar prin variația de frecvență.
Text extras: TALKINGDRUM

Acest cuvânt reprezintă o referință directă la Gángan, toba tradițională vorbitoare din cultura Yoruba menționată în contextul sarcinii Nigeria.
Flag-ul final
Prin încadrarea cuvântului descoperit în formatul solicitat, se obține flag-ul valid:

SIGMOID_TALKINGDRUM


4. Tabel sumar al parametrilor și rezultatelor
Parametru / Etapă
Detalii / Valoare
Fișier analizat
challenge.wav (448.556 bytes)
Format Audio
WAV PCM, 16-bit, Mono
Rată eșantionare / Durată
22.050 Hz / ~10,17 secunde (224.256 eșantioane)
Tehnică identificată
Steganografie spectrală (Audio-to-Image / STFT)
Bandă de frecvență mesaj
~3000 Hz – 3600 Hz
Cuvânt cheie extras
TALKINGDRUM
Flag Final
SIGMOID_TALKINGDRUM


