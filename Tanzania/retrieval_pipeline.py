"""Broken starter retrieval pipeline for the Tanzania agents task."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from flag_utils import derive_flag, load_verification_codes

DOCUMENT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
QUERY_MODEL = "intfloat/e5-small-v2"
CHUNK_SIZE = 180
STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "called",
    "does",
    "for",
    "from",
    "give",
    "in",
    "is",
    "of",
    "on",
    "or",
    "should",
    "the",
    "their",
    "this",
    "to",
    "under",
    "what",
    "when",
    "where",
    "which",
    "with",
}


@dataclass(frozen=True)
class Document:
    """One searchable source document."""

    document_id: str
    title: str
    text: str


@dataclass(frozen=True)
class Chunk:
    """One searchable fragment and its source document ID."""

    document_id: str
    text: str


def load_corpus(corpus_path: Path) -> list[Document]:
    """Read source documents from a JSON Lines corpus.

    :param corpus_path: Corpus file supplied with the task.
    :return: Searchable documents in file order.
    """
    documents: list[Document] = []
    with corpus_path.open(encoding="utf-8") as corpus_file:
        for line in corpus_file:
            row = json.loads(line)
            documents.append(Document(row["document_id"], row["title"], row["text"]))
    return documents


def load_questions(questions_path: Path) -> list[dict[str, str]]:
    """Read the ordered retrieval questions.

    :param questions_path: JSON question file supplied with the task.
    :return: Question objects in official order.
    """
    with questions_path.open(encoding="utf-8") as questions_file:
        questions = json.load(questions_file)
    if not isinstance(questions, list):
        raise ValueError("questions.json must contain a list.")
    return questions


def split_into_chunks(documents: list[Document]) -> list[Chunk]:
    """Split documents into fixed character slices.

    :param documents: Complete source documents.
    :return: Fixed-width fragments used by the broken starter.
    """
    chunks: list[Chunk] = []
    for document in documents:
        searchable_text = f"{document.title}\n{document.text}"
        for start in range(0, len(searchable_text), CHUNK_SIZE):
            chunks.append(
                Chunk(document.document_id, searchable_text[start : start + CHUNK_SIZE])
            )
    return chunks


def retrieve_documents(
    chunks: list[Chunk],
    questions: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return one source document for every question.

    :param chunks: Searchable text fragments.
    :param questions: Ordered task questions.
    :return: Top source document ID for each question.
    """
    def terms(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in STOP_WORDS
        }

    document_chunks: dict[str, list[str]] = {}
    for chunk in chunks:
        document_chunks.setdefault(chunk.document_id, []).append(chunk.text)

    results: list[dict[str, str]] = []
    for question in questions:
        query_terms = terms(question["question"])
        ranked_documents: list[tuple[float, str]] = []
        for document_id, document_parts in document_chunks.items():
            document_text = "\n".join(document_parts)
            title, _, body = document_text.partition("\n")
            title_terms = terms(title)
            body_terms = terms(body)
            score = (
                10 * len(query_terms & title_terms)
                + len(query_terms & body_terms)
            )
            if "current access notice" in title.lower():
                score += 6
            ranked_documents.append((score, document_id))

        _, best_document_id = max(ranked_documents)
        results.append(
            {
                "question_id": question["question_id"],
                "document_id": best_document_id,
            }
        )
    return results


def parse_arguments() -> argparse.Namespace:
    """Parse command-line file locations.

    :return: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("corpus.jsonl"))
    parser.add_argument("--questions", type=Path, default=Path("questions.json"))
    parser.add_argument("--output", type=Path, default=Path("retrieved_ids.json"))
    return parser.parse_args()


def main() -> None:
    """Run retrieval, save IDs, and print the derived flag."""
    arguments = parse_arguments()
    documents = load_corpus(arguments.corpus)
    questions = load_questions(arguments.questions)
    results = retrieve_documents(split_into_chunks(documents), questions)
    arguments.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    flag = derive_flag(results, questions, load_verification_codes(arguments.corpus))
    print(f"Saved {len(results)} results to {arguments.output}.")
    print(flag)


if __name__ == "__main__":
    main()
