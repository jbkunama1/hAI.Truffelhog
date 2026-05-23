# 🐗 hAI.Truffelhog

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-WebUI-000000?logo=flask&logoColor=white)
![TruffleHog](https://img.shields.io/badge/TruffleHog-Secret%20Scanning-orange)
![LAN](https://img.shields.io/badge/LAN-ready-blue)
![Network](https://img.shields.io/badge/Network-YourNetwork-8A2BE2)
![Status](https://img.shields.io/badge/Status-
[![Buy me a coffee](https://cdn.buymeacoffee.com/buttons/default-orange.png)](https://www.buymeacoffee.com/highfish)Ready%20to%20Hack-brightgreen)

<img src="./assets/logo-Truffel.png" alt="hAI.Truffelhog Logo" width="220">

**TruffleHog als Docker-Webservice mit einfacher Weboberfläche für Remote-Scans von GitHub/GitLab/GHCR im LAN**

</div>

---

## ✨ Überblick

**hAI.Truffelhog** ist ein Docker-basierter Webservice, der TruffleHog mit einer schlanken Flask-Weboberfläche kombiniert.  
Der Service läuft in deinem LAN, greift aber direkt per HTTPS/SSH auf Remote-Repositories (z. B. GitHub, GitLab, GHCR) zu.

Ziel: Aus dem Heimnetz oder Homelab bequem Secret-Scans starten, ohne TruffleHog lokal installieren zu müssen – alles zentral über einen Container und eine einfache Web-GUI.

---

## 🧠 Features

- 🐳 Docker-Setup mit `docker compose`
- 🌐 Einfache Weboberfläche mit Flask
- 🔎 Remote-Scan von Git-Repositories per URL (GitHub, GitLab, eigene Git-Server)
- 🛢️ Optionale Erweiterung für Docker-/GHCR-Image-Scans
- 💾 Persistente JSON-Ergebnisse im Volume
- 🏠 Betrieb im LAN (z. B. 127.0.0.1 auf `YourNetwork`)
- 🎨 Eigenes Branding mit Logo und farbiger UI

---

## 🗂️ Projektstruktur

```text
hAI.Truffelhog/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── assets/
│   └── logo-Truffel.png
└── trufflehog-web/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py
```

---

## 🚀 Voraussetzungen

- Docker Engine + Docker Compose Plugin
- Externes Docker-Netzwerk `YourNetwork`
- Frei verfügbare IP `127.0.0.1` im Docker-Netz
- Internetzugang für den Container (z. B. Docker-Bridge/NAT)
- Optional:
  - GitHub-/GitLab-Personal-Access-Tokens als ENV-Variablen
  - SSH-Keys, falls du per SSH auf private Repos zugreifen willst

---

## ⚙️ Einrichtung

### 1. Repository klonen

```bash
git clone https://github.com/DEIN-USERNAME/hAI.Truffelhog.git
cd hAI.Truffelhog
```

### 2. Docker-Netzwerk prüfen oder anlegen

Das Compose-Setup erwartet ein **externes** Docker-Netzwerk `YourNetwork` mit passendem Subnetz.

Beispiel:

```bash
docker network create \
  --driver bridge \
  --subnet 192.168.178.0/24 \
  YourNetwork
```

> Achtung: Verwende ein Subnetz, das zu deiner bestehenden Docker- und Host-Konfiguration passt.  
> Falls bereits ein `YourNetwork` existiert, diesen Schritt überspringen.

### 3. Optionale Umgebungsvariablen (.env)

```bash
cp .env.example .env
```

In `.env` kannst du z. B. Tokens oder Pfade hinterlegen:

```env
REPO_BASE_PATH=/srv/git          # aktuell nicht genutzt (nur Remote-Scans)
RESULTS_PATH=/app/data
WEB_PORT=5000
# GITHUB_TOKEN=...
# GITLAB_TOKEN=...
```

### 4. Container bauen und starten

```bash
docker compose up -d --build
```

Danach erreichst du die Weboberfläche im LAN unter:

```text
http://127.0.0.1:5000
```

---

## 🖥️ Nutzung

### GitHub-/GitLab-Repo scannen

1. Im Browser `http://127.0.0.1:5000` aufrufen.
2. Formular ausfüllen:
   - Scan-Typ: `Git`
   - Ziel-URL:
     - z. B. `https://github.com/user/repo`
     - oder `git@github.com:user/repo.git`
   - Ergebnis-Filter:
     - `verified,unknown` (Standard)
     - oder `verified` / `unknown` / `all`

Die Anwendung ruft intern TruffleHog mit:

```bash
trufflehog git <deine-url> --results=... --format=json
```

auf und speichert die Ausgabe als JSON-Datei in einem Volume. In der Tabelle unter „Gespeicherte Ergebnisse“ kannst du die Dateien herunterladen.

### (Optional) Docker-/GHCR-Image-Scans

Wenn du das Skript erweiterst, kannst du z. B. `trufflehog docker --image ghcr.io/org/image:tag` ausführen.  
Der Container braucht dafür Netzwerkzugriff auf `ghcr.io` und ggf. Token/Logins.

---

## 🐳 docker-compose.yml (Beispiel)

```yaml
version: "3.9"

services:
  trufflehog-web:
    build: ./trufflehog-web
    container_name: trufflehog-web
    restart: unless-stopped
    networks:
      YourNetwork:
        ipv4_address: 127.0.0.1
    volumes:
      - trufflehog-data:/app/data
    ports:
      - "5000:5000"
    environment:
      TZ: "Europe/Berlin"
      # Optional:
      # GITHUB_TOKEN: "dein-token"
      # GITLAB_TOKEN: "dein-token"

networks:
  YourNetwork:
    external: true

volumes:
  trufflehog-data:
```

---

## 🧰 Dockerfile

```Dockerfile
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \
    | sh -s -- -b /usr/local/bin

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "app.py"]
```

---

## 🧾 MIT Lizenz

Dieses Repository steht unter der MIT-Lizenz.  
Damit ist die Nutzung, das Kopieren, Modifizieren, Zusammenführen, Veröffentlichen und Verteilen erlaubt, solange der Lizenztext beibehalten wird.

---

## 🔐 Sicherheitshinweise

- Der Service sollte nur im internen Netz betrieben werden.
- Plane Authentifizierung (z. B. Reverse Proxy + Basic Auth), falls du das UI in sensiblere Umgebungen stellst.
- Werden echte Secrets gefunden:
  - **Schlüssel rotieren** (neu erzeugen), nicht nur aus dem Repo löschen.
  - Git-Historie im Blick behalten (Rewriting/Rewriting-Strategien prüfen).
- Tokens nur per ENV/Secrets, nie direkt ins Repo commiten.

---

## 🛠️ Roadmap

- [ ] Direktanzeige der Findings im Browser (Parsing des JSON)
- [ ] Filter nach `verified`, `unknown`, `unverified` in der UI
- [ ] Reverse-Proxy-Variante mit Authentifizierung
- [ ] CSV/HTML-Export für Reports
- [ ] Mehrsprachige UI (DE/EN)

---

## 🤝 Hinweis

Dieses Repository ist eine eigenständige Web-Hülle um TruffleHog und **kein** offizielles Projekt von Truffle Security.  
TruffleHog selbst ist das zugrunde liegende Secret-Scanning-Tool.
