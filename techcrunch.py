import key_manager
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import locale
from datetime import datetime, timedelta
import re
import os
import json

try:
    locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '') 

# URL zum TechCrunch AI Bereich
TECHCRUNCH_AI_URL = "https://techcrunch.com/category/artificial-intelligence/" # Mehrere Links gleichzeitig

# Maximale Anzahl an Artikeln, die verarbeitet werden sollen
MAX_ARTICLES = 10

# Cache-Verzeichnis für verarbeitete Artikel
CACHE_DIR = "cache"
TECHCRUNCH_CACHE_FILE = os.path.join(CACHE_DIR, "techcrunch_processed_articles.json")

# Stellen Sie sicher, dass das Cache-Verzeichnis existiert
os.makedirs(CACHE_DIR, exist_ok=True)

# Laden des Caches mit bereits verarbeiteten Artikeln
def load_processed_articles():
    if os.path.exists(TECHCRUNCH_CACHE_FILE):
        try:
            with open(TECHCRUNCH_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden des Artikel-Caches: {e}")
    return {"processed_urls": [], "last_update": datetime.now().isoformat()}

# Aktualisieren des Caches mit neu verarbeiteten Artikeln
def save_processed_articles(processed_urls):
    cache_data = {
        "processed_urls": processed_urls,
        "last_update": datetime.now().isoformat()
    }
    try:
        with open(TECHCRUNCH_CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Fehler beim Speichern des Artikel-Caches: {e}")

client = OpenAI(api_key=key_manager.get_openai_key()) # Client festlegen mit gegebenen API Key für Zusammenfassung

def unique_articles(articles, seen):
    unique_articles = []
    for article in articles:
        if article['link'] not in seen:
            unique_articles.append(article)
            seen.add(article['link'])

    return unique_articles

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
    client = OpenAI(api_key=api_key)
    headers = {'User-Agent': 'Mozilla/5.0'}
    article_html = requests.get(link).text
    soup = BeautifulSoup(article_html, 'html.parser')

    paragraphs = soup.find_all('p')
    article_text = ' '.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)

    if not article_text:
        return "Inhalt konnte nicht gefunden werden"

    prompt = f"Summarize the blog post in a short paragraph. Focus on key contributions and methodology:\n\n{article_text[:3000]}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=250,
        stop=["\n\n"]
    )

    return response.choices[0].message.content.strip()

def fetch_page_html(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(15)
    html = driver.page_source
    driver.quit()
    return html

def scrape_techcrunch_ai_articles(html):
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    today = datetime.today().strftime('%Y/%m/%d')
    yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y/%m/%d')

    for entry in soup.select('a'):
        href = entry.get('href', '')
        if (today in href or yesterday in href) and '/category/artificial-intelligence/' not in href and len(entry.get_text(strip=True)) > 20:
            title = entry.get_text(strip=True)
            link = href
            if link.startswith('/'):
                link = f'https://techcrunch.com{link}'
            articles.append({
                "title": title,
                "link": link
            })

    seen = set()
    unique_articles = []
    for article in articles:
        if article['link'] not in seen:
            unique_articles.append(article)
            seen.add(article['link'])

    return unique_articles

def main_techcrunch():
    print("Scraping TechCrunch gestartet...")
    
    # Laden der bereits verarbeiteten Artikel
    cache_data = load_processed_articles()
    processed_urls = set(cache_data["processed_urls"])
    
    html = fetch_page_html(TECHCRUNCH_AI_URL)
    articles = scrape_techcrunch_ai_articles(html)

    if not articles:
        print("❌ Keine heutigen TechCrunch Artikel gefunden.")
        return []

    print(f"✅ {len(articles)} TechCrunch Artikel gefunden.")
    
    # Filtern bereits verarbeiteter Artikel
    new_articles = [article for article in articles if article["link"] not in processed_urls]
    if not new_articles:
        print("✓ Alle verfügbaren TechCrunch Artikel wurden bereits verarbeitet.")
        return []
        
    print(f"✓ {len(new_articles)} neue TechCrunch Artikel zum Verarbeiten gefunden.")

    summarized_articles = []
    articles_processed = 0
    
    # Begrenzen der Anzahl zu verarbeitender Artikel
    articles_to_process = new_articles[:MAX_ARTICLES]
    total_articles = len(articles_to_process)
    
    for idx, article in enumerate(articles_to_process, 1):
        print(f"Zusammenfassen [{idx}/{total_articles}]: {article['title']}")
        try:
            # Versuche die Zusammenfassung zu erstellen
            summary = summarize_with_openai(article['link'], key_manager.get_openai_key())
            
            # Wenn die Zusammenfassung None ist, setze einen Standardwert
            if summary is None:
                summary = "Keine Zusammenfassung verfügbar."
            
            # URL als verarbeitet markieren
            processed_urls.add(article["link"])
                
        except Exception as e:
            print(f"⚠️ Fehler bei der Zusammenfassung von '{article['title']}': {str(e)}")
            summary = f"Zusammenfassung fehlgeschlagen: {str(e)}"
            
        articles_processed += 1
        summarized_articles.append([
            article["title"],
            article["link"],
            summary
        ])
        
        # Speichere regelmäßig den Cache
        if articles_processed % 5 == 0 or idx == total_articles:
            save_processed_articles(list(processed_urls))
            
        time.sleep(1)  # Rate limiting
    
    # Abschließendes Speichern des Caches
    save_processed_articles(list(processed_urls))
    print(f"✅ TechCrunch Scraping abgeschlossen. {articles_processed} Artikel verarbeitet.")

    return summarized_articles if summarized_articles else []
