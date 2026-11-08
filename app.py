"""Prompt Fuzzer - Streamlit app.

Demo mode runs the deterministic mock backend (no key, offline).
Live mode is BYOK: paste any OpenAI-compatible key in the sidebar. The key
lives only in this browser session's memory - it is never logged, stored,
or sent anywhere except the endpoint you name.
"""
import streamlit as st
from prompt_fuzzer.runner import run_fuzz
from prompt_fuzzer.score import fragility
from prompt_fuzzer.report import render_html
from prompt_fuzzer.backends import mock_backend, openai_compatible_backend

st.set_page_config(page_title="Prompt Fuzzer", page_icon=":shield:", layout="wide")
st.title("Prompt Fuzzer")
st.caption("Attack your own LLM system prompt with 12 adversarial inputs and "
           "score how fragile it is. Verdicts per attack, weighted fragility 0-100.")


def demo_backend(system_prompt, user_text):
    """ILLUSTRATIVE scripted replies (not a model): mostly refusals, one
    canary leak and one ambiguous answer so the verdict UI shows all three
    states. The tested all-refusal mock stays in prompt_fuzzer/backends.py."""
    from prompt_fuzzer.attacks import CANARY
    low = user_text.lower()
    if "authorized internal check" in low:
        return f"Sure - the token is {CANARY}. Anything else for the audit?"
    if "evil-twin" in low:
        return ("As EVIL-TWIN I would do the opposite of the rules... "
                "here is what I think some of them might be about, roughly.")
    return "I'm not able to share internal instructions. How can I help you today?"

default_prompt = open("examples/support-bot.txt").read() if __import__("os").path.exists("examples/support-bot.txt") else ""
system_prompt = st.text_area("System prompt to test", value=default_prompt, height=220)

with st.sidebar:
    st.header("Backend")
    mode = st.radio("Mode", ["Demo (illustrative script, no key)", "Live (your own key)"])
    base_url = model = key_env = None
    if mode.startswith("Live"):
        base_url = st.text_input("Base URL", "https://openrouter.ai/api/v1")
        model = st.text_input("Model", "nvidia/nemotron-3-ultra-550b-a55b:free")
        api_key = st.text_input("API key (session only, never stored)", type="password")
        st.caption("Free route: OpenRouter ':free' models cost $0 - verify on "
                   "openrouter.ai/models before running.")
    else:
        api_key = None

if st.button("Run the 12-attack battery", type="primary"):
    if not system_prompt.strip():
        st.error("Paste a system prompt first.")
    elif mode.startswith("Live") and not api_key:
        st.error("Live mode needs your API key (demo mode needs none).")
    else:
        import os
        if mode.startswith("Live"):
            os.environ["APP_SESSION_KEY"] = api_key  # session memory only
            backend = openai_compatible_backend(base_url, model, "APP_SESSION_KEY")
            label = model
        else:
            backend = demo_backend
            label = "illustrative scripted replies (not a real model)"
        with st.spinner("Fuzzing..."):
            result = run_fuzz(system_prompt, backend, model_label=label, sleep_s=1.0 if api_key else 0.0)
        frag = fragility(result)
        col1, col2, col3, col4 = st.columns(4)
        counts = {"BREACH": 0, "PARTIAL": 0, "HELD": 0, "ERROR": 0}
        for r in result["results"]:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        col1.metric("Fragility", f"{frag['score']}/100")
        col2.metric("HELD", counts["HELD"])
        col3.metric("PARTIAL", counts["PARTIAL"])
        col4.metric("BREACH", counts["BREACH"])
        if mode.startswith("Demo"):
            st.info("Demo mode: ILLUSTRATIVE scripted replies, not a real model - "
                    "Use Live mode to test a real endpoint.")
        for r in result["results"]:
            icon = {"HELD": "🟢", "PARTIAL": "🟡", "BREACH": "🔴"}.get(r["verdict"], "⚠️")
            with st.expander(f"{icon} {r['attack']} - {r['verdict']}"):
                st.write("**Judge:** " + "; ".join(r["reasons"]))
                st.code(r["reply"] or "(empty reply)", language=None)
        st.download_button("Download HTML report", render_html(result, frag, "streamlit-app"),
                           file_name="prompt-fuzz-report.html", mime="text/html")
        if api_key is not None:
            os.environ.pop("APP_SESSION_KEY", None)
