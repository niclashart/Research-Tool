import key_manager
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from openai import OpenAI
import requests
import locale
from datetime import datetime, timedelta
import re

locale.setlocale(locale.LC_TIME, 'en_US.UTF-8') # Setzt Zeit auf lokale Zeit, generell meist US Zeit 

# URL zum TechCrunch AI Bereich
TECHCRUNCH_AI_URL = "https://techcrunch.com/category/artificial-intelligence/" # Mehrere Links gleichzeitig

client = OpenAI(api_key=key_manager.get_openai_key()) # Client festlegen mit gegebenen API Key für Zusammenfassung

# Funktion zum Abrufen des HTML-Codes einer gegebenen URL
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

def main_techcrunch():
    print("Scraping gestartet...")
    html = fetch_page_html(TECHCRUNCH_AI_URL)
    articles = scrape_techcrunch_ai_articles(html)

    if not articles:
        print("❌ Keine heutigen Artikel gefunden.")
        return None

    print(f"✅ {len(articles)} heutige Artikel gefunden.")

    summarized_articles = []
    for article in articles:
        print(f"Zusammenfassen: {article['title']}")
        try:
            # Versuche die Zusammenfassung zu erstellen
            summary = summarize_with_openai(article['link'], key_manager.get_openai_key())
            
            # Wenn die Zusammenfassung None ist, setze einen Standardwert
            if summary is None:
                summary = "Keine Zusammenfassung verfügbar."
                
        except Exception as e:
            print(f"⚠️ Fehler bei der Zusammenfassung von '{article['title']}': {str(e)}")
            summary = f"Zusammenfassung fehlgeschlagen: {str(e)}"
            
        summarized_articles.append({
            "Titel": article["title"],
            "Link": article["link"],
            "Zusammenfassung": summary,
            "Datum": datetime.today().strftime('%Y-%m-%d')
        })
        time.sleep(1)  # Rate limiting

    return summarized_articles if summarized_articles else None