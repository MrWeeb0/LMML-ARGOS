import csv  # Importă citirea și scrierea tabelelor CSV.
import io  # Importă fluxurile text în memorie, folosite pentru eliminarea preambulului.
from collections import Counter  # Importă contorul frecvențelor pentru votul duplicatelor.
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP  # Importă aritmetica zecimală, excepția de parsare și regula de rotunjire.

INPUT_FILE = "test-input.csv"  # Caută intrarea în directorul curent, nu relativ la script.
OUTPUT_FILE = "test-output.csv"  # Scrie rezultatul curățat în directorul curent.

ONE_DECIMAL = Decimal("0.1")  # Definește precizia finală de o zecimală.


def fix_mojibake(name):  # Încearcă repararea unei singure decodări Latin-1 greșite a unui nume UTF-8.
    """Reverse a single Latin-1 mis-decode of UTF-8 bytes, if there was one."""
    try:  # Încearcă recodarea; numele corecte sau incompatibile trebuie păstrate.
        fixed = name.encode("latin-1").decode("utf-8")  # Recuperează octeții Latin-1 și îi interpretează din nou ca UTF-8.
    except (UnicodeEncodeError, UnicodeDecodeError):  # Tratează atât imposibilitatea codării Latin-1, cât și octeții UTF-8 invalizi.
        return name  # Păstrează numele original dacă repararea nu poate fi aplicată.
    return fixed  # Întoarce numele recodat când conversia a reușit.


def find_header_index(lines):  # Localizează antetul CSV după eventualele linii introductive.
    for i, line in enumerate(lines):  # Parcurge liniile împreună cu indicii lor, începând de la zero.
        if line.strip().lower().startswith("reading_id"):  # Recunoaște antetul după prefixul reading_id, ignorând spațiile marginale și majusculele.
            return i  # Întoarce indicele primei linii care seamănă cu antetul.
    raise ValueError("header row (starting with 'reading_id') not found")  # Oprește execuția dacă nu a fost găsit antetul așteptat.


def to_celsius(value, unit):  # Convertește temperatura din Fahrenheit în Celsius când unitatea este F.
    if unit == "F":  # Aplică formula Fahrenheit numai pentru unitatea F.
        return (value - Decimal(32)) * Decimal(5) / Decimal(9)  # Calculează (F − 32) × 5 / 9 folosind Decimal.
    return value  # Pentru orice altă unitate, păstrează valoarea fără conversie.


def main():  # Execută citirea, curățarea, votul pe ID și scrierea rezultatului.
    with open(INPUT_FILE, "r", encoding="utf-8", newline="") as f:  # Deschide intrarea UTF-8 și lasă modulul CSV să gestioneze sfârșiturile de linie.
        lines = f.readlines()  # Încarcă toate liniile pentru a putea căuta antetul după preambul.

    header_idx = find_header_index(lines)  # Găsește poziția antetului în fișier.
    data_text = "".join(lines[header_idx:])  # Elimină preambulul și reunește textul începând cu antetul.
    reader = csv.DictReader(io.StringIO(data_text), delimiter=";")  # Citește rânduri ca dicționare din textul în memorie, cu separator punct și virgulă.

    groups = {}  # Grupează după reading_id liste de tupluri (stație, temperatură Celsius, dată).
    for row in reader:  # Procesează fiecare rând de date după antet.
        rid_raw = (row.get("reading_id") or "").strip()  # Extrage ID-ul ca text curățat; absența sau None devin șir gol.
        if not rid_raw:  # Verifică dacă ID-ul lipsește după eliminarea spațiilor.
            continue  # Ignoră rândul fără ID și trece la următorul.
        try:  # Încearcă interpretarea ID-ului ca întreg.
            rid = int(rid_raw)  # Convertește ID-ul pentru grupare și sortare numerică.
        except ValueError:  # Tratează ID-urile care nu pot fi convertite la întreg.
            continue  # Ignoră rândul cu ID invalid.

        station_raw = (row.get("station_name") or "").strip()  # Extrage numele stației și elimină spațiile marginale.
        unit = (row.get("unit") or "").strip().upper()  # Normalizează unitatea la majuscule; o valoare absentă devine șir gol.
        date = (row.get("reading_date") or "").strip()  # Extrage data ca text; nu validează formatul sau calendarul.
        temp_raw = (row.get("temperature_raw") or "").strip().replace(",", ".")  # Elimină spațiile marginale și înlocuiește virgula zecimală cu punct.

        if not station_raw or not date or not temp_raw:  # Cere numele stației, data și temperatura ca texte nevidate.
            continue  # Ignoră rândurile cu oricare dintre cele trei câmpuri obligatorii lipsă.
        try:  # Încearcă parsarea temperaturii în aritmetică zecimală.
            temp = Decimal(temp_raw)  # Construiește valoarea Decimal direct din text, fără conversie intermediară la float.
        except InvalidOperation:  # Tratează textele care nu reprezintă o valoare Decimal acceptată.
            continue  # Ignoră temperatura care nu poate fi parsată.

        station = fix_mojibake(station_raw)  # Aplică repararea limitată a codării numelui stației.
        temp_c = to_celsius(temp, unit).quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)  # Convertește la Celsius și rotunjește la o zecimală; egalitățile se îndepărtează de zero.

        groups.setdefault(rid, []).append((station, temp_c, date))  # Creează lista ID-ului dacă lipsește și adaugă observația normalizată.

    out_rows = []  # Pregătește lista rândurilor finale, câte unul pentru fiecare ID.
    for rid in sorted(groups):  # Parcurge ID-urile în ordine numerică crescătoare.
        entries = groups[rid]  # Recuperează toate observațiile acceptate pentru ID-ul curent.
        vote = Counter((temp_c, date) for _, temp_c, date in entries)  # Numără perechile (temperatură rotunjită, dată); numele stației nu participă la vot.
        (best_temp_c, best_date), _ = vote.most_common(1)[0]  # Alege perechea cea mai frecventă; la egalitate câștigă prima întâlnită.
        station = next(  # Caută primul nume de stație asociat perechii câștigătoare.
            s for s, t, d in entries if t == best_temp_c and d == best_date  # Păstrează numai intrările cu temperatura și data alese prin vot.
        )  # Încheie căutarea next; există cel puțin o intrare pentru perechea câștigătoare.
        out_rows.append((rid, station, best_temp_c, best_date))  # Adaugă un singur rând final pentru acest ID.

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:  # Deschide ieșirea UTF-8 în modul scriere, înlocuind conținutul anterior.
        writer = csv.writer(f, lineterminator="\n")  # Creează scriitorul CSV cu separator implicit virgulă și terminator LF.
        writer.writerow(["reading_id", "station_name", "temperature_c", "reading_date"])  # Scrie antetul celor patru coloane ale rezultatului.
        for rid, station, temp_c, date in out_rows:  # Parcurge rândurile finale în ordinea numerică a ID-urilor.
            writer.writerow([rid, station, str(temp_c), date])  # Scrie ID-ul, stația, temperatura zecimală ca text și data.


if __name__ == "__main__":  # Rulează fluxul principal numai când fișierul este executat direct.
    main()  # Pornește procesarea completă.
