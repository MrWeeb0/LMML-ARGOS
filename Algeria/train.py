import argparse
import gc
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from corpus import build
from evaluation_script import build_prompt

ROOT = Path(__file__).resolve().parent
BASE = "HuggingFaceTB/SmolLM2-360M-Instruct"


def encode(rows, tokenizer, torch):
    groups = defaultdict(list)
    for row in rows:
        prompt = build_prompt(row["prompt"])
        prefix = tokenizer.encode(prompt, add_special_tokens=False)
        ids = tokenizer.encode(prompt + row["reply"] + "<|im_end|>", add_special_tokens=False)
        if ids[:len(prefix)] != prefix:
            raise ValueError(f"Token boundary changed for {row['prompt']}")
        groups[row["call"], (len(ids) + 7) // 8].append(
            (torch.tensor(ids), torch.tensor([-100] * len(prefix) + ids[len(prefix):]))
        )
    return groups


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE)
    parser.add_argument("--checkpoints", type=int, nargs="+", default=[240, 460, 720])
    parser.add_argument("--rank", type=int, default=16)
    parser.add_argument("--layers", type=int, default=12)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--lr", type=float, default=0.00055)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--output", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--no-eval", action="store_true")
    args = parser.parse_args()
    if args.batch < 1 or args.layers < 1 or args.rank < 1 or args.checkpoints != sorted(set(args.checkpoints)):
        parser.error("use positive dimensions and strictly increasing checkpoints")
    if min(args.checkpoints) < 1:
        parser.error("checkpoints must be positive")

    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    rng = random.Random(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    bf16 = (
        torch.cuda.is_bf16_supported() if device.type == "cuda"
        else getattr(torch.backends.cpu, "is_bf16_supported", lambda: False)()
    )
    dtype = torch.bfloat16 if bf16 else torch.float32
    tok = AutoTokenizer.from_pretrained(args.base)
    base = AutoModelForCausalLM.from_pretrained(args.base, dtype=dtype).to(device)
    base.config.use_cache = False
    body = base.model
    cut = max(0, len(body.layers) - args.layers)
    model = get_peft_model(base, LoraConfig(
        r=args.rank, lora_alpha=2 * args.rank, task_type="CAUSAL_LM",
        target_modules=["v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        layers_to_transform=list(range(cut, len(body.layers))), layers_pattern="layers",
    ))
    model.print_trainable_parameters()
    groups = encode(build(args.seed), tok, torch)
    print(f"{device} {dtype}, {sum(map(len, groups.values()))} examples, {cut} frozen prefix layers", flush=True)

    def batch(items):
        ids, labels = zip(*items)
        ids = torch.nn.utils.rnn.pad_sequence(ids, batch_first=True, padding_value=tok.pad_token_id if ids[0].ndim == 1 else 0).to(device)
        labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100).to(device)
        lengths = torch.tensor([len(item[0]) for item in items], device=device)
        mask = torch.arange(ids.shape[1], device=device)[None, :] < lengths[:, None]
        return ids, labels, mask

    full = body.layers
    st = time.monotonic()
    if cut:
        body.layers = torch.nn.ModuleList(list(full[:cut]))
        norm = body.norm
        body.norm = torch.nn.Identity()
        body.eval()
        with torch.no_grad():
            for key, items in groups.items():
                cached = []
                for offset in range(0, len(items), 12):
                    chunk = items[offset:offset + 12]
                    ids, _, mask = batch(chunk)
                    hidden = body(input_ids=ids, attention_mask=mask, use_cache=False).last_hidden_state.cpu()
                    cached.extend((h[:len(ids_i)].clone(), labels) for h, (ids_i, labels) in zip(hidden, chunk))
                groups[key] = cached
        body.norm = norm
        body.layers = torch.nn.ModuleList(list(full[cut:]))
        print(f"Cached frozen states in {time.monotonic() - st:.1f}s", flush=True)

    choices = {kind: [key for key in groups if key[0] == kind] for kind in (False, True)}
    weights = {kind: [len(groups[key]) for key in keys] for kind, keys in choices.items()}
    parameters = [param for param in model.parameters() if param.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=args.lr, weight_decay=0.01)
    args.output.mkdir(parents=True, exist_ok=True)
    model.train()
    total_loss = 0.0
    for step in range(1, max(args.checkpoints) + 1):
        kind = step % 3 == 0
        key = rng.choices(choices[kind], weights=weights[kind])[0]
        items = rng.sample(groups[key], min(args.batch, len(groups[key])))
        inputs, labels, mask = batch(items)
        kwargs = {"inputs_embeds": inputs} if cut else {"input_ids": inputs}
        hidden = body(**kwargs, attention_mask=mask, use_cache=False).last_hidden_state
        active = labels[:, 1:] != -100
        logits = base.lm_head(hidden[:, :-1][active]).float()
        loss = torch.nn.functional.cross_entropy(logits, labels[:, 1:][active])
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, 1.0)
        if step <= 20:
            optimizer.param_groups[0]["lr"] = args.lr * step / 20
        elif step > args.checkpoints[0]:
            optimizer.param_groups[0]["lr"] = args.lr * 0.6
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        total_loss += loss.item()
        if step % 20 == 0:
            print(f"step {step}: loss {total_loss / 20:.3f}, {time.monotonic() - st:.0f}s", flush=True)
            total_loss = 0.0
        if step in args.checkpoints:
            checkpoint = args.output / str(step)
            body.layers = full
            model.save_pretrained(checkpoint, save_embedding_layers=False)
            if cut:
                body.layers = torch.nn.ModuleList(list(full[cut:]))
            adapter = args.output / f"adapter-{step}.gguf"
            subprocess.run(
                [sys.executable, "tools/lora_to_gguf.py", str(checkpoint), "--outfile", str(adapter)],
                cwd=ROOT, check=True,
            )
            if args.no_eval:
                continue
            gc.collect()
            evaluation = args.output / f"evaluation-{step}.json"
            result = subprocess.run(
                [sys.executable, "evaluation_script.py", "--data", "public", "--model",
                 str(adapter), "--out", str(evaluation)],
                cwd=ROOT,
            )
            if result.returncode == 0:
                (ROOT / "adapter.gguf").write_bytes(adapter.read_bytes())
                (ROOT / "evaluation.json").write_bytes(evaluation.read_bytes())
                return 0
            if result.returncode != 1 or not evaluation.is_file():
                raise RuntimeError("The official evaluator did not produce a score report.")
    return 0 if args.no_eval else 1


if __name__ == "__main__":
    sys.exit(main())
