import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import time
import dotenv
import logging
from pathlib import Path

# Load environment variables
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_app.log')
    ]
)
logger = logging.getLogger('ai_research_hub')

# Import your existing modules - modified to work with .env
import arxiv_scraper
import techcrunch
import venture_beat
import stanford_ai
import theverge
import thn
import db_manager
import relevance
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))  # For session management
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# OpenAI client for chat functionality
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Setup database
db_path = os.environ.get('DB_PATH', 'research_data.db')
db_manager.init_db(db_path)

# Ensure directories exist
os.makedirs('summary', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# Routes
@app.route('/')
def index():
    """Home page route"""
    try:
        # Get basic statistics to display on home page
        stats = {
            'total_articles': len(db_manager.get_recent_articles(hours=24*30)),  # articles from last 30 days
            'sources_count': 6,  # ArXiv, TechCrunch, VentureBeat, Stanford AI, TheVerge, TheHackerNews
            'recent_articles': len(db_manager.get_recent_articles(hours=24)),  # articles from last 24 hours
        }
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return render_template('index.html', stats={'total_articles': 0, 'sources_count': 6, 'recent_articles': 0}, error=str(e))

@app.route('/dashboard')
def dashboard():
    """Dashboard page with visualizations and analytics"""
    try:
        # Get recent articles for dashboard display
        recent_articles = db_manager.get_recent_articles(hours=24*7)  # Last week
        
        # Process articles to extract keywords and trends
        keywords = {}
        sources = {}
        dates = {}
        
        for article in recent_articles:
            # Process keywords
            article_keywords = json.loads(article.get('keywords', '[]'))
            for kw in article_keywords:
                if kw in keywords:
                    keywords[kw] += 1
                else:
                    keywords[kw] = 1
            
            # Process sources
            source = article.get('source')
            if source in sources:
                sources[source] += 1
            else:
                sources[source] = 1
            
            # Process dates
            date_str = article.get('pub_date', '')[:10]  # Get only YYYY-MM-DD part
            if date_str:
                if date_str in dates:
                    dates[date_str] += 1
                else:
                    dates[date_str] = 1
        
        # Sort data for visualization
        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
        source_distribution = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        
        # Sort dates chronologically
        sorted_dates = sorted(dates.items(), key=lambda x: x[0])
        
        # Prepare data for charts
        chart_data = {
            'keywords': {
                'labels': [kw[0] for kw in top_keywords],
                'data': [kw[1] for kw in top_keywords]
            },
            'sources': {
                'labels': [s[0] for s in source_distribution],
                'data': [s[1] for s in source_distribution]
            },
            'timeline': {
                'labels': [d[0] for d in sorted_dates],
                'data': [d[1] for d in sorted_dates]
            }
        }
        
        return render_template('dashboard.html', 
                            articles=recent_articles[:20],  # Show only 20 most recent
                            chart_data=chart_data)
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}", exc_info=True)
        return render_template('dashboard.html', articles=[], chart_data={}, error=str(e))

@app.route('/sources')
def sources():
    """Sources page to fetch and view articles"""
    try:
        # Get data directly from the database to avoid refetching
        recent_articles = db_manager.get_recent_articles(hours=24*7)  # Last week
        
        # Group by source
        articles_by_source = {}
        for article in recent_articles:
            source = article.get('source')
            if source not in articles_by_source:
                articles_by_source[source] = []
            articles_by_source[source].append(article)
        
        return render_template('sources.html', 
                            articles_by_source=articles_by_source,
                            source_names={
                                'arxiv': 'ArXiv Papers',
                                'techcrunch': 'TechCrunch Articles',
                                'venturebeat': 'VentureBeat Articles',
                                'stanford': 'Stanford AI Blog',
                                'theverge': 'The Verge Articles',
                                'thehackernews': 'The Hacker News Articles'
                            })
    except Exception as e:
        logger.error(f"Error in sources route: {str(e)}", exc_info=True)
        return render_template('sources.html', articles_by_source={}, source_names={}, error=str(e))

@app.route('/chat')
def chat():
    """AI Chat Assistant page"""
    try:
        # Reset chat if requested
        if request.args.get('reset'):
            session.pop('chat_history', None)
        
        # Initialize chat history if needed
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        return render_template('chat.html', chat_history=session.get('chat_history', []))
    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}", exc_info=True)
        return render_template('chat.html', chat_history=[], error=str(e))

@app.route('/settings')
def settings():
    """Settings page"""
    try:
        # Get user preferences
        preferences = {
            'api_key_set': bool(os.environ.get('OPENAI_API_KEY')),
            'theme': 'light',
            'default_sources': ['arxiv', 'techcrunch', 'venturebeat'],
            'max_results': 10
        }
        
        return render_template('settings.html', preferences=preferences)
    except Exception as e:
        logger.error(f"Error in settings route: {str(e)}", exc_info=True)
        return render_template('settings.html', preferences={}, error=str(e))

@app.route('/api/fetch_articles', methods=['POST'])
def api_fetch_articles():
    """API endpoint to fetch articles"""
    try:
        data = request.form
        
        # Get parameters
        sources = data.getlist('sources')
        max_articles = int(data.get('max_articles', 10))
        arxiv_category = data.get('arxiv_category', 'cs.LG')
        
        # Get selected citation styles
        citation_styles = data.getlist('citation_styles')
        if not citation_styles:
            citation_styles = ["apa"]
        
        results = {}
        
        # Fetch articles from selected sources
        if 'arxiv' in sources:
            results['arxiv'] = arxiv_scraper.main_arxiv(
                categories=[arxiv_category],
                max_results=max_articles,
                citation_styles=citation_styles
            )
            # Save to database
            if results['arxiv']:
                for title, data in results['arxiv'].items():
                    # Format data for database
                    db_data = {
                        'title': title,
                        'link': data['link'],
                        'summary': data['summary'],
                        'pub_date': data['published'],
                        'content': data['summary'],
                        'keywords': relevance.extract_keywords(data['summary']),
                        'relevance_score': relevance.analyze_relevance(data['summary'])
                    }
                    db_manager.save_article('arxiv', db_data)
        
        if 'techcrunch' in sources:
            results['techcrunch'] = techcrunch.main_techcrunch()
            if results['techcrunch']:
                db_manager.save_batch('techcrunch', results['techcrunch'])
        
        if 'venturebeat' in sources:
            results['venturebeat'] = venture_beat.main_venturebeat()
            if results['venturebeat']:
                db_manager.save_batch('venturebeat', results['venturebeat'])
        
        if 'stanford' in sources:
            stanford_results = stanford_ai.main_stanford()
            if stanford_results:
                results['stanford'] = stanford_results
                # Convert to proper format for database
                for title, link, summary in stanford_results:
                    db_data = {
                        'title': title,
                        'link': link,
                        'summary': summary,
                        'pub_date': datetime.now().strftime('%Y-%m-%d'),
                        'keywords': relevance.extract_keywords(summary),
                        'relevance_score': relevance.analyze_relevance(summary)
                    }
                    db_manager.save_article('stanford', db_data)
        
        if 'theverge' in sources:
            results['theverge'] = theverge.main_verge()
            if results['theverge']:
                db_manager.save_batch('theverge', results['theverge'])
        
        if 'thehackernews' in sources:
            results['thehackernews'] = thn.main_thn()
            if results['thehackernews']:
                db_manager.save_batch('thehackernews', results['thehackernews'])
        
        # Store results in session for later use
        session['results'] = results
        
        return jsonify({
            'success': True,
            'message': 'Articles fetched successfully',
            'redirect': url_for('sources')
        })
    
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error fetching articles: {str(e)}'
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat interaction"""
    try:
        data = request.json
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({
                'success': False,
                'message': 'No query provided'
            }), 400
        
        # Get chat history
        chat_history = session.get('chat_history', [])
        
        # Add user message
        chat_history.append({
            'role': 'user',
            'content': user_query
        })
        
        # Get relevant articles
        recent_articles = db_manager.get_recent_articles(hours=24*7)  # Last week
        relevant_articles = []
        
        # Simple relevance filtering - in production, use a more sophisticated approach
        for article in recent_articles:
            if (user_query.lower() in article.get('title', '').lower() or 
                user_query.lower() in article.get('summary', '').lower()):
                relevant_articles.append(article)
        
        # If no direct matches, include some recent articles for context
        if len(relevant_articles) < 3:
            for article in recent_articles[:5]:
                if article not in relevant_articles:
                    relevant_articles.append(article)
                    if len(relevant_articles) >= 5:
                        break
        
        # Build context for AI
        context = "Available information:\n\n"
        for article in relevant_articles[:5]:  # Limit to 5 articles for context
            context += f"- {article.get('title')}\n"
            context += f"  Source: {article.get('source')}\n"
            context += f"  Summary: {article.get('summary', '')[:300]}...\n\n"
        
        # Prepare prompt for OpenAI
        system_prompt = (
            "You are an AI research assistant that helps analyze and explain scientific articles and tech news. "
            "Answer questions based on the provided article summaries. "
            "Be precise and clear. If the information is not available in the context, say so clearly. "
            "Refer to specific articles and research papers in your answers and compare sources when relevant."
        )
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'OpenAI API key not set. Please add it in your .env file or settings page.'
            }), 400
        
        try:
            response = client.chat.completions.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is information from various AI research and news sources:\n\n{context}\n\nUser question: {user_query}"}
                ],
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Add AI response to chat history
            chat_history.append({
                'role': 'assistant',
                'content': ai_response
            })
            
            # Update session
            session['chat_history'] = chat_history
            
            return jsonify({
                'success': True,
                'response': ai_response
            })
        
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error processing your request with our AI system. Please try again.'
            }), 500
    
    except Exception as e:
        logger.error(f"Chat API error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error processing chat: {str(e)}'
        }), 500

@app.route('/api/update_settings', methods=['POST'])
def api_update_settings():
    """Update application settings"""
    try:
        data = request.form
        
        # Get settings
        api_key = data.get('api_key')
        theme = data.get('theme', 'light')
        default_sources = data.getlist('default_sources')
        max_results = data.get('max_results', 10)
        
        # Update .env file with new settings
        env_path = Path('.env')
        
        # Create .env file if it doesn't exist
        if not env_path.exists():
            env_path.touch()
        
        # Read existing .env content
        env_content = env_path.read_text() if env_path.exists() else ''
        
        # Parse existing variables
        env_vars = {}
        for line in env_content.splitlines():
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        # Update variables
        if api_key:
            env_vars['OPENAI_API_KEY'] = api_key
        
        env_vars['THEME'] = theme
        env_vars['DEFAULT_SOURCES'] = ','.join(default_sources)
        env_vars['MAX_RESULTS'] = str(max_results)
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            for key, value in env_vars.items():
                # Quote the value if it contains spaces
                if ' ' in value:
                    value = f'"{value}"'
                f.write(f"{key}={value}\n")
        
        # Reload environment variables
        dotenv.load_dotenv(override=True)
        
        # If API key was updated, update the client
        if api_key:
            global client
            client = OpenAI(api_key=api_key)
        
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully'
        })
    
    except Exception as e:
        logger.error(f"Settings update error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error updating settings: {str(e)}'
        }), 500

@app.route('/api/export', methods=['POST'])
def api_export():
    """Export reports to various formats"""
    try:
        export_format = request.form.get('format', 'json')
        
        # Get articles to export
        article_ids = request.form.getlist('articles')
        
        if article_ids and article_ids[0] != 'all':
            # Fetch specific articles
            articles = []
            # This would need to be implemented in db_manager
        else:
            # Fetch all recent articles
            articles = db_manager.get_recent_articles(hours=24*7)  # Last week
        
        # Generate export filename
        date_str = datetime.today().strftime('%Y-%m-%d')
        filename = f"AI_Research_Summary_{date_str}.{export_format}"
        export_path = os.path.join('summary', filename)
        
        # Export based on format
        if export_format == 'json':
            # Convert articles to JSON
            with open(export_path, 'w') as f:
                json.dump(articles, f, indent=2)
        else:
            # Default to text export
            with open(export_path, 'w') as f:
                f.write(f"AI Research Summary - {date_str}\n\n")
                
                for article in articles:
                    f.write(f"Title: {article.get('title')}\n")
                    f.write(f"Source: {article.get('source')}\n")
                    f.write(f"Date: {article.get('pub_date')}\n")
                    f.write(f"Link: {article.get('link')}\n")
                    f.write(f"Summary: {article.get('summary')}\n\n")
                    f.write("-" * 80 + "\n\n")
        
        # Signal success and provide download link
        return jsonify({
            'success': True,
            'message': 'Export completed successfully',
            'file_url': url_for('download_file', filename=filename)
        })
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error exporting data: {str(e)}'
        }), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Route to download exported files"""
    try:
        file_path = os.path.join('summary', filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Download error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error downloading file: {str(e)}'
        }), 500

@app.route('/api/get-data')
def get_data():
    """API endpoint to get data for dashboard"""
    try:
        # Get recent articles
        recent_articles = db_manager.get_recent_articles(hours=24*7)
        
        # Format data for frontend
        data = {
            'articles': recent_articles,
            'meta': {
                'total': len(recent_articles),
                'last_updated': datetime.now().isoformat()
            }
        }
        
        return jsonify(data)
    except Exception as e:
        logger.error(f"API error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error retrieving data: {str(e)}'
        }), 500

# Custom template filters
@app.template_filter('format_date')
def format_date_filter(date_string):
    """Format date string for display"""
    if not date_string:
        return ''
    
    try:
        date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_obj.strftime('%b %d, %Y')
    except:
        return date_string

@app.template_filter('now')
def now_filter(format_string):
    """Return current date/time in specified format"""
    return datetime.now().strftime(format_string)

@app.template_filter('truncate_text')
def truncate_text_filter(text, length=100):
    """Truncate text to specified length"""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length] + '...'

# Create .env file if it doesn't exist
def init_env_file():
    env_path = Path('.env')
    if not env_path.exists():
        default_env = """# AI Research Hub Environment Variables
# Add your OpenAI API key here
OPENAI_API_KEY=

# Settings
FLASK_SECRET_KEY=replace_with_a_secure_random_key
OPENAI_MODEL=gpt-3.5-turbo
THEME=light
DEFAULT_SOURCES=arxiv,techcrunch,venturebeat
MAX_RESULTS=10
DB_PATH=research_data.db
"""
        with open(env_path, 'w') as f:
            f.write(default_env)
        logger.info(".env file created. Please add your OpenAI API key.")

# Run the app
if __name__ == '__main__':
    # Initialize environment file if needed
    init_env_file()
    
    # Check if API key is set
    if not os.environ.get('OPENAI_API_KEY'):
        logger.warning("OpenAI API key not set. Please add it to your .env file.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)