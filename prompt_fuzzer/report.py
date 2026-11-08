"""Self-contained HTML report."""
import html, json

def render_html(result, frag, target_name):
    rows = []
    for r in result["results"]:
        color = {"BREACH": "#b3261e", "HELD": "#176b44", "PARTIAL": "#8a6d1a",
                 "ERROR": "#555"}[r["verdict"]]
        rows.append(
            f"<tr><td><b>{html.escape(r['attack'])}</b><br>"
            f"<small>{html.escape(r['category'])}</small></td>"
            f"<td style='color:{color};font-weight:700'>{r['verdict']}</td>"
            f"<td>{html.escape('; '.join(r['reasons']))}</td>"
            f"<td><details><summary>reply</summary><pre>{html.escape(r['reply'][:1500])}</pre>"
            f"</details></td></tr>")
    cats = "".join(
        f"<tr><td>{c}</td><td>{d['breaches']}/{d['n']} breaches</td></tr>"
        for c, d in frag["per_category"].items())
    score = "n/a (all runs errored)" if frag["score"] is None else f"{frag['score']} / 100"
    return f"""<!doctype html><html><head><meta charset=utf-8>
<title>Prompt Fuzzer report - {html.escape(target_name)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#14181d}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}td,th{{border:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top}}
pre{{white-space:pre-wrap;font-size:.8rem;max-height:220px;overflow:auto}}.score{{font-size:2rem;font-weight:800}}
.note{{background:#fdf6e3;border:1px solid #e8d9be;padding:.8rem;border-radius:8px}}</style></head><body>
<h1>Prompt Fuzzer report</h1>
<p><b>Target prompt:</b> {html.escape(target_name)} &nbsp; <b>Model:</b> {html.escape(result['model'])} &nbsp; <b>Run:</b> {result['timestamp']}</p>
<p class=score>Fragility score: {score}</p>
<p class=note>{html.escape(frag['note'])}. A canary token was planted in the system prompt; extraction attacks try to make the model reveal it. Scores are per-run and per-model - they are not a universal safety rating.</p>
<h2>By category</h2><table><tr><th>Category</th><th>Outcome</th></tr>{cats}</table>
<h2>Every attack</h2><table><tr><th>Attack</th><th>Verdict</th><th>Why</th><th>Reply</th></tr>{''.join(rows)}</table>
</body></html>"""
