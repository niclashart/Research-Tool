import feedparser
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
from datetime import datetime, timedelta, timezone
import time
import key_manager

client = OpenAI(api_key=key_manager.get_openai_key())

# RSS Feed URL - Using the direct site feed instead of Feedburner
THN_FEED_URL = "https://thehackernews.com/feeds/posts/default?alt=rss"

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
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der sicherheitsrelevante Artikel zusammenfasst."},
                {"role": "user", "content": prompt}
            ],
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
    return fetch_thn_articles()

# Testlauf
if __name__ == "__main__":
    result = main_thn()
    if result:
        for r in result:
            print(f"📰 {r['Titel']}")
            print(f"🔗 {r['Link']}")
            print(f"KI-relevant: {'✅' if r['KI_bezogen'] else '❌'} ({r['KI_Keywords']})")
            print(f"📝 {r['Zusammenfassung']}")
            print("---")
    else:
        print("❌ Keine Artikel gefunden.")