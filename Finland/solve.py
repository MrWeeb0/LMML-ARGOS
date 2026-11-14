import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


DATA_FILE = Path(__file__).with_name("routes.csv")


ALIASES = {
    "Alavo": "Alavus",
    "Björneborg": "Pori",
    "Borga": "Porvoo",
    "Borgå": "Porvoo",
    "Brahestad": "Raahe",
    "Esbo": "Espoo",
    "Grankulla": "Kauniainen",
    "Fredrikshamn": "Hamina",
    "Hango": "Hanko",
    "Hangö": "Hanko",
    "Helsingfors": "Helsinki",
    "Hyvinge": "Hyvinkää",
    "Hyvinkaa": "Hyvinkää",
    "Hameenlinna": "Hämeenlinna",
    "Tavastehus": "Hämeenlinna",
    "Idensalmi": "Iisalmi",
    "Ikalis": "Ikaalinen",
    "Ilmola": "Ilmajoki",
    "Ingå": "Inkoo",
    "Jakobstad": "Pietarsaari",
    "Jyvaskyla": "Jyväskylä",
    "Kajana": "Kajaani",
    "Karleby": "Kokkola",
    "Kaskö": "Kaskinen",
    "Kemijarvi": "Kemijärvi",
    "Kemionsaari": "Kemiönsaari",
    "Kimitoön": "Kemiönsaari",
    "Kimitoon": "Kemiönsaari",
    "Keuru": "Keuruu",
    "Kyrkslätt": "Kirkkonummi",
    "Kyrkslatt": "Kirkkonummi",
    "Kumo": "Kokemäki",
    "Kristinestad": "Kristiinankaupunki",
    "Kronoby": "Kruunupyy",
    "Lahtis": "Lahti",
    "Villmanstrand": "Lappeenranta",
    "Lappo": "Lapua",
    "Larsmo": "Luoto",
    "Lempaala": "Lempäälä",
    "Leppavirta": "Leppävirta",
    "Lojo": "Lohja",
    "Lovisa": "Loviisa",
    "Malax": "Maalahti",
    "Mantsala": "Mäntsälä",
    "S:t Michel": "Mikkeli",
    "Narpes": "Närpiö",
    "Närpes": "Närpiö",
    "Narpio": "Närpiö",
    "Nådendal": "Naantali",
    "Nurmijarvi": "Nurmijärvi",
    "Nystad": "Uusikaupunki",
    "Uleåborg": "Oulu",
    "Pargas": "Parainen",
    "Pieksamaki": "Pieksämäki",
    "Raseborg": "Raasepori",
    "Reso": "Raisio",
    "Raumo": "Rauma",
    "Seinajoki": "Seinäjoki",
    "Sibbo": "Sipoo",
    "Sjundea": "Siuntio",
    "Sjundeå": "Siuntio",
    "S:t Karins": "Kaarina",
    "Tammerfors": "Tampere",
    "Tornea": "Tornio",
    "Torneå": "Tornio",
    "Tusby": "Tuusula",
    "Ulvsby": "Ulvila",
    "Nykarleby": "Uusikaarlepyy",
    "Vasa": "Vaasa",
    "Vanda": "Vantaa",
    "Vichtis": "Vihti",
    "Virmo": "Mynämäki",
    "Voyri": "Vöyri",
    "Vörå": "Vöyri",
    "Ylojarvi": "Ylöjärvi",
    "Åbo": "Turku",
    "Abo": "Turku",
    "Birkala": "Pirkkala",
    "Korsholm": "Mustasaari",
    "Kervo": "Kerava",
    "Lundo": "Lieto",
    "Traskanda": "Järvenpää",
    "Hogfors": "Karkkila",
    "Högfors": "Karkkila",
}


def lookup_key(value):
    return re.sub(r"[. ]", "", value).casefold()


def remove_accents(value):
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def canonical_names(rows):
    raw_names = {
        row[column]
        for row in rows
        for column in ("from_town", "to_town")
    }
    alias_lookup = {lookup_key(name): town for name, town in ALIASES.items()}
    preliminary = {
        name: alias_lookup.get(lookup_key(name), name.strip().rstrip("."))
        for name in raw_names
    }

    clusters = defaultdict(list)
    for town in preliminary.values():
        clusters[remove_accents(lookup_key(town))].append(town)

    representatives = {
        key: sorted(set(names), key=lambda name: (name.isupper(), name.islower(), len(name)))[0]
        for key, names in clusters.items()
    }
    return {
        name: representatives[remove_accents(lookup_key(town))]
        for name, town in preliminary.items()
    }


def main():
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    names = canonical_names(rows)
    connections = {
        tuple(sorted((names[row["from_town"]], names[row["to_town"]])))
        for row in rows
    }

    degrees = Counter()
    for town_a, town_b in connections:
        degrees[town_a] += 1
        degrees[town_b] += 1

    ranking = degrees.most_common()
    assert len(degrees) == 116, f"Expected 116 towns, found {len(degrees)}"
    assert len(connections) == 448, (
        f"Expected 448 connections, found {len(connections)}"
    )

    top_seven = ranking[:7]
    word = "".join(town[0] for town, _ in top_seven)
    print(f"Towns: {len(degrees)}")
    print(f"Connections: {len(connections)}")
    print("Top towns:")
    for town, degree in top_seven:
        print(f"  {town}: {degree}")
    print(f"Flag: SIGMOID_{word}")


if __name__ == "__main__":
    main()
