import key_manager
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime, timedelta, timezone
import time
import re
import os
import json

SITEMAP_FEED_URL = "https://www.theverge.com/rss/index.xml"

# Maximale Anzahl an Artikeln, die verarbeitet werden sollen
MAX_ARTICLES = 10

# Cache-Verzeichnis für verarbeitete Artikel
CACHE_DIR = "cache"
THEVERGE_CACHE_FILE = os.path.join(CACHE_DIR, "theverge_processed_articles.json")

# Stellen Sie sicher, dass das Cache-Verzeichnis existiert
os.makedirs(CACHE_DIR, exist_ok=True)

# Laden des Caches mit bereits verarbeiteten Artikeln
def load_processed_articles():
    if os.path.exists(THEVERGE_CACHE_FILE):
        try:
            with open(THEVERGE_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden des TheVerge-Artikel-Caches: {e}")
    return {"processed_urls": [], "last_update": datetime.now().isoformat()}

# Aktualisieren des Caches mit neu verarbeiteten Artikeln
def save_processed_articles(processed_urls):
    cache_data = {
        "processed_urls": processed_urls,
        "last_update": datetime.now().isoformat()
    }
    try:
        with open(THEVERGE_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Fehler beim Speichern des TheVerge-Artikel-Caches: {e}")

client = OpenAI(api_key=key_manager.get_openai_key())

def get_recent_articles_from_sitemap(feed_url):
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)

    recent_articles = []
    for entry in feed.entries:
        try:
            published = datetime(*entry.published_parsed[:6]).replace(tzinfo=None)
            if published >= cutoff:
                recent_articles.append({
                    'title': entry.title,
                    'link': entry.link
                })
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten von Feed-Eintrag: {e}")
            continue

    return recent_articles

def is_ai_related(text):
    keywords = [
        "AI", "artificial intelligence", "machine learning",
        "neural network", "large language model", "LLM",
        "OpenAI", "GPT", "chatbot"
    ]
    keyword_hits = []
    matched_sentences = []

    sentences = re.split(r'(?<=[.!?]) +', text)

    for kw in keywords:
        for sentence in sentences:
            if kw.lower() in sentence.lower():
                keyword_hits.append(kw)
                matched_sentences.append(sentence.strip())
                break

    return list(set(keyword_hits)), matched_sentences

def is_meaningfully_about_ai(text, api_key):
    prompt = (
        "Does the following article meaningfully discuss artificial intelligence, "
        "machine learning, or AI-related technology (like LLMs, OpenAI, etc.)? "
        "Answer with only 'Yes' or 'No'.\n\n"
        f"{text[:3000]}"
    )
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=5
    )
    answer = response.choices[0].message.content.strip().lower()
    return "yes" in answer

def summarize_with_openai(link, api_key):
    headers = {'User-Agent': 'Mozilla/5.0'}
    article_html = requests.get(link, headers=headers).text
    soup = BeautifulSoup(article_html, 'html.parser')

    paragraphs = soup.find_all('p')
    article_text = ' '.join(
        p.get_text(strip=True)
        for p in paragraphs
        if len(p.get_text(strip=True)) > 20
    )

    if not article_text:
        return None

    # Prüfe, ob der Artikel KI-bezogen ist
    if not is_meaningfully_about_ai(article_text, api_key):
        print("❌ GPT sagt: Kein AI-Artikel. Wird übersprungen.")
        return None

    # Extrahiere Keywords für Debugging
    keywords, sentences = is_ai_related(article_text)
    if keywords:
        print(f"Gefundene AI-Keywords: {', '.join(keywords)}")

    prompt = f"Summarize this blog post in a short paragraph. Focus on the most important, AI-related information in the summary: \n\n{article_text[:3000]}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=250,
        stop=["\n\n"]
    )

    return response.choices[0].message.content.strip()

def main_verge():
    print("📡 Abrufen der RSS-Feeds von The Verge...")
    
    # Laden der bereits verarbeiteten Artikel
    cache_data = load_processed_articles()
    processed_urls = set(cache_data.get("processed_urls", []))
    
    articles = get_recent_articles_from_sitemap(SITEMAP_FEED_URL)

    if not articles:
        print("❌ Keine aktuellen The Verge Artikel in den letzten 24 Stunden gefunden.")
        return []

    print(f"✅ {len(articles)} aktuelle The Verge Artikel gefunden.")
    
    # Filtern bereits verarbeiteter Artikel
    new_articles = [article for article in articles if article["link"] not in processed_urls]
    if not new_articles:
        print("✓ Alle verfügbaren The Verge Artikel wurden bereits verarbeitet.")
        return []
        
    print(f"✓ {len(new_articles)} neue The Verge Artikel zum Verarbeiten gefunden.")

    summarized_articles = []
    articles_processed = 0
    
    # Begrenzen der Anzahl zu verarbeitender Artikel
    articles_to_process = new_articles[:MAX_ARTICLES]
    total_articles = len(articles_to_process)
    
    for idx, article in enumerate(articles_to_process, 1):
        print(f"\n✏️ Prüfe Artikel auf AI-Bezug [{idx}/{total_articles}]: {article['title']}")
        try:
            summary = summarize_with_openai(article['link'], key_manager.get_openai_key())
            
            if summary:
                print(f"✅ GPT validiert: Artikel ist AI-relevant.")
                summarized_articles.append([
                    article["title"],
                    article["link"],
                    summary,
                    datetime.today().strftime('%Y-%m-%d')
                ])
                
                # URL als verarbeitet markieren
                processed_urls.add(article["link"])
                articles_processed += 1
            else:
                print("⏩ Kein AI-Bezug, übersprungen.")
                # Auch nicht-AI-relevante Artikel als verarbeitet markieren
                processed_urls.add(article["link"])
        except Exception as e:
            print(f"⚠️ Fehler bei der Verarbeitung von '{article['title']}': {str(e)}")
        
        # Speichere regelmäßig den Cache
        if articles_processed % 3 == 0 or idx == total_articles:
            save_processed_articles(list(processed_urls))
            
        time.sleep(1)  # Rate limiting
    
    # Abschließendes Speichern des Caches
    save_processed_articles(list(processed_urls))
    print(f"✅ The Verge Scraping abgeschlossen. {articles_processed} AI-relevante Artikel gefunden.")

    return summarized_articles if summarized_articles else []

if __name__ == "__main__":
    results = main_verge()
    if results:
        for r in results:
            # Array-Struktur: [title, link, summary, date]
            print("\n📰", r[0])  # Titel
            print(r[2])  # Zusammenfassung
            print("🔗", r[1])  # Link
            print("📅", r[3])  # Datum
            print("---")
