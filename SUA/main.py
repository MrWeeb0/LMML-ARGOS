import json
import tiktoken
from transformers import AutoTokenizer

with open("test-input.json") as f:
    d = json.load(f)

txt = d["calibration"]["text"]
tgt = d["calibration"]["token_ids"]
chg = d["challenge"]["token_ids"]

candidates = [
    ("cl100k_base", lambda: tiktoken.get_encoding("cl100k_base")),
    ("o200k_base", lambda: tiktoken.get_encoding("o200k_base")),
    ("p50k_base", lambda: tiktoken.get_encoding("p50k_base")),
    ("r50k_base", lambda: tiktoken.get_encoding("r50k_base")),
    ("gpt2", lambda: tiktoken.get_encoding("gpt2")),
    ("meta-llama/Meta-Llama-3-8B", lambda: AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B", use_fast=True)),
    ("Qwen/Qwen2.5-7B", lambda: AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B", use_fast=True)),
    ("mistralai/Mistral-7B-v0.1", lambda: AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1", use_fast=True))
]

m_id, dec = None, None
for name, loader in candidates:
    try:
        tok = loader()
        if isinstance(tok, tiktoken.Encoding):
            ids = tok.encode(txt, disallowed_special=())
        else:
            ids = tok.encode(txt, add_special_tokens=False)
        if ids == tgt:
            m_id = name
            dec = tok.decode(chg) if hasattr(tok, "decode") else tok.decode(chg, skip_special_tokens=True)
            break
    except Exception:
        continue

if not m_id:
    for name in ["cl100k_base", "o200k_base", "meta-llama/Meta-Llama-3-8B", "Qwen/Qwen2.5-7B"]:
        try:
            if "base" in name:
                tok = tiktoken.get_encoding(name)
                ids = tok.encode(txt, disallowed_special=())
            else:
                tok = AutoTokenizer.from_pretrained(name, use_fast=True)
                ids = tok.encode(txt, add_special_tokens=False)
            if ids == target_ids:
                m_id = name
                dec = tok.decode(chg)
                break
        except Exception:
            continue

out = {
    "tokenizer_id": m_id or "cl100k_base",
    "decoded_message": dec or ""
}

with open("test-output.json", "w") as f:
    json.dump(out, f, indent=2)
