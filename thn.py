import feedparser
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
from datetime import datetime, timedelta, timezone
import time
import key_manager
import os
import json

client = OpenAI(api_key=key_manager.get_openai_key())

# RSS Feed URL - Using the direct site feed instead of Feedburner
THN_FEED_URL = "https://thehackernews.com/feeds/posts/default?alt=rss"

# Maximale Anzahl an Artikeln, die verarbeitet werden sollen
MAX_ARTICLES = 10

# Cache-Verzeichnis für verarbeitete Artikel
CACHE_DIR = "cache"
THN_CACHE_FILE = os.path.join(CACHE_DIR, "thn_processed_articles.json")

# Stellen Sie sicher, dass das Cache-Verzeichnis existiert
os.makedirs(CACHE_DIR, exist_ok=True)

# Laden des Caches mit bereits verarbeiteten Artikeln
def load_processed_articles():
    if os.path.exists(THN_CACHE_FILE):
        try:
            with open(THN_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden des TheHackerNews-Artikel-Caches: {e}")
    return {"processed_urls": [], "last_update": datetime.now().isoformat()}

# Aktualisieren des Caches mit neu verarbeiteten Artikeln
def save_processed_articles(processed_urls):
    cache_data = {
        "processed_urls": processed_urls,
        "last_update": datetime.now().isoformat()
    }
    try:
        with open(THN_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Fehler beim Speichern des TheHackerNews-Artikel-Caches: {e}")

# Keywords to detect AI-related articles - expanded list
AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "neural network", 
    "deep learning", "OpenAI", "GPT", "LLM", "AI", "algorithm",
    "chatbot", "transformer", "language model", "generative", 
    "autonomous system", "computer vision"
]

def fetch_thn_articles():
    feed = feedparser.parse(THN_FEED_URL)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=72)  # Extended to 3 days

    articles = []
    for entry in feed.entries:
        try:
            # Different feeds might have different date formats/fields
            published = None
            if hasattr(entry, 'published_parsed'):
                published = datetime(*entry.published_parsed[:6]).replace(tzinfo=None)
            elif hasattr(entry, 'updated_parsed'):
                published = datetime(*entry.updated_parsed[:6]).replace(tzinfo=None)
            else:
                # If no date available, assume it's recent
                published = datetime.now()
            
            if published < cutoff:
                continue

            title = entry.title
            
            # Get the correct link - different feeds structure links differently
            if hasattr(entry, 'link'):
                link = entry.link
            elif 'links' in entry and len(entry.links) > 0:
                link = entry.links[0].href
            else:
                print(f"⚠️ Keine Link für Eintrag gefunden: {title}")
                continue
                
            # Extract the actual content
            if hasattr(entry, 'content'):
                html_content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                html_content = entry.summary
            else:
                # Fetch the full article if content not in feed
                try:
                    response = requests.get(link, timeout=10)
                    soup = BeautifulSoup(response.text, "html.parser")
                    article_body = soup.find('div', {'class': 'post-body'})
                    html_content = str(article_body) if article_body else ""
                except Exception as e:
                    print(f"⚠️ Fehler beim Laden des Artikels {title}: {e}")
                    html_content = ""

            # Extract text from HTML
            text = BeautifulSoup(html_content, "html.parser").get_text()
            
            # Check if AI related but don't skip if not
            ai_related, matched_keywords = is_ai_related_with_details(text)
            if not ai_related:
                print(f"ℹ️ Artikel nicht KI-bezogen, aber wird trotzdem verarbeitet: {title}")
            
            summary = summarize_article(text)

            articles.append({
                "Titel": title,
                "Link": link,
                "Zusammenfassung": summary,
                "KI_bezogen": ai_related,
                "KI_Keywords": ", ".join(matched_keywords) if matched_keywords else "Keine",
                "Datum": published.strftime("%Y-%m-%d")
            })

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"⚠️ Fehler beim Verarbeiten eines Artikels: {e}")

    return articles if articles else None

def is_ai_related_with_details(text):
    lower_text = text.lower()
    matched_keywords = []
    
    for kw in AI_KEYWORDS:
        if kw.lower() in lower_text:
            matched_keywords.append(kw)
            
    return len(matched_keywords) > 0, matched_keywords

def is_ai_related(text):
    related, _ = is_ai_related_with_details(text)
    return related

def summarize_article(text):
    if not text or len(text.strip()) < 100:
        return "Nicht genügend Text für eine Zusammenfassung."
        
    prompt = (
        "Fasse den folgenden Artikel auf Deutsch in einem kurzen Absatz zusammen. "
        "Fokussiere auf die wichtigsten Informationen, insbesondere wenn es Bezug zu KI hat:\n\n"
        f"{text[:3000]}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "Du bist ein hilfreicher Assistent, der sicherheitsrelevante Artikel zusammenfasst."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
            stop=["\n\n"]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Fehler bei der Zusammenfassung: {e}")
        return "Zusammenfassung fehlgeschlagen."

def main_thn():
    print("📡 Starte TheHackerNews Scraper...")
    
    # Laden der bereits verarbeiteten Artikel
    cache_data = load_processed_articles()
    processed_urls = set(cache_data.get("processed_urls", []))
    
    feed = feedparser.parse(THN_FEED_URL)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=72)
    
    print(f"📊 THN Feed enthält {len(feed.entries)} Einträge")
    
    articles = []
    new_articles = []
    
    # Alle verfügbaren Artikel sammeln
    for entry in feed.entries:
        try:
            # Different feeds might have different date formats/fields
            published = None
            if hasattr(entry, 'published_parsed'):
                published = datetime(*entry.published_parsed[:6]).replace(tzinfo=None)
            elif hasattr(entry, 'updated_parsed'):
                published = datetime(*entry.updated_parsed[:6]).replace(tzinfo=None)
            else:
                # If no date available, assume it's recent
                published = datetime.now()
            
            if published < cutoff:
                continue

            title = entry.title
            
            # Get the correct link - different feeds structure links differently
            if hasattr(entry, 'link'):
                link = entry.link
            elif 'links' in entry and len(entry.links) > 0:
                link = entry.links[0].href
            else:
                print(f"⚠️ Keine Link für Eintrag gefunden: {title}")
                continue
            
            # Nur neue Artikel hinzufügen
            if link not in processed_urls:
                new_articles.append({
                    "title": title,
                    "link": link,
                    "published": published
                })
        except Exception as e:
            print(f"⚠️ Fehler beim Verarbeiten eines Eintrags: {e}")
    
    if not new_articles:
        print("✓ Alle verfügbaren TheHackerNews Artikel wurden bereits verarbeitet.")
        return []
    
    print(f"✓ {len(new_articles)} neue TheHackerNews Artikel zum Verarbeiten gefunden.")
    
    # Begrenzen der Anzahl zu verarbeitender Artikel
    articles_to_process = new_articles[:MAX_ARTICLES]
    total_articles = len(articles_to_process)
    articles_processed = 0
    
    for idx, article in enumerate(articles_to_process, 1):
        print(f"\n📄 Verarbeite Artikel [{idx}/{total_articles}]: {article['title']}")
        
        try:
            # HTML-Inhalt des Artikels laden
            try:
                response = requests.get(article['link'], timeout=10)
                soup = BeautifulSoup(response.text, "html.parser")
                article_body = soup.find('div', {'class': 'post-body'})
                html_content = str(article_body) if article_body else ""
            except Exception as e:
                print(f"⚠️ Fehler beim Laden des Artikels: {e}")
                html_content = ""
            
            # Text aus HTML extrahieren
            text = BeautifulSoup(html_content, "html.parser").get_text()
            
            # Auf KI-Bezug prüfen
            ai_related, matched_keywords = is_ai_related_with_details(text)
            if ai_related:
                print(f"✅ Artikel ist KI-bezogen. Gefundene Keywords: {', '.join(matched_keywords)}")
            else:
                print(f"ℹ️ Artikel nicht KI-bezogen, wird trotzdem verarbeitet.")
            
            # Artikel zusammenfassen
            summary = summarize_article(text)
            
            # Artikel dem Ergebnis hinzufügen
            articles.append([
                article['title'],
                article['link'],
                summary,
                article['published'].strftime('%Y-%m-%d')
            ])
            
            # URL als verarbeitet markieren
            processed_urls.add(article['link'])
            articles_processed += 1
            
            # Speichere regelmäßig den Cache
            if articles_processed % 3 == 0 or idx == total_articles:
                save_processed_articles(list(processed_urls))
                
        except Exception as e:
            print(f"❌ Fehler bei der Verarbeitung des Artikels: {e}")
        
        time.sleep(1)  # Rate limiting
    
    # Abschließendes Speichern des Caches
    save_processed_articles(list(processed_urls))
    print(f"✅ TheHackerNews Scraping abgeschlossen. {articles_processed} Artikel verarbeitet.")
    
    return articles if articles else []

# Testlauf
if __name__ == "__main__":
    result = main_thn()
    if result:
        for r in result:
            # Array-Format: [title, link, summary, date]
            print(f"📰 {r[0]}")  # Titel
            print(f"🔗 {r[1]}")  # Link
            print(f"📝 {r[2]}")  # Zusammenfassung
            print(f"📅 {r[3]}")  # Datum
            print("---")
    else:
        print("❌ Keine Artikel gefunden.")