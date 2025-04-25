import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "articles_database.db"

def init_db():
    """Initialize the database with necessary tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create articles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        link TEXT NOT NULL UNIQUE,
        pub_date TEXT,
        summary TEXT,
        content TEXT,
        keywords TEXT,
        relevance_score REAL,
        created_at TEXT,
        UNIQUE(source, link)
    )
    ''')
    
    # Create user preferences table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_preferences (
        keyword TEXT PRIMARY KEY,
        score REAL
    )
    ''')
    
    conn.commit()
    conn.close()

def save_article(source, article_data):
    """Save an article to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Extract common fields from different source formats
    title = article_data.get('title') or article_data.get('Titel', '')
    link = article_data.get('link') or article_data.get('Link', '')
    
    # Format pub_date to ISO format string
    pub_date = article_data.get('pub_date') or article_data.get('Datum', datetime.now())
    if isinstance(pub_date, datetime):
        pub_date = pub_date.isoformat()
    
    summary = (article_data.get('summary') or 
               article_data.get('Zusammenfassung', ''))
    
    content = article_data.get('content', '')
    keywords = json.dumps(article_data.get('keywords', []))
    relevance_score = article_data.get('relevance_score', 0.0)
    
    # Check if article already exists
    cursor.execute('SELECT id FROM articles WHERE source=? AND link=?', 
                  (source, link))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing article
        cursor.execute('''
        UPDATE articles 
        SET summary=?, content=?, keywords=?, relevance_score=?
        WHERE source=? AND link=?
        ''', (summary, content, keywords, relevance_score, source, link))
    else:
        # Insert new article
        cursor.execute('''
        INSERT INTO articles 
        (source, title, link, pub_date, summary, content, keywords, relevance_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (source, title, link, pub_date, summary, content, keywords, 
              relevance_score, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def save_batch(source, articles):
    """Save a batch of articles to the database"""
    if not articles:
        return
        
    for article in articles:
        save_article(source, article)

def get_recent_articles(hours=24, sources=None):
    """Get recent articles from the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = '''
    SELECT * FROM articles 
    WHERE datetime(created_at) >= datetime('now', ?)
    '''
    params = [f'-{hours} hours']
    
    if sources:
        source_placeholders = ','.join(['?' for _ in sources])
        query += f' AND source IN ({source_placeholders})'
        params.extend(sources)
    
    cursor.execute(query, params)
    articles = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return articles

def update_user_preferences(keyword, score):
    """Update user preference scores"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO user_preferences (keyword, score)
    VALUES (?, ?)
    ''', (keyword.lower(), score))
    
    conn.commit()
    conn.close()

def get_user_preferences():
    """Get all user preferences"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_preferences ORDER BY score DESC')
    preferences = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return preferences