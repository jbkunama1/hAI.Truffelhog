import os
import subprocess
import datetime
from flask import Flask, request, redirect, url_for, render_template_string, send_file, abort

app = Flask(__name__)

DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

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
      font-family: Arial, sans-serif;
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: grid;
      gap: 16px;
      margin-bottom: 28px;
      padding: 24px;
      background: linear-gradient(
        135deg,
        rgba(33,212,199,0.12),
        rgba(255,95,162,0.08)
      );
      border: 1px solid var(--line);
      border-radius: 20px;
    }
    h1 { margin: 0; font-size: 2rem; }
    p, li { color: var(--muted); }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 700;
      color: var(--text);
    }
    input, select, button {
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: var(--surface-2);
      color: var(--text);
    }
    button {
      background: linear-gradient(90deg, var(--primary), #17a2ff);
      color: #041019;
      font-weight: 800;
      cursor: pointer;
      border: 0;
      margin-top: 10px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      text-align: left;
      padding: 10px;
      border-bottom: 1px solid var(--line);
    }
    a {
      color: var(--primary);
      text-decoration: none;
    }
    code {
      background: #11182d;
      padding: 2px 6px;
      border-radius: 6px;
    }
    .tag {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(33,212,199,0.12);
      color: var(--primary);
      font-size: 0.85rem;
      margin-right: 8px;
    }
    @media (max-width: 800px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div>
        <span class="tag">🐗 Secret Scanning</span>
        <span class="tag">🌐 Web UI</span>
        <span class="tag">🐳 Docker</span>
      </div>
      <h1>hAI.Truffelhog</h1>
      <p>Git-Repositories bequem im Browser mit TruffleHog scannen – Remote über HTTPS/SSH.</p>
    </section>

    <section class="grid">
      <div class="card">
        <h2>Neuen Remote-Scan starten</h2>
        <form method="post" action="/scan">
          <label for="target">Git-URL</label>
          <input
            type="text"
            name="target"
            id="target"
            placeholder="https://github.com/user/repo oder git@github.com:user/repo.git"
            required
          >

          <label for="results" style="margin-top:14px;">Ergebnis-Filter</label>
          <select name="results" id="results">
            <option value="verified,unknown">verified + unknown</option>
            <option value="verified">nur verified</option>
            <option value="unknown">nur unknown</option>
            <option value="all">alle</option>
          </select>

          <button type="submit">🚀 Remote-Scan starten</button>
        </form>
      </div>

      <div class="card">
        <h2>Hinweise</h2>
        <p>
          Dieser Service ruft <code>trufflehog git &lt;url&gt;</code> im Container auf.
          Die Ergebnisse werden als JSON im Daten-Volume gespeichert und können
          unten heruntergeladen werden.
        </p>
        <ul>
          <li>🔒 Setze Tokens/SSH-Keys nur per ENV/Secrets, nicht im Repo.</li>
          <li>📦 Ergebnisse persistent im Volume <code>trufflehog-data</code>.</li>
          <li>🏠 Für internes LAN / Homelab gedacht.</li>
        </ul>
      </div>
    </section>

    <section class="card" style="margin-top:20px;">
      <h2>Gespeicherte Ergebnisse</h2>
      {% if files %}
      <table>
        <tr><th>Datei</th><th>Download</th></tr>
        {% for f in files %}
        <tr>
          <td>{{ f }}</td>
          <td><a href="{{ url_for('download', filename=f) }}">⬇️ Download</a></td>
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

@app.route("/", methods=["GET"])
def index():
    files = sorted(os.listdir(DATA_DIR), reverse=True)
    return render_template_string(INDEX_TEMPLATE, files=files)

@app.route("/scan", methods=["POST"])
def scan():
    target = request.form.get("target", "").strip()
    results_mode = request.form.get("results", "verified,unknown")

    if not target:
        return redirect(url_for("index"))

    # Mapping für Ergebnisse
    if results_mode == "all":
        results_arg = "verified,unknown,unverified"
    else:
        results_arg = results_mode

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outfile = os.path.join(DATA_DIR, f"{timestamp}_git.json")

    cmd = [
        "trufflehog",
        "git",
        target,
        f"--results={results_arg}",
        "--format=json",
    ]

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1800,
        )
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(completed.stdout)
    except Exception as e:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(str(e))

    return redirect(url_for("index"))

@app.route("/results/<path:filename>")
def download(filename):
    safe_path = os.path.join(DATA_DIR, filename)
    if not os.path.abspath(safe_path).startswith(os.path.abspath(DATA_DIR)):
        abort(403)
    if not os.path.isfile(safe_path):
        abort(404)
    return send_file(safe_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
