"""Runs one model over pool_probe_v2.json with greedy decoding. Resumable.

Usage: python code/run_probe.py --model EleutherAI/pythia-2.8b
"""
import argparse
import json
import os
import time

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

# Two worked examples with invented facts, shown before every context item.
PREAMBLE = (
    "Read the text and answer using ONLY what the text says.\n\n"
    "Text:\n- The capital of Veldoria is Marn.\n"
    "Question: According to the text, what is the capital of Veldoria?\nAnswer: Marn\n\n"
    "Read the text and answer using ONLY what the text says.\n\n"
    "Text:\n- The chemical symbol of zorium is Zq.\n"
    "Question: According to the text, what is the chemical symbol of zorium?\nAnswer: Zq\n\n"
)


def out_path(model):
    return os.path.join("outputs", model.replace("/", "__") + ".jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--pool", default="pool_probe_v2.json")
    ap.add_argument("--max-new-tokens", type=int, default=12)
    a = ap.parse_args()

    os.makedirs("outputs", exist_ok=True)
    path = out_path(a.model)
    done = set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                done.add(json.loads(line)["item_id"])
    pool = json.load(open(a.pool, encoding="utf-8"))
    todo = [it for it in pool if it["item_id"] not in done]
    if not todo:
        print(f"[{a.model}] already complete ({len(done)} items)")
        return

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if dev == "cuda" else torch.float32
    print(f"[{a.model}] loading on {dev}; {len(done)} done, {len(todo)} to go", flush=True)
    tok = AutoTokenizer.from_pretrained(a.model)
    new_api = tuple(int(x) for x in transformers.__version__.split(".")[:2]) >= (4, 56)
    kw = {"dtype": dtype} if new_api else {"torch_dtype": dtype}
    model = AutoModelForCausalLM.from_pretrained(a.model, device_map="auto", **kw)
    model.eval()
    pad = tok.eos_token_id if tok.eos_token_id is not None else 0

    t0 = time.time()
    with open(path, "a", encoding="utf-8") as fh:
        for k, it in enumerate(todo, 1):
            prompt = it["prompt"] if it["condition"] == "baseline" else PREAMBLE + it["prompt"]
            enc = tok(prompt, return_tensors="pt").to(model.device)
            ids = enc["input_ids"]
            with torch.no_grad():
                out = model.generate(input_ids=ids, attention_mask=enc.get("attention_mask"),
                                     max_new_tokens=a.max_new_tokens, do_sample=False, pad_token_id=pad)
            text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
            text = text.strip().split("\n")[0].strip()
            rec = {k2: it[k2] for k2 in ("item_id", "fact_id", "category", "condition", "length",
                                         "position", "planted", "real_answer", "context_answer")}
            rec.update(model=a.model, response=text)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if k % 100 == 0 or k == len(todo):
                rate = (time.time() - t0) / k
                print(f"[{a.model}] {k}/{len(todo)}  {rate:.2f}s/item  "
                      f"~{rate * (len(todo) - k) / 60:.0f} min left", flush=True)


if __name__ == "__main__":
    main()
