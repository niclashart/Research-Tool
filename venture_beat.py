import key_manager
import time
from datetime import datetime, timezone, timedelta
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import re

client = OpenAI(api_key=key_manager.get_openai_key())

VENTUREBEAT_AI_URL = "https://venturebeat.com/category/ai/"

# Aktueller Zeitpunkt (UTC) für den 24h-Vergleich
now = datetime.now(timezone.utc)

def scrape_article_list(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Fehler beim Abrufen der Seite ({url}): {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    articles_html = soup.find_all("article")
    
    article_list = []
    for art in articles_html:
        title_tag = art.find(["h2", "h3"])
        if not title_tag:
            continue
        
        a_tag = title_tag.find("a")
        if not a_tag:
            continue
        
        title = a_tag.get_text(strip=True)
        link = a_tag.get("href", "")
        if not link.startswith("http"):
            link = "https://venturebeat.com" + link
        
        time_tag = art.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            date_str = time_tag["datetime"]
            try:
                pub_date = datetime.fromisoformat(date_str)
            except Exception as e:
                print("Fehler beim Parsen des Datums:", e)
                continue
        else:
            continue
        
        if pub_date.tzinfo is None:
            pub_date = pub_date.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) - pub_date > timedelta(days=1):
            continue
        
        author = "Unbekannt"
        author_tag = art.find("span", class_="Article__author-info")
        if author_tag:
            author = author_tag.get_text(strip=True)
        
        article_list.append({
            "title": title,
            "link": link,
            "pub_date": pub_date,
            "author": author
        })
    
    return article_list

def scrape_article_content(article_url):
    try:
        response = requests.get(article_url)
        if response.status_code != 200:
            print("Fehler beim Abrufen des Artikels:", article_url)
            return ""
        
        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find("div", class_="article-content")
        if not content_div:
            return ""
        
        paragraphs = content_div.find_all("p")
        text = "\n".join(p.get_text() for p in paragraphs)
        return text
    
    except Exception as e:
        print("Fehler beim Laden des Artikels:", e)
        return ""

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

def summarize_text(article_text):
    if not is_meaningfully_about_ai(article_text=article_text, api_key=key_manager.get_openai_key()):
        print ("GPT sagt: Kein AI-Artikel. Wird übersprungen")

    prompt = (
        "Summarize this articl in 3 paragraphs. Focus on key contributions and methodology."
        "Keep in mind to keep the summary concise and only name the most relevant , AI-related information\n\n"
        f"{article_text}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Artikel prägnant zusammenfasst. Das Ganze bitte auf deutsch."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300,
            stop=["\n\n"]
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("Fehler bei der ChatGPT API Anfrage:", e)
        return ""

def main_venturebeat():
    articles = scrape_article_list(VENTUREBEAT_AI_URL)
    if not articles:
        print("Keine Artikel in den letzten 24 Stunden gefunden.")
        return None
    
    results = []
    for art in articles:
        print(f"Verarbeite Artikel: {art['title']}")
        content = scrape_article_content(art["link"])
        if not content:
            print("  Kein Inhalt gefunden, überspringe Artikel.")
            continue
        
        summary = summarize_text(content)
        if not summary:
            print("  Zusammenfassung fehlgeschlagen, überspringe Artikel.")
            continue
        
        results.append({
            "title": art["title"],
            "link": art["link"],
            "pub_date": art["pub_date"],
            "author": art["author"],
            "summary": summary
        })
        
        time.sleep(1)
    
    return results if results else None