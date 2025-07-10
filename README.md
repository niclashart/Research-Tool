# AI Research Hub 🤖📚

Ein intelligentes Forschungs-Tool, das automatisch KI-relevante Artikel aus verschiedenen Quellen sammelt, zusammenfasst und analysiert. Mit integriertem AI-Chat-Assistenten für erweiterte Recherche und Analyse.

## 🌟 Features

### 📊 Dashboard
- **Echtzeit-Übersicht** über aktuelle KI-Forschung und News
- **Interaktive Diagramme** für Trends und Quellen-Statistiken
- **Top-Keywords** und Trending-Topics-Analyse
- **Responsive Design** mit Dark/Light Mode

### 🔍 Multi-Source Datensammlung
- **ArXiv**: Aktuelle KI-Forschungsarbeiten mit Zitationsstilen
- **TechCrunch**: KI-relevante Tech-News
- **VentureBeat**: Startup- und Business-KI-News
- **Stanford AI Blog**: Akademische KI-Insights
- **The Verge**: Tech-Journalismus zu KI-Themen
- **The Hacker News**: Cybersecurity mit KI-Fokus

### 🤖 AI-Chat-Assistent
- **OpenAI-Integration** für intelligente Artikel-Analyse
- **Kontextuelle Antworten** basierend auf gesammelten Artikeln
- **Mehrsprachige Unterstützung** (DE/EN/FR/ZH)
- **Persistente Chat-Historie**

### ⚙️ Erweiterte Funktionen
- **Automatische Relevanz-Bewertung** mit KI-Keywords
- **Flexible Export-Optionen** (Word, JSON, Text)
- **Caching-System** für Performance-Optimierung
- **Benutzerfreundliche Einstellungen**

## 🚀 Installation

### Voraussetzungen
- Python 3.8+
- Google Chrome (für Web-Scraping)
- OpenAI API Key

### 1. Repository klonen
```bash
git clone https://github.com/yourusername/ai-research-hub.git
cd ai-research-hub
```

### 2. Virtual Environment erstellen
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen konfigurieren
Erstellen Sie eine `.env`-Datei im Projektverzeichnis:
```env
# OpenAI API Key (erforderlich)
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Weitere Einstellungen
FLASK_SECRET_KEY=your_secret_key_here
OPENAI_MODEL=gpt-3.5-turbo
THEME=light
DEFAULT_SOURCES=arxiv,techcrunch,venturebeat
MAX_RESULTS=10
DB_PATH=research_data.db
```

### 5. Anwendung starten
```bash
python app.py
```

Die Anwendung ist dann unter `http://localhost:5000` verfügbar.

## 📱 Verwendung

### 1. Quellen konfigurieren
- Navigieren Sie zur **Sources**-Seite
- Wählen Sie gewünschte Datenquellen aus
- Konfigurieren Sie Parameter (max. Artikel, ArXiv-Kategorien, etc.)
- Klicken Sie auf "Daten abrufen"

### 2. Dashboard analysieren
- **Aktuelle Artikel** durchstöbern
- **Trend-Diagramme** analysieren
- **Top-Keywords** verfolgen
- **Quellen-Statistiken** einsehen

### 3. AI-Chat nutzen
- Stellen Sie Fragen zu gesammelten Artikeln
- Lassen Sie sich Trends erklären
- Vergleichen Sie verschiedene Forschungsansätze
- Exportieren Sie Chat-Verläufe

### 4. Berichte exportieren
- Word-Dokumente mit Zusammenfassungen
- JSON-Daten für weitere Analyse
- Verschiedene Zitationsstile (APA, MLA, Chicago, BibTeX)

## 🛠️ Technische Details

### Architektur
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Data Layer    │
│   (HTML/JS)     │◄──►│   (Flask)       │◄──►│   (SQLite)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   AI Services   │
                       │   (OpenAI)      │
                       └─────────────────┘
```

### Hauptkomponenten
- **app.py**: Haupt-Flask-Anwendung
- **scrapers/**: Datensammlung von verschiedenen Quellen
- **templates/**: Frontend-Templates
- **static/**: CSS, JavaScript, Assets
- **db_manager.py**: Datenbankoperationen
- **relevance.py**: KI-Relevanz-Analyse

### Datenbank Schema
```sql
-- Artikel-Tabelle
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    summary TEXT,
    content TEXT,
    pub_date TEXT,
    keywords TEXT,
    relevance_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📦 Projektstruktur

```
ai-research-hub/
├── app.py                 # Haupt-Flask-Anwendung
├── web_app.py            # Alternative Flask-App
├── requirements.txt      # Python-Dependencies
├── .env                  # Umgebungsvariablen
├── .gitignore           # Git-Ignore-Datei
├── README.md            # Diese Datei
├── LICENSE              # MIT-Lizenz
│
├── scrapers/            # Datensammlung
│   ├── arxiv_scraper.py
│   ├── techcrunch.py
│   ├── venture_beat.py
│   ├── stanford_ai.py
│   ├── theverge.py
│   └── thn.py
│
├── templates/           # HTML-Templates
│   ├── layout.html
│   ├── index.html
│   ├── dashboard.html
│   ├── sources.html
│   ├── chat.html
│   └── settings.html
│
├── static/              # Frontend-Assets
│   ├── css/
│   ├── js/
│   └── images/
│
├── cache/               # Zwischenspeicher
├── summary/             # Export-Dateien
└── logs/                # Log-Dateien
```

## 🔧 Konfiguration

### Scraper-Einstellungen
```python
# Maximale Artikel pro Quelle
MAX_ARTICLES = 10

# ArXiv-Kategorien
ARXIV_CATEGORIES = ['cs.AI', 'cs.LG', 'cs.CL', 'cs.CV']

# Cache-Verhalten
CACHE_DURATION = 3600  # 1 Stunde
```

### OpenAI-Einstellungen
```python
# Verwendetes Modell
OPENAI_MODEL = 'gpt-3.5-turbo'

# Max. Tokens pro Anfrage
MAX_TOKENS = 500

# Temperatur (Kreativität)
TEMPERATURE = 0.7
```

## 🐛 Troubleshooting

### Häufige Probleme

#### 1. OpenAI API-Fehler
```
Error: OpenAI API key not set
```
**Lösung**: Setzen Sie `OPENAI_API_KEY` in der `.env`-Datei

#### 2. Chrome-Driver-Fehler
```
Error: ChromeDriver not found
```
**Lösung**: Installieren Sie Chrome und aktualisieren Sie den WebDriver:
```bash
pip install --upgrade webdriver-manager
```

#### 3. Keine Daten vom Dashboard
```
Error: No sources selected
```
**Lösung**: 
- Gehen Sie zur Sources-Seite
- Wählen Sie mindestens eine Quelle aus
- Klicken Sie auf "Daten abrufen"

#### 4. Langsame Performance
**Lösung**: 
- Reduzieren Sie `MAX_ARTICLES` in den Einstellungen
- Leeren Sie den Cache-Ordner
- Prüfen Sie Ihre Internetverbindung

## 📈 Performance-Optimierung

### Caching-Strategien
- **Artikel-Cache**: 1 Stunde für bereits verarbeitete Artikel
- **Database-Cache**: Lokale SQLite-Datenbank für schnelle Abfragen
- **API-Cache**: Rate-Limiting für externe APIs

### Monitoring
```python
# Logging-Konfiguration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
```

## 🤝 Contributing

Beiträge sind willkommen! Bitte beachten Sie:

1. **Fork** das Repository
2. **Erstellen** Sie einen Feature-Branch (`git checkout -b feature/amazing-feature`)
3. **Committen** Sie Ihre Änderungen (`git commit -m 'Add amazing feature'`)
4. **Push** zum Branch (`git push origin feature/amazing-feature`)
5. **Erstellen** Sie eine Pull Request

### Entwicklungsrichtlinien
- Verwenden Sie aussagekräftige Commit-Messages
- Fügen Sie Tests für neue Features hinzu
- Dokumentieren Sie Ihre Änderungen
- Befolgen Sie PEP 8 für Python-Code

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.


*Dieses Tool wurde entwickelt, um Forschern und KI-Enthusiasten zu helfen, mit den neuesten Entwicklungen in der Künstlichen Intelligenz Schritt zu halten.*