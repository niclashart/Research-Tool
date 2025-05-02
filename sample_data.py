import db_manager
import json
from datetime import datetime, timedelta

def add_sample_data():
    """Add sample data to the database for testing"""
    print("Initializing database...")
    db_manager.init_db("research_data.db")
    
    # Sample article data
    sample_articles = [
        {
            'source': 'arxiv',
            'data': {
                'title': 'Generalization Capability for Imitation Learning',
                'link': 'https://arxiv.org/abs/2504.18538',
                'pub_date': (datetime.now() - timedelta(days=2)).isoformat(),
                'summary': 'This paper explores novel approaches to improve generalization in imitation learning systems, focusing on AI agents that learn from demonstrations.',
                'content': 'Extended content about imitation learning systems...',
                'keywords': json.dumps(['imitation learning', 'generalization', 'AI agents', 'reinforcement learning', 'neural networks']),
                'relevance_score': 0.95
            }
        },
        {
            'source': 'arxiv',
            'data': {
                'title': 'Scaling Laws For Scalable Oversight',
                'link': 'https://arxiv.org/abs/2504.18530',
                'pub_date': (datetime.now() - timedelta(days=1)).isoformat(),
                'summary': 'This research investigates scaling laws for AI oversight mechanisms that can grow alongside increasingly powerful AI systems.',
                'content': 'Extended content about AI oversight...',
                'keywords': json.dumps(['AI safety', 'oversight', 'scaling laws', 'alignment', 'machine learning']),
                'relevance_score': 0.92
            }
        },
        {
            'source': 'techcrunch',
            'data': {
                'title': 'New Framework for Responsible AI Development Released',
                'link': 'https://techcrunch.com/sample/responsible-ai',
                'pub_date': datetime.now().isoformat(),
                'summary': 'A consortium of tech companies announced a new framework for responsible AI development, focusing on transparency and accountability.',
                'content': 'Full article about responsible AI development...',
                'keywords': json.dumps(['responsible AI', 'ethics', 'governance', 'technology policy', 'industry standards']),
                'relevance_score': 0.88
            }
        },
        {
            'source': 'theverge',
            'data': {
                'title': 'AI Researchers Make Breakthrough in Language Understanding',
                'link': 'https://theverge.com/sample/language-ai',
                'pub_date': (datetime.now() - timedelta(days=3)).isoformat(),
                'summary': 'A team of researchers has announced a significant improvement in AI language understanding capabilities, achieving human-level performance on complex reasoning tasks.',
                'content': 'Full article about AI language understanding...',
                'keywords': json.dumps(['NLP', 'language models', 'reasoning', 'AI research', 'benchmarks']),
                'relevance_score': 0.91
            }
        },
        {
            'source': 'stanford',
            'data': {
                'title': 'Stanford Launches New AI Safety Center',
                'link': 'https://ai.stanford.edu/sample/safety-center',
                'pub_date': (datetime.now() - timedelta(days=4)).isoformat(),
                'summary': 'Stanford University has launched a new research center dedicated to the study of AI safety and alignment, with a focus on long-term risks.',
                'content': 'Full article about Stanford AI Safety Center...',
                'keywords': json.dumps(['AI safety', 'alignment', 'research center', 'stanford', 'ethics']),
                'relevance_score': 0.94
            }
        },
        {
            'source': 'thehackernews',
            'data': {
                'title': 'New Cybersecurity Risks from AI Systems Identified',
                'link': 'https://thehackernews.com/sample/ai-security-risks',
                'pub_date': (datetime.now() - timedelta(days=2)).isoformat(),
                'summary': 'Security researchers have identified novel attack vectors targeting AI systems, raising concerns about the security implications of deployed models.',
                'content': 'Full article about AI security risks...',
                'keywords': json.dumps(['cybersecurity', 'AI security', 'machine learning', 'vulnerabilities', 'attacks']),
                'relevance_score': 0.87
            }
        },
    ]
    
    # Add sample articles to database
    print("Adding sample articles to database...")
    for article in sample_articles:
        db_manager.save_article(article['source'], article['data'])
    
    print("Sample data added successfully!")
    
    # Verify data was added
    recent = db_manager.get_recent_articles(hours=24*30)
    print(f"Database now has {len(recent)} articles")

if __name__ == "__main__":
    add_sample_data()