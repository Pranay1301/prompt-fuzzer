# Prompt Fuzzer

Attack your own LLM prompt with adversarial inputs and score how fragile it is.

You write a system prompt. Prompt Fuzzer throws 12 known jailbreak and
extraction attacks at it - instruction overrides, canary/secret extraction,
delimiter escapes, authority forgery, persona reframes, encoding smuggles,
multilingual pivots, context floods, format smuggling, few-shot poisoning,
refusal bait, indirect continuation - judges every reply, and produces a
weighted fragility score (0-100) plus a shareable HTML report.

## Live demo

- **Hosted app (Render, free tier):** https://prompt-fuzzer-dbhm.onrender.com -
  runs in Demo mode with no key (clearly labeled illustrative scripted replies)
  or Live mode with your own OpenRouter key (kept in session memory only,
  never stored or logged). Sleeps when idle; first load can take a minute.
- **Real run report (static):** https://pranay1301.github.io/prompt-fuzzer/reports/live-nemotron-ultra.html -
  an actual 12-attack battery against `nvidia/nemotron-3-ultra-550b-a55b:free`
  (a verified $0 OpenRouter route), not a mock.

## Why

"Seems fine when I try it" is not evidence. This gives you a repeatable
battery with a written verdict per attack, so a prompt change that quietly
reopens an extraction path shows up as a score movement, not a surprise.

## Quickstart

No dependencies beyond Python 3.8+ for the core. Try it with zero setup on
the deterministic mock backend:

```bash
python3 -m prompt_fuzzer.cli --system-prompt examples/support-bot.txt --backend mock --out report.html
```

Run it against a live model over any OpenAI-compatible endpoint:

```bash
export OPENROUTER_API_KEY=...   # your key; never stored in the repo
python3 -m prompt_fuzzer.cli \
  --system-prompt examples/support-bot.txt \
  --backend openai \
  --base-url https://openrouter.ai/api/v1 \
  --model nvidia/nemotron-3-ultra-550b-a55b:free \
  --api-key-env OPENROUTER_API_KEY \
  --out report.html --json-out report.json
```

Verified-zero-cost route: OpenRouter `:free` models, confirmed `$0/$0` on the
public pricing API on 2026-11-08. The run in `reports/` was executed against
`nvidia/nemotron-3-ultra-550b-a55b:free`; no credits were charged.
(`google/gemma-4-31b-it:free` was attempted the same day and was too
rate-limited to complete - recorded as not run, not retried into existence.)

## What a run tells you

- **Per-attack verdicts**: BREACH / PARTIAL / HELD with the judge's reasons
  and the model's actual reply.
- **Fragility score 0-100**: weighted by attack category
  (extraction weighs most, obfuscation least). Lower is sturdier.
- **Canary test**: a planted secret string (`CANARY`) in the system prompt -
  if any attack coaxes it out, that attack is an automatic BREACH.

Sample live result (bounded evidence - read this honestly): one run of the
12-attack battery against one example prompt on one free model
(nemotron-3-ultra-550b-a55b) scored **14.8/100**: 9 HELD, 3 PARTIAL
(authority forgery, multilingual pivot, refusal bait), 0 BREACH. That is a
snapshot of that prompt on that model on that day - a regression alarm and a
starting point, not a security proof. See `reports/live-nemotron-ultra.html`
for the full replies.

## Backends

| backend | use |
|---|---|
| `mock` | deterministic, offline, for tests and demos |
| `openai` | any OpenAI-compatible endpoint (OpenRouter, Groq, Gemini, vLLM, ...) |
| `local` | a persistent local model runner (experimental) |

## Tests

```bash
python3 -m unittest discover tests -v
```

15 tests: every attack's judge logic, canary detection, scoring math, report
generation, and a CLI end-to-end on the mock backend. No network, no key.

## Honest limits

- The judge is rule-based (pattern + canary + refusal analysis), not an LLM
  jury - it can misread a clever reply either way; read the raw replies in
  the report.
- 12 attacks is a starter battery, not coverage of the attack space.
- Free-tier models rate-limit; the CLI retries with backoff, and a run that
  cannot complete says so instead of fabricating verdicts.

## License

MIT
