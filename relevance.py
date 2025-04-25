from openai import OpenAI
import key_manager
import spacy
import re
from collections import Counter
import cache_utils

client = OpenAI(api_key=key_manager.get_openai_key())

# Load spaCy model for NLP tasks
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# AI-related keywords with weights
AI_KEYWORDS = {
    "artificial intelligence": 1.0,
    "machine learning": 0.9,
    "deep learning": 0.9,
    "neural network": 0.8,
    "large language model": 1.0,
    "llm": 0.9,
    "generative ai": 1.0,
    "natural language processing": 0.8,
    "nlp": 0.7,
    "computer vision": 0.7,
    "reinforcement learning": 0.8,
    "ai ethics": 0.8,
    "transformer": 0.7,
    "openai": 0.8,
    "gpt": 0.8,
    "chatgpt": 0.8,
    "gemini": 0.7,
    "claude": 0.7,
    "mistral": 0.7,
    "anthropic": 0.7,
    "google ai": 0.7
}

@cache_utils.cached(expiry=86400)
def analyze_relevance(text, model="gpt-3.5-turbo"):
    """
    Analyze text relevance using both keyword-based and AI-based methods
    Returns a score between 0 and 10
    """
    # First pass: quick keyword-based scoring
    keyword_score = calculate_keyword_score(text)
    
    # If keyword score is very low, avoid API call
    if keyword_score < 0.2:
        return round(keyword_score * 5)  # Scale to 0-1 range
    
    # Second pass: detailed AI-based scoring
    ai_score = analyze_with_gpt(text, model)
    
    # Combine scores (weighted average)
    combined_score = (keyword_score * 0.4) + (ai_score * 0.6)
    
    # Return final score on scale 0-10
    return round(combined_score * 10)

def calculate_keyword_score(text):
    """Calculate relevance score based on keyword matching"""
    text = text.lower()
    total_weight = 0
    matches = 0
    
    # Check for keyword matches
    for keyword, weight in AI_KEYWORDS.items():
        if keyword in text:
            matches += 1
            total_weight += weight
            
            # Bonus for keywords in title or beginning of text
            first_500_chars = text[:500]
            if keyword in first_500_chars:
                total_weight += weight * 0.5
    
    # Normalize score between 0 and 1
    if matches == 0:
        return 0
    
    # Extract named entities for additional context
    doc = nlp(text[:2000])  # Limit to first 2000 chars for performance
    entities = [ent.text.lower() for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "PERSON"]]
    
    # Check if AI companies/products are mentioned
    ai_companies = ["openai", "google", "microsoft", "anthropic", "meta", "nvidia"]
    company_matches = sum(1 for company in ai_companies if any(company in entity for entity in entities))
    
    # Final score calculation with normalization
    base_score = min(1.0, total_weight / 10)  # Cap at 1.0
    company_bonus = min(0.3, company_matches * 0.1)  # Max 0.3 bonus for companies
    
    return min(1.0, base_score + company_bonus)

@cache_utils.cached(expiry=86400)
def analyze_with_gpt(text, model="gpt-3.5-turbo"):
    """Use GPT to analyze text relevance to AI topics"""
    prompt = (
        "On a scale of 0.0 to 1.0, rate how relevant this text is to artificial intelligence, "
        "machine learning, or related AI technologies. "
        "Consider technical depth, specificity to AI, and importance to the field. "
        "Return ONLY a single decimal number between 0.0 and 1.0, with no explanation.\n\n"
        f"{text[:3000]}"
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=5,
            temperature=0.0
        )
        score_text = response.choices[0].message.content.strip()
        # Extract decimal number
        match = re.search(r'([0-9]*\.?[0-9]+)', score_text)
        if match:
            return float(match.group(1))
        return 0.5  # Default if parsing fails
    except Exception as e:
        print(f"❌ Error in GPT relevance analysis: {e}")
        return 0.5  # Default score on error

def extract_keywords(text, max_keywords=10):
    """Extract important keywords from text"""
    doc = nlp(text[:5000])  # Process first 5000 chars for performance
    
    # Filter for noun phrases and named entities
    important_tokens = []
    for token in doc:
        if (token.pos_ in ["NOUN", "PROPN"] and 
            not token.is_stop and 
            len(token.text) > 3):
            important_tokens.append(token.lemma_.lower())
    
    # Count frequencies
    keyword_freq = Counter(important_tokens)
    
    # Get most common keywords
    top_keywords = keyword_freq.most_common(max_keywords)
    return [kw for kw, _ in top_keywords]

def get_most_relevant_sentences(text, n=3):
    """Extract the most AI-relevant sentences from text"""
    sentences = [sent.text.strip() for sent in nlp(text).sents]
    
    # Score each sentence
    scored_sentences = []
    for sentence in sentences:
        if len(sentence) < 20:  # Skip very short sentences
            continue
            
        score = 0
        for keyword, weight in AI_KEYWORDS.items():
            if keyword in sentence.lower():
                score += weight
                
        scored_sentences.append((sentence, score))
    
    # Sort by score and return top n
    scored_sentences.sort(key=lambda x: x[1], reverse=True)
    return [sent for sent, score in scored_sentences[:n]]