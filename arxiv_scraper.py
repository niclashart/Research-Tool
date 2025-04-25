import key_manager
import requests
import arxiv
import os
import re
from openai import OpenAI
import logging
import time
from PyPDF2 import PdfReader
import pdfplumber
import relevance
import citation
import cache_utils

# Configuration
ARXIV_CATEGORIES = ['cs.LG'] # 'cs.AI', 'cs.LG', 'cs.CV' LG for Machine Learning / 'st.LG' for statisctical ML
OUTPUT_DIR = 'research_papers'
MAX_TITLE_LENGTH = 50  
MAX_TEXT_LENGTH = 3000  
RETRIES = 3
DOWNLOAD_DELAY = 1

client = OpenAI(api_key=key_manager.get_openai_key())

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_environment():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_pdf_filename(paper):
    clean_title = re.sub(r'[^\w\-_\. ]', '_', paper['title'])
    clean_title = clean_title.replace(' ', '_')
    short_title = clean_title[:MAX_TITLE_LENGTH].strip('_')
    paper_id = paper['entry_id'].split('/')[-1]
    return f"{short_title}_{paper_id}.pdf"

def get_prompt_style(style):
    if style == "Detailliert":
        return "Fasse den folgenden wissenschaftlichen Text möglichst vollständig und verständlich zusammen."
    elif style == "Bullet-Points":
        return "Fasse den folgenden wissenschaftlichen Text in 3-5 Bullet-Points zusammen."
    else:  # Kompakt oder unbekannt
        return "Fasse den folgenden wissenschaftlichen Text kurz und prägnant zusammen."

def scrape_arxiv(categories, max_results=10):
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=" OR ".join(f"cat:{cat}" for cat in categories),
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        papers = []
        for result in client.results(search):
            papers.append({
                'title': result.title,
                'authors': [a.name for a in result.authors],
                'published': result.published,
                'summary': result.summary,
                'pdf_url': f"https://arxiv.org/pdf/{result.entry_id.split('/')[-1]}.pdf",
                'entry_id': result.entry_id
            })
        return papers
    except Exception as e:
        logging.error(f"arXiv API failed: {str(e)}")
        return []

def download_pdf(paper):
    for attempt in range(RETRIES):
        try:
            filename = sanitize_pdf_filename(paper)
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if os.path.exists(filepath):
                logging.info(f"Skipping existing: {filename}")
                return filepath

            pdf_url = paper['pdf_url']
            logging.info(f"Downloading from: {pdf_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()

            if 'application/pdf' not in response.headers.get('Content-Type', ''):
                raise ValueError("URL doesn't point to PDF content")

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if not validate_pdf(filepath):
                os.remove(filepath)
                raise ValueError("Invalid PDF structure")

            return filepath

        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < RETRIES - 1:
                time.sleep(DOWNLOAD_DELAY * (attempt + 1))
    
    logging.error(f"Failed to download {paper['title']} after {RETRIES} attempts")
    return None

def validate_pdf(filepath):
    try:
        if os.path.getsize(filepath) < 1024:
            return False

        with open(filepath, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False
            
            f.seek(-128, os.SEEK_END)
            trailer = f.read()
            return b'%%EOF' in trailer
    except Exception:
        return False

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            text = '\n'.join([page.extract_text() for page in reader.pages])
            if text.strip():
                return text
    except Exception as e:
        logging.warning(f"PyPDF2 failed: {str(e)}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = '\n'.join([page.extract_text() for page in pdf.pages])
            return text if text.strip() else None
    except Exception as e:
        logging.error(f"pdfplumber failed: {str(e)}")
        return None

@cache_utils.cached(expiry=86400)  # Cache for 1 day
def summarize_with_gpt(text, model="gpt-3.5-turbo"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": f"Summarize the given article and focus on the most important things{text[:MAX_TEXT_LENGTH]}"
            }],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"GPT summarization failed: {str(e)}")
        return None

def generate_all_citations(paper):
    """Generate citations for a paper in all supported formats"""
    citation_data = paper.copy()
    citation_data['link'] = paper.get('pdf_url', '')
    
    return {
        'apa': citation.generate_apa_citation(citation_data),
        'mla': citation.generate_mla_citation(citation_data),
        'chicago': citation.generate_chicago_citation(citation_data),
        'bibtex': citation.generate_bibtex_citation(citation_data)
    }

def main_arxiv(categories=['cs.LG'], max_results=10, citation_styles=None):
    setup_environment()
    logging.info(f"Fetching papers from arXiv with categories: {categories}, max: {max_results}")
    papers = scrape_arxiv(categories=categories, max_results=max_results)
    
    if not papers:
        logging.error("No papers retrieved. Exiting.")
        return None
    
    if citation_styles is None:
        citation_styles = ["apa"]  # Default to APA
    elif citation_styles == "all":
        citation_styles = ["apa", "mla", "chicago", "bibtex"]

    summaries = {}
    for paper in papers:
        logging.info(f"\nProcessing: {paper['title']}")
        
        pdf_path = download_pdf(paper)
        if not pdf_path:
            continue

        text = extract_text_from_pdf(pdf_path)
        if not text:
            logging.error(f"Failed to extract text from {pdf_path}")
            continue

        summary = summarize_with_gpt(text)
        if summary:
            # Generate citations in requested styles
            paper_citations = {}
            for style in citation_styles:
                try:
                    # Ensure paper data has the expected 'link' field
                    paper_for_citation = paper.copy()
                    paper_for_citation['link'] = paper['pdf_url']
                    paper_citations[style] = citation.format_arxiv_citation(paper_for_citation, citation_style=style)
                except Exception as e:
                    logging.error(f"Failed to generate {style} citation: {str(e)}")
            
            summaries[paper['title']] = {
                'summary': summary,
                'link': paper['pdf_url'],
                'authors': ', '.join(paper['authors']),
                'published': paper['published'].strftime('%Y-%m-%d'),
                'citations': paper_citations  # Add citations to the data
            }
            
            print(f"\nSummary for {paper['title']}:")
            print(summary)
            
            # Print citations
            if paper_citations:
                print("\nCitations:")
                for style, cite in paper_citations.items():
                    print(f"{style.upper()}: {cite}")
                    
            print("\n" + "="*80 + "\n")
        else:
            logging.warning("Failed to generate summary")

    return summaries if summaries else None
