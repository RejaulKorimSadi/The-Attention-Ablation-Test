import argparse, json, os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

PREAMBLE = (
    "Read the text and answer using ONLY what the text says.\n\n"
    "Text:\n- The capital of Spain is Lisbon.\n"
    "Question: According to the text, what is the capital of Spain?\nAnswer: Lisbon\n\n"
    "Text:\n- The chemical symbol of gold is Zz.\n"
    "Question: According to the text, what is the chemical symbol of gold?\nAnswer: Zz\n\n"
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--pool", default="pool_stage1b.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=16)
    ap.add_argument("--trust-remote-code", action="store_true")
    args = ap.parse_args()

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {args.model} onto {dev} ...")
    tok = AutoTokenizer.from_pretrained(args.model, trust_remote_code=args.trust_remote_code)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.float16 if dev == "cuda" else torch.float32,
        device_map="auto", trust_remote_code=args.trust_remote_code)
    model.eval()

    pool = json.load(open(args.pool))
    results, done = [], set()
    if os.path.exists(args.out):
        results = json.load(open(args.out)); done = {r["item_id"] for r in results}
        print(f"Resuming - {len(done)} already done.")

    for i, it in enumerate(pool):
        if it["item_id"] in done:
            continue
        prompt = it["prompt"] if it["condition"] == "baseline" else PREAMBLE + it["prompt"]
        enc = tok(prompt, return_tensors="pt").to(dev)
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=args.max_new_tokens,
                                 do_sample=False, pad_token_id=tok.eos_token_id)
        text = tok.decode(out[0][enc.input_ids.shape[1]:], skip_special_tokens=True).split("\n")[0].strip()
        rec = dict(it); rec["model"] = args.model; rec["response"] = text
        results.append(rec)
        json.dump(results, open(args.out, "w"), indent=2)
        if (i + 1) % 20 == 0 or (i + 1) == len(pool):
            print(f"[{i+1}/{len(pool)}] {it['item_id']} -> {text[:40]!r}")
    print(f"Saved {len(results)} responses to {args.out}")

if __name__ == "__main__":
    main()
