# 🐗 hAI.Truffelhog

<div align="center">

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-WebUI-000000?logo=flask&logoColor=white)
![TruffleHog](https://img.shields.io/badge/TruffleHog-Secret%20Scanning-orange)
![LAN](https://img.shields.io/badge/LAN-192.168.178.11-blue)
![Network](https://img.shields.io/badge/Network-highfishNetwork-8A2BE2)
![Status](https://img.shields.io/badge/Status-Ready%20to%20Hack-brightgreen)

<img src="logo-Truffel.png" alt="hAI.Truffelhog Logo" width="220">

**TruffleHog als Docker-Webservice mit einfacher Weboberfläche für lokale Repo-Scans im LAN**

</div>

---

## ✨ Überblick

**hAI.Truffelhog** ist ein kleines GitHub-Projekt, das TruffleHog als Docker-Container mit einer einfachen Flask-Weboberfläche bereitstellt. TruffleHog unterstützt das Scannen von Git-Repositories, Dateisystemen, Container-Images und weiteren Quellen nach potenziellen Secrets.

Die Lösung in diesem Repository fokussiert sich auf einen praxistauglichen lokalen Einsatz im Heimnetz oder Homelab: Container starten, Verzeichnisse mit Repos read-only mounten, Scans im Browser auslösen und JSON-Ergebnisse herunterladen.

---

## 🧠 Features

- 🐳 Docker-Setup mit `docker compose`
- 🌐 Einfache Weboberfläche mit Flask
- 🔎 Scan von lokalen Repos oder Git-URLs
- 💾 Persistente JSON-Ergebnisse im Volume
- 🛡️ Read-only Mount für Repo-Verzeichnisse
- 🎨 Eigenes Branding mit Logo und GitHub-README
- 🏠 Ausgelegt für dein LAN / Homelab

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
│   └── logo.svg
└── trufflehog-web/
    ├── Dockerfile
    ├── requirements.txt
    └── app.py
```

---

## 🚀 Voraussetzungen

- Docker Engine + Docker Compose Plugin
- Vorhandenes Docker-Netzwerk `highfishNetwork`
- Frei verfügbare IP `192.168.178.11`
- Lokale Git-Repositories, z. B. unter `/srv/git`

TruffleHog stellt ein offizielles Container-Image bereit und dokumentiert Docker-basierte Nutzung für Scans.

---

## ⚙️ Einrichtung

### 1. Repository klonen

```bash
git clone https://github.com/DEIN-USERNAME/hAI.Truffelhog.git
cd hAI.Truffelhog
```

### 2. Netzwerk prüfen

Das Compose-Setup erwartet ein **externes** Docker-Netzwerk namens `highfishNetwork`.

Falls es noch nicht existiert, kannst du es beispielhaft so anlegen:

```bash
docker network create \
  --driver bridge \
  --subnet 192.168.178.0/24 \
  highfishNetwork
```

> Achtung: Nur verwenden, wenn dieses Subnetz zu deiner Docker- und Host-Konfiguration passt.

### 3. Compose-Datei anpassen

Standardmäßig ist Folgendes vorgesehen:

- Netzwerk: `highfishNetwork`
- Container-IP: `192.168.178.11`
- Repo-Mount: `/srv/git:/repos:ro`
- Weboberfläche: Port `5000`

Wenn deine Repos woanders liegen, passe den Volume-Mount in `docker-compose.yml` an.

### 4. Container bauen und starten

```bash
docker compose up -d --build
```

Danach erreichst du die Oberfläche im LAN unter:

```text
http://192.168.178.11:5000
```

---

## 🖥️ Nutzung

### Scan eines lokalen Repos

Im Webformular:

- Modus: `Filesystem`
- Ziel: `/repos/mein-repo`

### Scan eines Git-Repos per URL

Im Webformular:

- Modus: `Git`
- Ziel: `https://github.com/user/repo`

Die Anwendung ruft intern die TruffleHog-Subcommands `filesystem` oder `git` auf und speichert die Ausgabe als JSON-Datei. Das offizielle Projekt dokumentiert diese Scan-Modi und die Verwendung im Docker-Kontext.

---

## 🔐 Sicherheitshinweise

- Das Repo-Verzeichnis wird **read-only** in den Container gemountet.
- Die Weboberfläche ist bewusst einfach gehalten und sollte nur im internen Netz betrieben werden.
- Für produktiven Einsatz sind Reverse Proxy, Basic Auth und ggf. IP-Restriktionen sinnvoll.
- Werden echte Secrets gefunden, sollten diese rotiert und nicht nur aus dem Repository entfernt werden, da Git-Historie betroffen sein kann.

---

## 🧪 Beispielbefehle ohne Weboberfläche

Direkt im Container oder mit offiziellem Image:

```bash
docker run --rm trufflesecurity/trufflehog git https://github.com/trufflesecurity/trufflehog
```

```bash
docker run --rm \
  -v /srv/git/mein-repo:/repo:ro \
  trufflesecurity/trufflehog git file:///repo
```

Die offizielle Projektseite und das Docker-Image beschreiben diese Nutzungsart für Git-Scans.

---

## 🐳 docker-compose.yml

```yaml
version: "3.9"

services:
  trufflehog-web:
    build: ./trufflehog-web
    container_name: trufflehog-web
    restart: unless-stopped
    networks:
      highfishNetwork:
        ipv4_address: 192.168.178.11
    volumes:
      - /srv/git:/repos:ro
      - trufflehog-data:/app/data
    ports:
      - "5000:5000"

networks:
  highfishNetwork:
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

Das offizielle Repository stellt das Install-Script bereit; zusätzlich existiert ein offizielles Docker-Image für containerisierte Nutzung.

---

## 🧾 MIT Lizenz

Dieses Repository enthält eine MIT-Lizenz und ist damit offen für private und angepasste Nutzung. Die MIT-Lizenz erlaubt Nutzung, Kopieren, Modifikation, Zusammenführung, Veröffentlichung und Weitergabe unter Beibehaltung des Lizenzhinweises.

---

## 🛠️ Roadmap

- [ ] Direktanzeige der Findings im Browser
- [ ] Filter nach `verified`, `unknown`, `unverified`
- [ ] Reverse-Proxy-Variante mit Authentifizierung
- [ ] CSV/HTML-Export für Reports
- [ ] Mehrsprachige UI

---

## 🤝 Hinweis

Dieses Repository ist eine eigenständige Web-Verpackung um TruffleHog und kein offizielles Projekt von Truffle Security. TruffleHog selbst ist das zugrunde liegende Secret-Scanning-Tool.
