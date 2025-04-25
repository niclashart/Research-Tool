import key_manager
import time
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==== CONFIGURATION ====
MAX_ARTICLES = 5  
WAIT_TIME = 10     
TEXT_LIMIT = 2000
STANFORD_AI_URL = "https://ai.stanford.edu/blog/"

client = OpenAI(api_key=key_manager.get_openai_key())

# ==== SETUP HEADLESS CHROME ====
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(options=options)

# ==== STEP 1: GET BLOG POST LINKS ====
def get_blog_links(main_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    
    driver.get(main_url)
    time.sleep(10)
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post-teaser")))
    except Exception as e:
        print("⚠️ Warning: Articles did not load in time.")
    
    articles = driver.find_elements(By.CLASS_NAME, "post-teaser")
    print(f"📰 Found {len(articles)} posts")
    links = []
    
    for article in articles[:5]:  # Limit to 5 articles
        try:
            title = article.find_element(By.CLASS_NAME, "excerpt").text.strip()
            button = article.find_element(By.CSS_SELECTOR, "div.excerpt-continue a.button")
            link = button.get_attribute("href")
            if link.startswith("/"):
                link = "https://ai.stanford.edu" + link
            print(f"✅ Extracted: {title} - {link}")
            links.append((title, link))
        except Exception as e:
            print(f"⚠️ Error finding button for article: {e}")
    
    driver.quit()
    return links

def extract_article(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "post-content")))
        
        try:
            header = driver.find_element(By.CLASS_NAME, "post-header")
            title = header.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            title = driver.find_element(By.CSS_SELECTOR, "header h1").text.strip()
        
        paragraphs = driver.find_elements(By.CSS_SELECTOR, "section.post-content p")
        content = "\n\n".join(p.text for p in paragraphs)
        print(f"📄 Extracted content length: {len(content)} characters")
        
        driver.quit()
        return title, content
    except Exception as e:
        print(f"❌ Error extracting article at {url}: {e}")
        driver.quit()
        return None, None

def summarize_text(article_text):
    prompt = (
        "Summarize this blog post in 3 paragraphs. Focus on key contributions and methodology. "
        "Please keep the summary concise and only name the most relevant information out of the article:\n\n"
        f"{article_text}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Assistent, der Artikel prägnant zusammenfasst. Das Ganze bitte auf Deutsch."},
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
    
def main_stanford():
    summaries = []
    print("🔍 Scraping Stanford AI Blog...")
    blog_links = get_blog_links(STANFORD_AI_URL)
    print(f"🔗 Found {len(blog_links)} articles")
    
    for title, link in blog_links:
        print(f"--- Processing: {title} ---")
        article_title, full_text = extract_article(link)
        if article_title and full_text:
            summary = summarize_text(full_text)
            summaries.append((article_title, link, summary))
        time.sleep(5)
    
    return summaries if summaries else None
