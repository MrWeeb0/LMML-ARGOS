import argparse
import json
import tempfile
from pathlib import Path

import gguf
from safetensors.numpy import save_file

from tools.lora_to_gguf import MODULE_MAP, convert


def rescale(source, output, alpha):
    reader = gguf.GGUFReader(str(source))
    modules = {dest: origin for origin, dest in MODULE_MAP.items()}
    tensors = {}
    for item in reader.tensors:
        _, layer, module, _, kind = item.name.split(".")
        letter = {"lora_a": "A", "lora_b": "B"}[kind]
        name = f"base_model.model.model.layers.{layer}.{modules[module]}.lora_{letter}.weight"
        tensors[name] = item.data.copy()
    with tempfile.TemporaryDirectory() as directory:
        peft = Path(directory)
        (peft / "adapter_config.json").write_text(json.dumps({"lora_alpha": alpha}), encoding="utf-8")
        save_file(tensors, peft / "adapter_model.safetensors")
        convert(peft, output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--alpha", type=float, required=True)
    args = parser.parse_args()
    if args.alpha <= 0:
        parser.error("alpha must be positive")
    rescale(args.source, args.output, args.alpha)


if __name__ == "__main__":
    main()
