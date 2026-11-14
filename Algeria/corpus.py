import argparse
import json
import random
import re
from pathlib import Path

from style_checker import check_reply, load_vocab, split_sentences

ROOT = Path(__file__).resolve().parent
VOCAB = load_vocab()
CLASSES = VOCAB["classes"]
WORDS = VOCAB["words"]
DIGITS = VOCAB["digits"]
TOKEN = re.compile(r"\[([A-F]):([^\]]+)\]|[0-9]+|[^\W\d_]+(?:['’][sS])?|[^\w\s]+", re.UNICODE)
CALL_ENDINGS = (
    "Answer with one noun.", "Give one noun as your answer.",
    "Reply with a single noun.", "Use one noun only.",
    "Answer in one noun.", "Give a one-noun answer.",
)
CAPITAL_QUESTIONS = (
    "What is the capital city of {place}?",
    "Which city serves as {place}'s capital?",
    "Name the capital of {place}.",
    "What city is {place}'s capital?",
    "Where is the capital of {place}?",
)
CAPITALS = (
    "Algeria:Algiers;France:Paris;Spain:Madrid;Portugal:Lisbon;Italy:Rome;"
    "Egypt:Cairo;Tunisia:Tunis;Morocco:Rabat;Libya:Tripoli;Mauritania:Nouakchott;"
    "Mali:Bamako;Niger:Niamey;Senegal:Dakar;Ghana:Accra;Kenya:Nairobi;"
    "Russia:Moscow;Iraq:Baghdad;Iran:Tehran;Netherlands:Amsterdam;Germany:Berlin;"
    "Austria:Vienna;Belgium:Brussels;Switzerland:Bern;Poland:Warsaw;Greece:Athens;"
    "Romania:Bucharest;Moldova:Chișinău;United Kingdom:London;Ireland:Dublin;"
    "Norway:Oslo;Sweden:Stockholm;Denmark:Copenhagen;Finland:Helsinki;"
    "China:Beijing;Japan:Tokyo;South Korea:Seoul;India:New Delhi;Pakistan:Islamabad;"
    "Bangladesh:Dhaka;Thailand:Bangkok;Vietnam:Hanoi;Nepal:Kathmandu;"
    "Canada:Ottawa;United States:Washington;Mexico:Mexico City;Cuba:Havana;"
    "Brazil:Brasília;Argentina:Buenos Aires;Chile:Santiago;Peru:Lima;"
    "Australia:Canberra;New Zealand:Wellington;Turkey:Ankara"
)


def register(reply):
    def encode(match):
        cls, name = match.groups()
        token = match.group()
        if cls:
            suffix = CLASSES[cls]["suffix"]
            return " ".join(f"{word}-{suffix}" for word in name.split())
        if token.isascii() and token.isdigit():
            return "-".join([*(DIGITS[int(digit)] for digit in token), CLASSES["D"]["suffix"]])
        word = token.lower()
        poss = token[-2:] if word.endswith(("'s", "’s")) else ""
        word = word[:-2] if poss else word
        key = VOCAB["forbidden_english"].get(word)
        if key is not None:
            if isinstance(key, str) and key.isascii() and key.isdigit():
                return "-".join([*(DIGITS[int(digit)] for digit in key), CLASSES["D"]["suffix"]]) + poss
            entry = WORDS.get(key, WORDS.get(word))
            if entry:
                return f"{entry['stem']}-{CLASSES[entry['class']]['suffix']}{poss}"
        return token

    lines = []
    for sentence in split_sentences(reply):
        ending = "?" if sentence.endswith("?") else "."
        source = sentence.rstrip(".?!")
        body = TOKEN.sub(encode, source)
        seal = VOCAB["neutral_seal"]
        suffixes = re.findall(r"-([a-z]+)(?=[^\w-]|$)", body)
        for suffix in reversed(suffixes):
            if suffix in VOCAB["_suffix_to_class"]:
                seal = VOCAB["_class_to_seal"][VOCAB["_suffix_to_class"][suffix]]
                break
        lines.append(f"{body} {seal}{ending}")
    result = VOCAB["opening"] + ", " + " ".join(lines)
    if check_reply(result, VOCAB)["conformance"] != 1:
        raise ValueError(f"{reply} -> {result}: {check_reply(result, VOCAB)['sentences']}")
    return result


def build(seed):
    rng = random.Random(seed)
    public = ROOT / "public"
    excluded = {
        row["prompt"].casefold()
        for file in ("prompts.json", "calls.json")
        for row in json.loads((public / file).read_text(encoding="utf-8"))
    }
    rows = {}

    def add(question, answer, noun=None, call=True):
        if question.casefold() not in excluded:
            rows[question] = {"prompt": question, "reply": register(answer), "call": False}
        if noun and call:
            target = register(noun)
            for ending in rng.sample(CALL_ENDINGS, 2):
                short = f"{question} {ending}"
                if short.casefold() not in excluded:
                    rows[short] = {"prompt": short, "reply": target, "call": True}

    for pair in CAPITALS.split(";"):
        country, city = pair.split(":")
        place = f"the {country}" if country in {"Netherlands", "United States", "United Kingdom"} else country
        marked_place = place.replace(country, f"[A:{country}]")
        noun = f"[C:{city}]"
        questions = rng.sample(CAPITAL_QUESTIONS, 3)
        for index, query in enumerate(questions):
            answer = (f"{noun} is the capital of {marked_place}." if index != 1
                      else f"The capital of {marked_place} is {noun}.")
            add(query.format(place=place), answer, noun, index == 0)

    facts = (ROOT / "facts.tsv").read_text(encoding="utf-8").splitlines()
    for line in filter(None, facts):
        queries, answer, *noun = line.split("\t")
        for index, question in enumerate(queries.split(" / ")):
            add(question, answer, noun[0] if noun else None, index == 0)

    for x, y in [(2, 2), (7, 5), (9, 4), (11, 8), (13, 19), (16, 26), (19, 23),
                 (21, 21), (12, 30), (49, 51), (10, 5), (25, 6), (18, 12), (55, 34)]:
        add(f"How much is {x} plus {y}?", f"{x} plus {y} is {x + y}.", str(x + y))
        add(f"Calculate {x} + {y}.", f"The answer is {x + y}.", str(x + y), False)

    data = list(rows.values())
    rng.shuffle(data)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "training.jsonl")
    parser.add_argument("--seed", type=int, default=31)
    args = parser.parse_args()
    data = build(args.seed)
    args.out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in data), encoding="utf-8")
    print(f"{len(data)} checked targets, {sum(row['call'] for row in data)} calls", flush=True)


if __name__ == "__main__":
    main()
