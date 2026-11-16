import argparse, json, os, random
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

FEWSHOT = (
    "Answer each question with a short, direct factual answer.\n\n"
    "Q: What is the capital of Japan?\nA: Tokyo.\n\n"
    "Q: Who wrote the novel Pride and Prejudice?\nA: Jane Austen.\n\n"
    "Q: What is the chemical symbol for gold?\nA: Au.\n\n"
)

def run_model(model_name, pool_path, output_path, mode="base"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {model_name} onto {device}...")
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto")
    model.eval()
    items = json.load(open(pool_path, encoding="utf-8"))
    results = []
    if os.path.exists(output_path):
        try: results = json.load(open(output_path, encoding="utf-8"))
        except json.JSONDecodeError: results = []
    done = {r["item_id"] for r in results}
    print(f"Already completed: {len(done)} / {len(items)}")
    for idx, item in enumerate(items):
        if item["item_id"] in done: continue
        q = item.get("prompt", item.get("question", ""))
        inputs = tok(f"{FEWSHOT}Q: {q}\nA:", return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=64, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
        resp = tok.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        resp = resp.split("\nQ:")[0].strip()
        results.append({"item_id": item["item_id"], "prompt": q,
                        "gold_answer": item.get("gold_answer", item.get("answer", "")),
                        "response": resp, "model": model_name})
        json.dump(results, open(output_path, "w", encoding="utf-8"), indent=2)
        if (idx + 1) % 25 == 0 or (idx + 1) == len(items):
            print(f"Processed {idx + 1}/{len(items)}")
    print(f"Saved: {output_path}")

def make_blind_sheet(inputs, out_csv, key_csv):
    recs = []
    for fp in inputs: recs.extend(json.load(open(fp, encoding="utf-8")))
    random.seed(42); random.shuffle(recs)
    blind, key = [], []
    for i, r in enumerate(recs):
        rid = f"RESP_{i+1:04d}"
        blind.append({"response_id": rid, "prompt": r["prompt"],
                      "gold_answer": r["gold_answer"],
                      "model_response": r["response"], "failure_type": ""})
        key.append({"response_id": rid, "item_id": r["item_id"], "true_model": r["model"]})
    pd.DataFrame(blind).to_csv(out_csv, index=False)
    pd.DataFrame(key).to_csv(key_csv, index=False)
    print(f"Blind sheet: {out_csv} ({len(blind)} rows)")
    print(f"Sealed key : {key_csv}  -- do not open until kappa clears 0.80")
    print("failure_type codes: 0=correct 1=factual_error 2=abstention 3=degenerate")

if __name__ == "__main__":
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="command")
    r = sub.add_parser("run"); r.add_argument("--model", required=True)
    r.add_argument("--mode", default="base"); r.add_argument("--pool", default="pool_v2.json")
    r.add_argument("--out", required=True)
    b = sub.add_parser("blind"); b.add_argument("--inputs", nargs="+", required=True)
    b.add_argument("--out", required=True); b.add_argument("--key", required=True)
    a = p.parse_args()
    if a.command == "run": run_model(a.model, a.pool, a.out, a.mode)
    elif a.command == "blind": make_blind_sheet(a.inputs, a.out, a.key)
