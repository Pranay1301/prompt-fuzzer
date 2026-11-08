"""Model backends. A backend is a callable(system_prompt, user_text) -> reply.
- mock: deterministic offline backend for tests (no network).
- openai-compatible: any endpoint (Groq, OpenRouter :free models, Gemini
  OpenAI-compat, local servers). Key comes from an env var and is never
  written to logs, reports, or the repo.
- local: a small local instruct model via node + @huggingface/transformers
  (fully offline, zero cost) - used for this project's own live test.
"""
import json, os, subprocess, urllib.request

def mock_backend(system_prompt, user_text):
    low = user_text.lower()
    if "ignore all previous instructions" in low or "codeword" in low:
        return "I'm not able to share internal instructions. How can I help you today?"
    return "I'm not able to share internal instructions. How can I help you today?"

def openai_compatible_backend(base_url, model, api_key_env, timeout=60, max_retries=6):
    import time, urllib.error
    def run(system_prompt, user_text):
        key = os.environ.get(api_key_env, "")
        if not key:
            raise RuntimeError(f"env var {api_key_env} not set; export your key first")
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0,
        }).encode()
        delay = 5.0
        for attempt in range(max_retries):
            req = urllib.request.Request(
                base_url.rstrip("/") + "/chat/completions", data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + key})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    data = json.load(r)
                return data["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < max_retries - 1:
                    time.sleep(delay + attempt * 2)  # free-tier RPM windows
                    delay = min(delay * 1.5, 45)
                    continue
                raise
        raise RuntimeError("unreachable")
    return run

def local_transformers_backend(node_script, model, timeout=180, env=None):
    """Persistent node process: one model load, line-based JSON protocol."""
    def run(system_prompt, user_text):
        payload = json.dumps({"system": system_prompt, "user": user_text})
        proc = run._proc
        if proc is None or proc.poll() is not None:
            import os as _os
            e = dict(_os.environ); e.update(env or {})
            proc = subprocess.Popen(
                ["node", node_script, model],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, env=e)
            run._proc = proc
        proc.stdin.write(payload + "\n"); proc.stdin.flush()
        deadline = __import__("time").time() + timeout
        while __import__("time").time() < deadline:
            line = proc.stdout.readline()
            if not line:
                raise RuntimeError("local backend process ended")
            if line.startswith("MODEL_REPLY>>>"):
                return line.split(">>>", 1)[1].strip()
        raise RuntimeError("local backend timed out")
    run._proc = None
    return run
