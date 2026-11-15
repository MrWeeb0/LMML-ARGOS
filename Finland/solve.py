import csv  # Importă csv
import re  # Importă re
import unicodedata  # Importă unicodedata
from collections import Counter, defaultdict  # Importă Counter, defaultdict din collections
from pathlib import Path  # Importă Path din pathlib


DATA_FILE = Path(__file__).with_name("routes.csv")  # Stabilește DATA_FILE: calea routes.csv de lângă script.


ALIASES = {  # Stabilește ALIASES: corespondențele dintre variante suedeze/alternative și numele finlandeze.
    "Alavo": "Alavus",  # Asociază varianta de nume cu numele canonic finlandez.
    "Björneborg": "Pori",  # Asociază varianta de nume cu numele canonic finlandez.
    "Borga": "Porvoo",  # Asociază varianta de nume cu numele canonic finlandez.
    "Borgå": "Porvoo",  # Asociază varianta de nume cu numele canonic finlandez.
    "Brahestad": "Raahe",  # Asociază varianta de nume cu numele canonic finlandez.
    "Esbo": "Espoo",  # Asociază varianta de nume cu numele canonic finlandez.
    "Grankulla": "Kauniainen",  # Asociază varianta de nume cu numele canonic finlandez.
    "Fredrikshamn": "Hamina",  # Asociază varianta de nume cu numele canonic finlandez.
    "Hango": "Hanko",  # Asociază varianta de nume cu numele canonic finlandez.
    "Hangö": "Hanko",  # Asociază varianta de nume cu numele canonic finlandez.
    "Helsingfors": "Helsinki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Hyvinge": "Hyvinkää",  # Asociază varianta de nume cu numele canonic finlandez.
    "Hyvinkaa": "Hyvinkää",  # Asociază varianta de nume cu numele canonic finlandez.
    "Hameenlinna": "Hämeenlinna",  # Asociază varianta de nume cu numele canonic finlandez.
    "Tavastehus": "Hämeenlinna",  # Asociază varianta de nume cu numele canonic finlandez.
    "Idensalmi": "Iisalmi",  # Asociază varianta de nume cu numele canonic finlandez.
    "Ikalis": "Ikaalinen",  # Asociază varianta de nume cu numele canonic finlandez.
    "Ilmola": "Ilmajoki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Ingå": "Inkoo",  # Asociază varianta de nume cu numele canonic finlandez.
    "Jakobstad": "Pietarsaari",  # Asociază varianta de nume cu numele canonic finlandez.
    "Jyvaskyla": "Jyväskylä",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kajana": "Kajaani",  # Asociază varianta de nume cu numele canonic finlandez.
    "Karleby": "Kokkola",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kaskö": "Kaskinen",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kemijarvi": "Kemijärvi",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kemionsaari": "Kemiönsaari",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kimitoön": "Kemiönsaari",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kimitoon": "Kemiönsaari",  # Asociază varianta de nume cu numele canonic finlandez.
    "Keuru": "Keuruu",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kyrkslätt": "Kirkkonummi",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kyrkslatt": "Kirkkonummi",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kumo": "Kokemäki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kristinestad": "Kristiinankaupunki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kronoby": "Kruunupyy",  # Asociază varianta de nume cu numele canonic finlandez.
    "Lahtis": "Lahti",  # Asociază varianta de nume cu numele canonic finlandez.
    "Villmanstrand": "Lappeenranta",  # Asociază varianta de nume cu numele canonic finlandez.
    "Lappo": "Lapua",  # Asociază varianta de nume cu numele canonic finlandez.
    "Larsmo": "Luoto",  # Asociază varianta de nume cu numele canonic finlandez.
    "Lempaala": "Lempäälä",  # Asociază varianta de nume cu numele canonic finlandez.
    "Leppavirta": "Leppävirta",  # Asociază varianta de nume cu numele canonic finlandez.
    "Lojo": "Lohja",  # Asociază varianta de nume cu numele canonic finlandez.
    "Lovisa": "Loviisa",  # Asociază varianta de nume cu numele canonic finlandez.
    "Malax": "Maalahti",  # Asociază varianta de nume cu numele canonic finlandez.
    "Mantsala": "Mäntsälä",  # Asociază varianta de nume cu numele canonic finlandez.
    "S:t Michel": "Mikkeli",  # Asociază varianta de nume cu numele canonic finlandez.
    "Narpes": "Närpiö",  # Asociază varianta de nume cu numele canonic finlandez.
    "Närpes": "Närpiö",  # Asociază varianta de nume cu numele canonic finlandez.
    "Narpio": "Närpiö",  # Asociază varianta de nume cu numele canonic finlandez.
    "Nådendal": "Naantali",  # Asociază varianta de nume cu numele canonic finlandez.
    "Nurmijarvi": "Nurmijärvi",  # Asociază varianta de nume cu numele canonic finlandez.
    "Nystad": "Uusikaupunki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Uleåborg": "Oulu",  # Asociază varianta de nume cu numele canonic finlandez.
    "Pargas": "Parainen",  # Asociază varianta de nume cu numele canonic finlandez.
    "Pieksamaki": "Pieksämäki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Raseborg": "Raasepori",  # Asociază varianta de nume cu numele canonic finlandez.
    "Reso": "Raisio",  # Asociază varianta de nume cu numele canonic finlandez.
    "Raumo": "Rauma",  # Asociază varianta de nume cu numele canonic finlandez.
    "Seinajoki": "Seinäjoki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Sibbo": "Sipoo",  # Asociază varianta de nume cu numele canonic finlandez.
    "Sjundea": "Siuntio",  # Asociază varianta de nume cu numele canonic finlandez.
    "Sjundeå": "Siuntio",  # Asociază varianta de nume cu numele canonic finlandez.
    "S:t Karins": "Kaarina",  # Asociază varianta de nume cu numele canonic finlandez.
    "Tammerfors": "Tampere",  # Asociază varianta de nume cu numele canonic finlandez.
    "Tornea": "Tornio",  # Asociază varianta de nume cu numele canonic finlandez.
    "Torneå": "Tornio",  # Asociază varianta de nume cu numele canonic finlandez.
    "Tusby": "Tuusula",  # Asociază varianta de nume cu numele canonic finlandez.
    "Ulvsby": "Ulvila",  # Asociază varianta de nume cu numele canonic finlandez.
    "Nykarleby": "Uusikaarlepyy",  # Asociază varianta de nume cu numele canonic finlandez.
    "Vasa": "Vaasa",  # Asociază varianta de nume cu numele canonic finlandez.
    "Vanda": "Vantaa",  # Asociază varianta de nume cu numele canonic finlandez.
    "Vichtis": "Vihti",  # Asociază varianta de nume cu numele canonic finlandez.
    "Virmo": "Mynämäki",  # Asociază varianta de nume cu numele canonic finlandez.
    "Voyri": "Vöyri",  # Asociază varianta de nume cu numele canonic finlandez.
    "Vörå": "Vöyri",  # Asociază varianta de nume cu numele canonic finlandez.
    "Ylojarvi": "Ylöjärvi",  # Asociază varianta de nume cu numele canonic finlandez.
    "Åbo": "Turku",  # Asociază varianta de nume cu numele canonic finlandez.
    "Abo": "Turku",  # Asociază varianta de nume cu numele canonic finlandez.
    "Birkala": "Pirkkala",  # Asociază varianta de nume cu numele canonic finlandez.
    "Korsholm": "Mustasaari",  # Asociază varianta de nume cu numele canonic finlandez.
    "Kervo": "Kerava",  # Asociază varianta de nume cu numele canonic finlandez.
    "Lundo": "Lieto",  # Asociază varianta de nume cu numele canonic finlandez.
    "Traskanda": "Järvenpää",  # Asociază varianta de nume cu numele canonic finlandez.
    "Hogfors": "Karkkila",  # Asociază varianta de nume cu numele canonic finlandez.
    "Högfors": "Karkkila",  # Asociază varianta de nume cu numele canonic finlandez.
}  # Închide dicționarul sau mulțimea.


def lookup_key(value):  # Uniformizează cheia de căutare eliminând puncte/spații și diferențe de majuscule.
    return re.sub(r"[. ]", "", value).casefold()  # Întoarce re.sub('[. ]', '', value).casefold().


def remove_accents(value):  # Elimină semnele diacritice prin descompunere Unicode.
    return "".join(  # Întoarce ''.join((char for char in unicodedata.normalize('NFKD', value) if not unicodedata.combining(char))).
        char  # Păstrează caracterul de bază în textul fără diacritice.
        for char in unicodedata.normalize("NFKD", value)  # Clauză de comprehensiune: for char in unicodedata.normalize("NFKD", value).
        if not unicodedata.combining(char)  # Filtrează elementele comprehensiunii după condiția indicată.
    )  # Închide apelul sau gruparea.


def canonical_names(rows):  # Unește aliasurile orașelor și alege nume canonice.
    raw_names = {  # Stabilește raw_names: toate numele întâlnite la ambele capete ale rutelor.
        row[column]  # Extrage numele orașului din coloana capătului curent al rutei.
        for row in rows  # Clauză de comprehensiune: for row in rows.
        for column in ("from_town", "to_town")  # Clauză de comprehensiune: for column in ("from_town", "to_town").
    }  # Închide dicționarul sau mulțimea.
    alias_lookup = {lookup_key(name): town for name, town in ALIASES.items()}  # Stabilește alias_lookup: dicționarul de aliasuri cu chei normalizate.
    preliminary = {  # Stabilește preliminary: numele după aplicarea aliasurilor și curățarea punctuației finale.
        name: alias_lookup.get(lookup_key(name), name.strip().rstrip("."))  # Aplică aliasul dacă există; altfel elimină spațiile marginale și punctele finale.
        for name in raw_names  # Clauză de comprehensiune: for name in raw_names.
    }  # Închide dicționarul sau mulțimea.

    clusters = defaultdict(list)  # Stabilește clusters: grupurile de nume echivalente fără accente.
    for town in preliminary.values():  # Parcurge preliminary.values(); elementul curent este town.
        clusters[remove_accents(lookup_key(town))].append(town)  # Adaugă elementul la sfârșitul colecției.

    representatives = {  # Stabilește representatives: numele reprezentativ al fiecărui grup.
        key: sorted(set(names), key=lambda name: (name.isupper(), name.islower(), len(name)))[0]  # Preferă formele care nu sunt integral majuscule/minuscule, apoi lungimea minimă; egalitățile păstrează ordinea mulțimii.
        for key, names in clusters.items()  # Clauză de comprehensiune: for key, names in clusters.items().
    }  # Închide dicționarul sau mulțimea.
    return {  # Întoarce {name: representatives[remove_accents(lookup_key(town))] for name, town in preliminary.items()}.
        name: representatives[remove_accents(lookup_key(town))]  # Mapează fiecare nume original la reprezentantul grupului fără accente.
        for name, town in preliminary.items()  # Clauză de comprehensiune: for name, town in preliminary.items().
    }  # Închide dicționarul sau mulțimea.


def main():  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as file:  # Gestionează automat contextul: DATA_FILE.open(newline='', encoding='utf-8-sig').
        rows = list(csv.DictReader(file))  # Materializează toate rutele ca dicționare, folosind antetul CSV.

    names = canonical_names(rows)  # Stabilește names: dicționarul nume original → nume canonic.
    connections = {  # Stabilește connections: perechile neorientate unice, după normalizarea numelor.
        tuple(sorted((names[row["from_town"]], names[row["to_town"]])))  # Sortează cele două nume canonice pentru a trata ruta ca neorientată.
        for row in rows  # Clauză de comprehensiune: for row in rows.
    }  # Închide dicționarul sau mulțimea.

    degrees = Counter()  # Stabilește degrees: contorul conexiunilor pentru fiecare oraș.
    for town_a, town_b in connections:  # Parcurge connections; elementul curent este (town_a, town_b).
        degrees[town_a] += 1  # Actualizează degrees[town_a] folosind 1.
        degrees[town_b] += 1  # Actualizează degrees[town_b] folosind 1.

    ranking = degrees.most_common()  # Stabilește ranking: orașele ordonate descrescător după grad.
    assert len(degrees) == 116, f"Expected 116 towns, found {len(degrees)}"  # Oprește execuția dacă nu este adevărat: len(degrees) == 116.
    assert len(connections) == 448, (  # Oprește execuția dacă nu este adevărat: len(connections) == 448.
        f"Expected 448 connections, found {len(connections)}"  # Construiește mesajul de eroare cu numărul real de conexiuni.
    )  # Închide apelul sau gruparea.

    top_seven = ranking[:7]  # Stabilește top_seven: primele șapte orașe după numărul de conexiuni.
    word = "".join(town[0] for town, _ in top_seven)  # Stabilește word: inițialele primelor șapte orașe.
    print(f"Towns: {len(degrees)}")  # Afișează valorile sau mesajul pentru verificare.
    print(f"Connections: {len(connections)}")  # Afișează valorile sau mesajul pentru verificare.
    print("Top towns:")  # Afișează valorile sau mesajul pentru verificare.
    for town, degree in top_seven:  # Parcurge top_seven; elementul curent este (town, degree).
        print(f"  {town}: {degree}")  # Afișează valorile sau mesajul pentru verificare.
    print(f"Flag: SIGMOID_{word}")  # Afișează valorile sau mesajul pentru verificare.


if __name__ == "__main__":  # Pornește execuția numai când fișierul este rulat direct.
    main()  # Execută fluxul principal al programului.
