import key_manager
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from datetime import datetime, timedelta, timezone
import time
import re

SITEMAP_FEED_URL = "https://www.theverge.com/rss/index.xml"

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
        return None, [], []

    if not is_meaningfully_about_ai(article_text, api_key):
        print("❌ GPT sagt: Kein AI-Artikel. Wird übersprungen.")
        return None, [], []

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
    articles = get_recent_articles_from_sitemap(SITEMAP_FEED_URL)

    if not articles:
        print("❌ Keine aktuellen Artikel in den letzten 24 Stunden gefunden.")
        return None

    print(f"✅ {len(articles)} aktuelle Artikel gefunden.")

    summarized_articles = []
    for article in articles:
        print(f"\n✏️ Prüfe Artikel auf AI-Bezug: {article['title']}")
        summary, matched_keywords, matched_sentences = summarize_with_openai(article['link'], key_manager.get_openai_key())
        if summary:
            print(f"✅ GPT validiert: Artikel ist AI-relevant.")
            print(f"Gefundene Keywords: {', '.join(matched_keywords)}")
            for sent in matched_sentences:
                print(f"→ {sent}")
            summarized_articles.append({
                "Titel": article["title"],
                "Link": article["link"],
                "Zusammenfassung": summary,
                "Keywords": matched_keywords,
                "Keyword_Sätze": matched_sentences,
                "Datum": datetime.today().strftime('%Y-%m-%d')
            })
        else:
            print("⏩ Übersprungen.")
        time.sleep(1)  

    return summarized_articles if summarized_articles else None

if __name__ == "__main__":
    results = main_verge()
    if results:
        for r in results:
            print("\n📰", r["Titel"])
            print("Gefundene Keywords:", ", ".join(r["Keywords"]))
            for s in r["Keyword_Sätze"]:
                print(f"→ {s}")
            print(r["Zusammenfassung"])
            print("🔗", r["Link"])
            print("---")
