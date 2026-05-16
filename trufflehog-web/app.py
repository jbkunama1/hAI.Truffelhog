import os
import json
import subprocess
from datetime import datetime, timedelta

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template_string,
    send_file,
    abort,
)
from markupsafe import Markup

app = Flask(__name__)

DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

QUERIES_FILE = os.path.join(DATA_DIR, "queries.json")


# -----------------------------
# Hilfsfunktionen für Saved Queries
# -----------------------------

def load_saved_queries():
    if not os.path.isfile(QUERIES_FILE):
        return []
    try:
        with open(QUERIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_saved_queries(queries):
    try:
        with open(QUERIES_FILE, "w", encoding="utf-8") as f:
            json.dump(queries, f, indent=2)
    except Exception:
        pass


# -----------------------------
# Zeit-Parsing für --since
# -----------------------------

def parse_since(value: str) -> str | None:
    """
    Unterstützt:
    - ISO-String: 2026-05-16T18:00:00
    - last_hours=2  -> jetzt - 2 Stunden (UTC)
    """
    value = value.strip()
    if not value:
        return None

    if value.startswith("last_hours="):
        try:
            hours = int(value.split("=", 1)[1])
            dt = datetime.utcnow() - timedelta(hours=hours)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

    # sonst: direkt verwenden (du gibst selbst ein valides Format vor)
    return value


# -----------------------------
# Markdown-Report aus JSON bauen
# -----------------------------

def render_markdown_report(json_text: str, meta: dict) -> str:
    """
    Erzeugt eine einfache Markdown-Zusammenfassung der TruffleHog-Resultate.
    Versucht sowohl JSON-Liste als auch JSON-Lines zu verstehen.
    """
    lines = []
    lines.append("# TruffleHog Report")
    lines.append("")
    lines.append(f"- Target: `{meta.get('target', '-')}`")
    lines.append(f"- Mode: `{meta.get('mode', '-')}`")
    lines.append(f"- Results: `{meta.get('results', '-')}`")
    if meta.get("since"):
        lines.append(f"- Since: `{meta['since']}`")
    lines.append(f"- Timestamp: `{meta.get('timestamp', '-')}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    findings = []

    # Versuch 1: komplette Ausgabe als JSON-Liste
    try:
        data = json.loads(json_text)
        if isinstance(data, list):
            findings = data
        else:
            findings = [data]
    except json.JSONDecodeError:
        # Versuch 2: JSON-Lines
        for line in json_text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                findings.append(obj)
            except json.JSONDecodeError:
                continue

    if not findings:
        lines.append("_Keine Findings oder Ausgabe nicht im erwarteten JSON-Format._")
        return "\n".join(lines)

    lines.append("## Findings")
    lines.append("")

    for idx, fnd in enumerate(findings, start=1):
        rule_name = fnd.get("rule_name") or fnd.get("DetectorName") or "unbekannt"
        verified = fnd.get("verified") or fnd.get("Verified") or False
        redacted = fnd.get("redacted") or fnd.get("Raw") or ""
        extra = fnd.get("extra") or {}
        file_path = extra.get("file") or extra.get("path") or ""
        line_info = extra.get("line") or ""
        commit = extra.get("commit") or ""

        lines.append(f"### Finding {idx}")
        lines.append("")
        lines.append(f"- Regel/Detector: `{rule_name}`")
        lines.append(f"- Verified: `{verified}`")
        if file_path:
            lines.append(f"- Datei: `{file_path}`")
        if line_info:
            lines.append(f"- Zeile/Position: `{line_info}`")
        if commit:
            lines.append(f"- Commit: `{commit}`")
        if redacted:
            lines.append("")
            lines.append("```")
            lines.append(str(redacted))
            lines.append("```")
        lines.append("")

    return "\n".join(lines)


# -----------------------------
# HTML-Template (Mobile Ready, Single+Multi, Saved Queries)
# -----------------------------

INDEX_TEMPLATE = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>hAI.Truffelhog</title>
  <style>
    :root {
      --bg: #0b1020;
      --surface: #121a30;
      --surface-2: #1a2542;
      --text: #ecf3ff;
      --muted: #a8b4d1;
      --primary: #21d4c7;
      --accent: #ff5fa2;
      --line: #2f3d66;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at top right, rgba(33,212,199,0.18), transparent 28%),
        var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px 12px 32px;
    }
    .hero {
      display: grid;
      gap: 8px;
      margin-bottom: 16px;
      padding: 14px 16px;
      background: linear-gradient(
        135deg,
        rgba(33,212,199,0.12),
        rgba(255,95,162,0.08)
      );
      border: 1px solid var(--line);
      border-radius: 16px;
    }
    h1 { margin: 0; font-size: 1.6rem; }
    p, li { color: var(--muted); font-size: 0.95rem; }
    .tag {
      display: inline-block;
      padding: 4px 9px;
      border-radius: 999px;
      background: rgba(33,212,199,0.12);
      color: var(--primary);
      font-size: 0.8rem;
      margin-right: 6px;
    }
    .grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 14px;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px 14px 16px;
    }
    label {
      display: block;
      margin-bottom: 6px;
      font-weight: 600;
      color: var(--text);
      font-size: 0.9rem;
    }
    input, select, textarea, button {
      width: 100%;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: var(--surface-2);
      color: var(--text);
      font-size: 0.9rem;
    }
    textarea {
      min-height: 72px;
      resize: vertical;
      font-family: inherit;
    }
    button.primary {
      background: linear-gradient(90deg, var(--primary), #17a2ff);
      color: #041019;
      font-weight: 700;
      cursor: pointer;
      border: 0;
      margin-top: 10px;
    }
    .hint {
      font-size: 0.8rem;
      color: var(--muted);
      margin-top: 4px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      text-align: left;
      padding: 8px;
      border-bottom: 1px solid var(--line);
      font-size: 0.85rem;
    }
    a {
      color: var(--primary);
      text-decoration: none;
    }
    code {
      background: #11182d;
      padding: 2px 5px;
      border-radius: 6px;
      font-size: 0.85rem;
    }
    .tabs {
      display: flex;
      gap: 6px;
      margin-bottom: 10px;
    }
    .tab-btn {
      flex: 1;
      padding: 7px 10px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: var(--surface-2);
      color: var(--muted);
      font-size: 0.85rem;
    }
    .tab-btn.active {
      background: rgba(33,212,199,0.18);
      color: var(--primary);
      border-color: var(--primary);
    }
    .examples-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.85rem;
      margin-top: 6px;
    }
    .examples-link span {
      font-size: 1rem;
    }
    @media (max-width: 800px) {
      .wrap { padding: 12px 10px 24px; }
      .grid { grid-template-columns: 1fr; }
      .hero { padding: 12px 14px; }
      h1 { font-size: 1.4rem; }
    }
  </style>
  <script>
    function setMode(mode) {
      const single = document.getElementById('single-mode');
      const multi = document.getElementById('multi-mode');
      const tabSingle = document.getElementById('tab-single');
      const tabMulti = document.getElementById('tab-multi');

      if (mode === 'single') {
        single.style.display = 'block';
        multi.style.display = 'none';
        tabSingle.classList.add('active');
        tabMulti.classList.remove('active');
      } else {
        single.style.display = 'none';
        multi.style.display = 'block';
        tabSingle.classList.remove('active');
        tabMulti.classList.add('active');
      }
    }
  </script>
</head>
<body onload="setMode('single')">
  <div class="wrap">
    <section class="hero">
      <div>
        <span class="tag">🐗 Secret Scanning</span>
        <span class="tag">🌐 Web UI</span>
        <span class="tag">📱 Mobile Ready</span>
      </div>
      <h1>hAI.Truffelhog</h1>
      <p>Git-Repositories bequem im Browser mit TruffleHog scannen – Remote über HTTPS/SSH, auch vom Smartphone aus.</p>
      <a class="examples-link" href="/examples" target="_blank" rel="noopener">
        <span>📚</span> <span>Examples & CLI-Snippets anzeigen</span>
      </a>
    </section>

    <section class="grid">
      <div class="card">
        <h2>Neuen Scan starten</h2>

        <div class="tabs">
          <button id="tab-single" type="button" class="tab-btn" onclick="setMode('single')">
            Einzelnes Repo
          </button>
          <button id="tab-multi" type="button" class="tab-btn" onclick="setMode('multi')">
            Mehrere Repos / Saved
          </button>
        </div>

        <!-- Single Repo -->
        <form id="single-mode" method="post" action="/scan">
          <input type="hidden" name="mode" value="single">

          <label for="target">Git-URL</label>
          <input
            type="text"
            name="target"
            id="target"
            placeholder="https://github.com/user/repo oder git@github.com:user/repo.git"
            required
          >

          <label for="since" style="margin-top:10px;">Seit (optional)</label>
          <input
            type="text"
            name="since"
            id="since"
            placeholder="z. B. 2026-05-16T18:00:00 oder last_hours=2"
          >
          <div class="hint">
            Nutzt <code>--since</code> für zeitlich eingeschränkte Scans. Beispiel: <code>last_hours=2</code>.
          </div>

          <label for="results" style="margin-top:10px;">Ergebnis-Filter</label>
          <select name="results" id="results">
            <option value="verified,unknown">verified + unknown</option>
            <option value="verified">nur verified</option>
            <option value="unknown">nur unknown</option>
            <option value="all">alle</option>
          </select>

          <button class="primary" type="submit">🚀 Repo scannen</button>
        </form>

        <!-- Multi Repo -->
        <form id="multi-mode" method="post" action="/scan" style="display:none;">
          <input type="hidden" name="mode" value="multi">

          <label for="targets">Git-URLs (eine pro Zeile)</label>
          <textarea
            name="targets"
            id="targets"
            placeholder="https://github.com/user/repo-1
https://github.com/user/repo-2
git@github.com:user/repo-3.git"
          ></textarea>
          <div class="hint">
            Jede Zeile wird als eigenes Target gescannt.
          </div>

          <label for="since_multi" style="margin-top:10px;">Seit (optional)</label>
          <input
            type="text"
            name="since_multi"
            id="since_multi"
            placeholder="z. B. 2026-05-16T18:00:00 oder last_hours=2"
          >

          <label for="results_multi" style="margin-top:10px;">Ergebnis-Filter</label>
          <select name="results_multi" id="results_multi">
            <option value="verified,unknown">verified + unknown</option>
            <option value="verified">nur verified</option>
            <option value="unknown">nur unknown</option>
            <option value="all">alle</option>
          </select>

          <label for="query_name" style="margin-top:10px;">Query-Name (zum Speichern)</label>
          <input
            type="text"
            name="query_name"
            id="query_name"
            placeholder="z. B. GitHub-Repos-last2h"
          >
          <div class="hint">
            Wenn ein Name gesetzt ist, wird die Query gespeichert und kann später erneut ausgeführt werden.
          </div>

          <button class="primary" type="submit">🚀 Alle Repos scannen</button>
        </form>
      </div>

      <div class="card">
        <h2>Hinweise</h2>
        <p>
          hAI.Truffelhog läuft als Docker-Service in deinem LAN und nutzt
          <code>trufflehog git &lt;url&gt;</code>, um Remote-Repos zu scannen.
        </p>
        <ul>
          <li>🔒 Setze Tokens/SSH-Keys nur per ENV/Secrets.</li>
          <li>📦 Ergebnisse als JSON und Markdown im Volume <code>trufflehog-data</code>.</li>
          <li>⏱️ <code>--since</code> hilft, nur neue Commits zu scannen.</li>
          <li>📚 Weitere Beispiele unter <code>examples.md</code>.</li>
        </ul>

        <h3>Gespeicherte Queries</h3>
        {% if saved_queries %}
        <form method="post" action="/run_saved">
          <label for="saved_name">Query auswählen</label>
          <select name="saved_name" id="saved_name">
            {% for q in saved_queries %}
            <option value="{{ q['name'] }}">{{ q['name'] }}</option>
            {% endfor %}
          </select>
          <button class="primary" type="submit" style="margin-top:8px;">🚀 Saved Query ausführen</button>
        </form>
        {% else %}
        <p class="hint">Noch keine gespeicherten Queries vorhanden.</p>
        {% endif %}
      </div>
    </section>

    <section class="card" style="margin-top:16px;">
      <h2>Gespeicherte Ergebnisse</h2>
      {% if files %}
      <table>
        <tr><th>Datei</th><th>Download</th><th>Anzeige</th></tr>
        {% for f in files %}
        <tr>
          <td>{{ f }}</td>
          <td><a href="{{ url_for('download', filename=f) }}">⬇️ Download</a></td>
          <td>
            {% if f.endswith(".json") %}
            <a href="{{ url_for('view_report', filename=f) }}" target="_blank">📄 Anzeigen</a>
            {% else %}
            -
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </table>
      {% else %}
      <p>Noch keine Ergebnisse vorhanden.</p>
      {% endif %}
    </section>
  </div>
</body>
</html>
"""


# -----------------------------
# Routen
# -----------------------------

@app.route("/", methods=["GET"])
def index():
    files = sorted(os.listdir(DATA_DIR), reverse=True)
    saved_queries = load_saved_queries()
    return render_template_string(
        INDEX_TEMPLATE,
        files=files,
        saved_queries=saved_queries,
    )


@app.route("/scan", methods=["POST"])
def scan():
    mode = request.form.get("mode", "single")

    if mode == "multi":
        targets_raw = request.form.get("targets", "")
        results_mode = request.form.get("results_multi", "verified,unknown")
        since_raw = request.form.get("since_multi", "")
        query_name = request.form.get("query_name", "").strip()

        targets = [
            line.strip()
            for line in targets_raw.splitlines()
            if line.strip()
        ]

        # Query speichern
        if query_name and targets:
            queries = load_saved_queries()
            queries = [q for q in queries if q.get("name") != query_name]
            queries.append({
                "name": query_name,
                "mode": "multi",
                "targets": targets,
                "results": results_mode,
                "since": since_raw,
                "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            })
            save_saved_queries(queries)

    else:  # single
        target = request.form.get("target", "").strip()
        results_mode = request.form.get("results", "verified,unknown")
        since_raw = request.form.get("since", "")
        targets = [target] if target else []
        query_name = None

    if not targets:
        return redirect(url_for("index"))

    if results_mode == "all":
        results_arg = "verified,unknown,unverified"
    else:
        results_arg = results_mode

    since_value = parse_since(since_raw)

    for t in targets:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        safe_name = t.replace("://", "_").replace("/", "_").replace("@", "_")
        json_outfile = os.path.join(DATA_DIR, f"{timestamp}_git_{safe_name}.json")
        md_outfile = os.path.join(DATA_DIR, f"{timestamp}_git_{safe_name}.md")

        cmd = [
            "trufflehog",
            "git",
            t,
            f"--results={results_arg}",
            "--json",
        ]
        if since_value:
            cmd.append(f"--since={since_value}")

        try:
            completed = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=1800,
            )
            output = completed.stdout

            # JSON speichern
            with open(json_outfile, "w", encoding="utf-8") as f:
                f.write(output)

            # Markdown erzeugen
            meta = {
                "target": t,
                "mode": mode,
                "results": results_mode,
                "since": since_raw,
                "timestamp": timestamp,
            }
            md_text = render_markdown_report(output, meta)
            with open(md_outfile, "w", encoding="utf-8") as f:
                f.write(md_text)

        except Exception as e:
            error_text = str(e)
            with open(json_outfile, "w", encoding="utf-8") as f:
                f.write(error_text)
            with open(md_outfile, "w", encoding="utf-8") as f:
                f.write(f"# Fehler\n\n```text\n{error_text}\n```")

    return redirect(url_for("index"))


@app.route("/run_saved", methods=["POST"])
def run_saved():
    name = request.form.get("saved_name", "").strip()
    if not name:
        return redirect(url_for("index"))

    queries = load_saved_queries()
    q = next((x for x in queries if x.get("name") == name), None)
    if not q:
        return redirect(url_for("index"))

    mode = q.get("mode", "multi")
    targets = q.get("targets", [])
    results_mode = q.get("results", "verified,unknown")
    since_raw = q.get("since", "")

    if not targets:
        return redirect(url_for("index"))

    if results_mode == "all":
        results_arg = "verified,unknown,unverified"
    else:
        results_arg = results_mode

    since_value = parse_since(since_raw)

    for t in targets:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        safe_name = t.replace("://", "_").replace("/", "_").replace("@", "_")
        json_outfile = os.path.join(DATA_DIR, f"{timestamp}_git_{safe_name}.json")
        md_outfile = os.path.join(DATA_DIR, f"{timestamp}_git_{safe_name}.md")

        cmd = [
            "trufflehog",
            "git",
            t,
            f"--results={results_arg}",
            "--json",
        ]
        if since_value:
            cmd.append(f"--since={since_value}")

        try:
            completed = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=1800,
            )
            output = completed.stdout

            # JSON speichern
            with open(json_outfile, "w", encoding="utf-8") as f:
                f.write(output)

            # Markdown erzeugen
            meta = {
                "target": t,
                "mode": mode,
                "results": results_mode,
                "since": since_raw,
                "timestamp": timestamp,
            }
            md_text = render_markdown_report(output, meta)
            with open(md_outfile, "w", encoding="utf-8") as f:
                f.write(md_text)

        except Exception as e:
            error_text = str(e)
            with open(json_outfile, "w", encoding="utf-8") as f:
                f.write(error_text)
            with open(md_outfile, "w", encoding="utf-8") as f:
                f.write(f"# Fehler\n\n```text\n{error_text}\n```")

    return redirect(url_for("index"))


@app.route("/results/<path:filename>")
def download(filename):
    safe_path = os.path.join(DATA_DIR, filename)
    if not os.path.abspath(safe_path).startswith(os.path.abspath(DATA_DIR)):
        abort(403)
    if not os.path.isfile(safe_path):
        abort(404)
    return send_file(safe_path, as_attachment=True)


@app.route("/view/<path:filename>")
def view_report(filename):
    """
    Zeigt die passende .md-Datei als HTML an.
    Erwartung: filename ist ein JSON-Dateiname,
    die MD-Datei hat denselben basename mit .md-Endung.
    """
    base_json = os.path.join(DATA_DIR, filename)
    if not os.path.isfile(base_json):
        base_md = os.path.join(DATA_DIR, filename)
    else:
        base_md = base_json.rsplit(".", 1)[0] + ".md"

    if not os.path.isfile(base_md):
        return "Report nicht gefunden", 404

    with open(base_md, "r", encoding="utf-8") as f:
        md_content = f.read()

    html = (
        "<html><head><meta charset='utf-8'>"
        "<title>TruffleHog Report</title>"
        "<style>body{background:#0b1020;color:#ecf3ff;font-family:monospace;padding:16px;}"
        "a{color:#21d4c7;}</style>"
        "</head><body><pre style='white-space:pre-wrap;'>"
        + Markup.escape(md_content)
        + "</pre></body></html>"
    )
    return html


@app.route("/examples")
def examples():
    """
    Liefert die examples.md (falls vorhanden) als text/markdown.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    examples_path = os.path.join(base_dir, "..", "examples.md")
    if os.path.isfile(examples_path):
        return send_file(examples_path, mimetype="text/markdown")
    return "examples.md nicht gefunden", 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
