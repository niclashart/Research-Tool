import os
import json
from collections import defaultdict, Counter

FEEDBACK_FILE = "user_feedback.json"

def save_feedback(title, text, score):
    keywords = extract_keywords(text)
    entry = {
        "title": title,
        "keywords": keywords,
        "score": score
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return[json.loads(line) for line in f.readlines()]
    
def extract_keywords(text, max_keywords=5):
    words = [w.lower() for w in text.split() if len(w) > 4]
    common = Counter(words).most_common(max_keywords)
    return  [w for w, _ in common]

def get_user_preference():
    feedback = load_feedback()
    scores = defaultdict(list)
    for entry in feedback:
        for kw in entry["keywords"]:
            scores[kw].append(entry["score"])
    avg_scores = {kw: sum(vals)/len(vals) for kw, vals in scores.items()}
    return sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

