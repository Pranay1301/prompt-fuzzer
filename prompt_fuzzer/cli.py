"""CLI: python -m prompt_fuzzer.cli --system-prompt examples/support-bot.txt --backend mock"""
import argparse, json, os, sys
from .runner import run_fuzz
from .score import fragility
from .report import render_html
from .backends import mock_backend, openai_compatible_backend, local_transformers_backend

def main(argv=None):
    p = argparse.ArgumentParser(prog="prompt-fuzzer",
        description="Attack your own LLM prompt with adversarial inputs and score its fragility.")
    p.add_argument("--system-prompt", required=True, help="path to the system prompt to test")
    p.add_argument("--backend", choices=["mock", "openai", "local"], default="mock")
    p.add_argument("--base-url", default="https://api.groq.com/openai/v1")
    p.add_argument("--model", default="llama-3.1-8b-instant")
    p.add_argument("--api-key-env", default="GROQ_API_KEY")
    p.add_argument("--local-script", default="local_model.mjs")
    p.add_argument("--out", default="report.html")
    p.add_argument("--json-out", default="results.json")
    p.add_argument("--sleep", type=float, default=0.0)
    args = p.parse_args(argv)

    system_prompt = open(args.system_prompt).read()
    if args.backend == "mock":
        backend, label = mock_backend, "mock (offline determinism check)"
    elif args.backend == "openai":
        backend = openai_compatible_backend(args.base_url, args.model, args.api_key_env)
        label = f"{args.model} via {args.base_url}"
    else:
        backend = local_transformers_backend(args.local_script, args.model)
        label = f"{args.model} (local, CPU)"

    result = run_fuzz(system_prompt, backend, model_label=label, sleep_s=args.sleep)
    frag = fragility(result)
    open(args.json_out, "w").write(json.dumps({"result": result, "fragility": frag}, indent=2))
    open(args.out, "w").write(render_html(result, frag, os.path.basename(args.system_prompt)))
    print(f"verdicts: " + ", ".join(f"{r['attack']}={r['verdict']}" for r in result["results"]))
    print(f"fragility score: {frag['score']}  ->  {args.out}, {args.json_out}")

if __name__ == "__main__":
    main()
