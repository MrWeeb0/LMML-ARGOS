from __future__ import annotations

import json
import re
from pathlib import Path


WORD = r"A-Za-zÀ-ÖØ-öø-ÿ"
NAME = rf"[{WORD}]+(?:[-'][{WORD}]+)?(?:\s+[{WORD}]+(?:[-'][{WORD}]+)?)"


def redact(text: str) -> str:
    """Replace personal values while preserving the surrounding message."""
    # Replace the longest, most structured values first.
    text = re.sub(
        r"\b[A-Z]{2}\d{2}(?:[\s-]*\d{4}){4}[\s-]*\d{2}\b",
        "[ACCOUNT]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?i)\b(?:my\s+)?(?:date\s+of\s+birth)\s+is\s+"
        r"(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4}|"
        r"(?:january|february|march|april|may|june|july|august|"
        r"september|october|november|december)\s+\d{1,2},\s+\d{4})",
        lambda match: re.sub(r"is\s+.*$", "is [DOB]", match.group(0), flags=re.I),
        text,
    )
    text = re.sub(r"\b\d-\d{4}-\d{4}\b|\b\d{9}\b", "[ID]", text)
    text = re.sub(
        r"(?<![\d-])(?:\+506[\s-]*)?\d{4}[\s-]\d{4}(?![\d-])"
        r"|(?<![\d-])(?:\+506[\s-]*)?\d{8}(?![\d-])",
        "[PHONE]",
        text,
    )
    text = re.sub(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[EMAIL]",
        text,
        flags=re.IGNORECASE,
    )

    # Addresses are variable-length phrases, so use their surrounding prose.
    text = re.sub(
        rf"(?i)(\b(?:the\s+)?pickup\s+at\s+)(.*?)(?=\s+to\s+our\s+booking\b)",
        r"\1[ADDRESS]",
        text,
    )
    text = re.sub(
        rf"(?i)(\b(?:send\s+the\s+)?(?:paperwork|written\s+reply)\s+to\s+)(.*?)(?=[.!?])",
        r"\1[ADDRESS]",
        text,
    )

    # Names in labelled passenger/name fields.
    text = re.sub(
        rf"(?i)(\bmy\s+name\s+is\s+){NAME}",
        r"\1[NAME]",
        text,
    )
    text = re.sub(
        rf"(?i)(\bmy\s+(?:son|daughter|wife|husband)\s+){NAME}(?=\s+will\b)",
        r"\1[NAME]",
        text,
    )

    # The signature is a personal name on the line after "Regards,".
    text = re.sub(
        rf"(?im)(^(\s*regards,\s*\n)\s*){NAME}\s*$",
        r"\2[NAME]",
        text,
    )
    text = re.sub(
        rf"(?i)(\bregards,\s*){NAME}\s*$",
        r"\1[NAME]",
        text,
    )
    return text


def main() -> None:
    input_path = Path("test-input.json")
    output_path = Path("test-output.json")
    if not input_path.exists():
        input_path = Path("train-input.json")
        output_path = Path("train-predicted-output.json")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    documents = payload.get("documents")
    if not isinstance(documents, list):
        raise ValueError("Input must contain a documents list.")
    redacted_documents: dict[str, str] = {}
    for document in documents:
        if not isinstance(document, dict) or not isinstance(document.get("id"), str):
            raise ValueError("Each document must have a string id.")
        if not isinstance(document.get("text"), str):
            raise ValueError("Each document must have string text.")
        redacted_documents[document["id"]] = redact(document["text"])

    output_path.write_text(
        json.dumps({"redacted_documents": redacted_documents}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
