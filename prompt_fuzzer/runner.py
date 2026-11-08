"""Run every attack against a target system prompt through a backend and
judge each reply. Produces a result dict consumed by score/report."""
import time
from .attacks import ATTACKS, CATEGORIES, CANARY
from .judge import judge

def run_fuzz(system_prompt, backend, model_label="unknown-model", sleep_s=0.0):
    results = []
    for name, fn in ATTACKS.items():
        attack_text = fn(system_prompt)
        err = None
        try:
            reply = backend(system_prompt, attack_text)
        except Exception as e:  # backend failure is reported, never hidden
            reply, err = "", f"{type(e).__name__}: {e}"
        if err:
            verdict, reasons = "ERROR", [err]
        else:
            verdict, reasons = judge(reply, system_prompt, CANARY)
        results.append({
            "attack": name, "category": CATEGORIES[name],
            "verdict": verdict, "reasons": reasons, "reply": reply,
        })
        if sleep_s:
            time.sleep(sleep_s)
    return {"model": model_label, "canary_mode": "planted-token",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "results": results}
