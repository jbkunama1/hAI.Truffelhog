# 📚 hAI.Truffelhog – Examples

Dieses Dokument sammelt typische TruffleHog-Kommandos, wie du sie im Container oder direkt in deinem Setup verwenden kannst. Grundlage ist das `git`-Subcommand mit Remote-Repositories.

---

## 1. Basis: Remote-Git-Repository scannen

### 1.1 Einfacher Scan eines öffentlichen GitHub-Repos

```bash
trufflehog git https://github.com/trufflesecurity/test_keys
```

- Klont das Repo temporär.
- Scannt die Git-Historie.
- Gibt Ergebnisse im Standardformat auf `stdout` aus.

### 1.2 Scan eines privaten Repos (HTTPS)

```bash
trufflehog git https://github.com/DEIN-USER/dein-privates-repo
```

Voraussetzungen:

- Ggf. `GITHUB_TOKEN` als ENV im Container gesetzt.
- Repo ist mit diesem Token lesbar.

### 1.3 Scan mit SSH-URL

```bash
trufflehog git git@github.com:DEIN-USER/dein-repo.git
```

Voraussetzungen:

- SSH-Key im Container vorhanden (oder per Volume/Security-Setup eingebunden).
- SSH-Konfiguration erlaubt Zugriff auf das Repo.

---

## 2. Ausgabeformat: JSON

### 2.1 JSON-Output für weiterführende Verarbeitung

```bash
trufflehog git https://github.com/trufflesecurity/test_keys \
  --format=json
```

- Ideal für `jq`, eigene Scripts oder Log-Pipelines.
- Wird im hAI.Truffelhog-Webservice auch so genutzt, um JSON-Dateien zu speichern.

### 2.2 Nur verifizierte Findings

```bash
trufflehog git https://github.com/trufflesecurity/test_keys \
  --results=verified \
  --format=json
```

- Filtert auf verifizierte Secrets (minimiert Noise).
- Praktisch für „ernste“ Reviews ohne zu viele False Positives.

---

## 3. Branch-Filter

### 3.1 Nur einen bestimmten Branch scannen

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --branch main
```

- Beschränkt den Scan auf `main`.
- Kann mehrfach wiederholt werden für andere Branches (`--branch develop`, etc.).

### 3.2 Mehrere Branches explizit scannen (nacheinander)

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --branch main \
  --format=json > results-main.json

trufflehog git https://github.com/DEIN-USER/dein-repo \
  --branch develop \
  --format=json > results-develop.json
```

- Duplizierte Scans mit unterschiedlichem Branch.
- Gute Grundlage für Vergleich / Diff-Auswertungen.

---

## 4. Zeitliche Einschränkung: --since

### 4.1 Nur Commits seit einem bestimmten Datum

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --since="2024-01-01" \
  --format=json
```

- Scan nur für Commits ab 1. Januar 2024.
- Sinnvoll für regelmäßige, inkrementelle Scans.

### 4.2 Kombination mit Branch-Filter

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --branch main \
  --since="2024-06-01" \
  --format=json
```

- „Nur main, nur neue Commits seit Juni 2024“.

---

## 5. Ergebnis-Filter: verified / unknown / unverified

### 5.1 Standard (verified + unknown)

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --results=verified,unknown \
  --format=json
```

- Entspricht dem Standard-Setup in hAI.Truffelhog.
- Zeigt verifizierte Secrets + Funde, die nicht eindeutig geprüft werden konnten.

### 5.2 Nur unknown

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --results=unknown \
  --format=json
```

- Wenn du z. B. nur potenzielle Kandidaten sammeln willst.

### 5.3 Alle Ergebnisse

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --results=verified,unknown,unverified \
  --format=json
```

- Volle „Noise“-Breite, nützlich für Analyse/Tests.

---

## 6. Beispiele im Docker-Container (ohne WebUI)

Wenn du TruffleHog direkt im Container verwenden willst (z. B. über `docker exec`), kannst du folgende Muster nutzen.

### 6.1 Interaktiv im hAI.Truffelhog-Container

```bash
docker exec -it trufflehog-web bash

# im Container:
trufflehog git https://github.com/trufflesecurity/test_keys \
  --results=verified,unknown \
  --format=json
```

### 6.2 Eigenes Script / Cronjob

Beispiel: Täglicher Scan eines bestimmten Repos, der Ergebnisse im Container in `/app/data` ablegt:

```bash
docker exec trufflehog-web \
  sh -c 'trufflehog git https://github.com/DEIN-USER/dein-repo \
    --results=verified,unknown \
    --format=json > /app/data/$(date +%Y%m%d-%H%M%S)_git.json'
```

---

## 7. Nützliche Kombinationen

### 7.1 Konzentrierter „Quick Scan“ (neuere Commits, JSON, verified-only)

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --since="2025-01-01" \
  --results=verified \
  --format=json
```

### 7.2 „Deep Scan“ (gesamtes Repo, alle Ergebnisse)

```bash
trufflehog git https://github.com/DEIN-USER/dein-repo \
  --results=verified,unknown,unverified \
  --format=json
```

---

## 8. Integration mit hAI.Truffelhog-WebUI

Die WebUI führt Befehle nach folgendem Muster aus:

```bash
trufflehog git <target-url> \
  --results=<deine-auswahl> \
  --format=json
```

- Der `<target-url>`-Wert kommt aus dem HTML-Formular.
- Die Ergebnisse werden als JSON-Datei unter `/app/data` gespeichert.
- Die Weboberfläche zeigt alle gespeicherten Dateien in einer Liste und bietet einen Download-Link.

---

## 9. Tipps für deinen Homelab-Einsatz

- Lege dir eine kleine Liste mit Standard-Targets an (z. B. deine wichtigsten GitHub-Repos) und teste regelmäßig.
- Nutze `--since`, um regelmäßige inkrementelle Scans zu fahren, statt jedes Mal die komplette Historie zu scannen.
- Für sensible Setups: Tokens und SSH-Keys nur über ENV/Docker Secrets, nie direkt im Repo versionieren.
