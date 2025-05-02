from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
import os
import datetime
import json
import openai
# Fix imports - import whole modules instead of specific classes that don't exist
import arxiv_scraper
import techcrunch
import theverge
import thn
import venture_beat
import stanford_ai
from relevance import analyze_relevance
from cache_utils import save_to_cache, get_cached_data

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())

# Get API keys from environment variables
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ARXIV_API_KEY = os.environ.get('ARXIV_API_KEY')  # If applicable

# Initialize OpenAI client with the API key
openai.api_key = OPENAI_API_KEY

# We don't need to initialize scrapers here - we'll call their main functions directly

# Utility functions
def now(format="%Y-%m-%d %H:%M:%S"):
    """Return current time in specified format"""
    return datetime.datetime.now().strftime(format)

@app.template_filter('now')
def now_filter(format="%Y-%m-%d %H:%M:%S", *args, **kwargs):
    """Flask template filter to get current time"""
    return now(format)

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard route"""
    return render_template('dashboard.html')

@app.route('/chat')
def chat():
    """Chat interface route"""
    # Check if we need to reset the chat
    if request.args.get('reset'):
        if 'chat_history' in session:
            session.pop('chat_history')
    
    # Initialize chat history if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Get user preferences
    preferences = {
        'api_key_set': bool(OPENAI_API_KEY),
        'model': 'gpt-3.5-turbo'
    }
    
    return render_template('chat.html', chat_history=session.get('chat_history', []), preferences=preferences)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat functionality"""
    if not OPENAI_API_KEY:
        return jsonify({
            'success': False,
            'message': 'OpenAI API key not set. Please add your API key in the .env file.'
        })
    
    try:
        # Get request data
        data = request.get_json()
        query = data.get('query', '')
        model = data.get('model', 'gpt-3.5-turbo')
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'No query provided'
            })
        
        # Update chat history in session
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        session['chat_history'].append({
            'role': 'user',
            'content': query,
            'timestamp': now('%I:%M %p')
        })
        
        # Search for relevant content across all sources
        sources = []
        
        # Try to get cached data first
        cache_key = f"query_{hash(query)}"
        cached_result = get_cached_data(cache_key)
        
        if cached_result:
            sources = cached_result
        else:
            # Query all data sources
            # Update this section to use the correct function calls
            try:
                # Get arxiv results - assume search functionality is available
                if hasattr(arxiv_scraper, 'search_arxiv'):
                    arxiv_results = arxiv_scraper.search_arxiv(query, max_results=5)
                else:
                    # Fall back to main function and filter results
                    all_arxiv = arxiv_scraper.main_arxiv()
                    arxiv_results = [
                        {"title": title, "content": data["summary"], "url": data["link"], "date": data["published"]} 
                        for title, data in all_arxiv.items() 
                        if query.lower() in title.lower() or query.lower() in data["summary"].lower()
                    ][:5]
                sources.extend(arxiv_results)
            except Exception as e:
                app.logger.error(f"Error querying ArXiv: {str(e)}")
            
            try:
                # Get TechCrunch results
                tech_results = techcrunch.main_techcrunch()
                # Filter by query
                filtered_tech = [
                    {"title": item[0], "content": item[2], "url": item[1], "date": "Recent"} 
                    for item in tech_results 
                    if query.lower() in item[0].lower() or query.lower() in item[2].lower()
                ][:3]
                sources.extend(filtered_tech)
            except Exception as e:
                app.logger.error(f"Error querying TechCrunch: {str(e)}")
            
            try:
                # Get The Verge results
                verge_results = theverge.main_verge()
                # Filter by query
                filtered_verge = [
                    {"title": item[0], "content": item[2], "url": item[1], "date": "Recent"} 
                    for item in verge_results 
                    if query.lower() in item[0].lower() or query.lower() in item[2].lower()
                ][:3]
                sources.extend(filtered_verge)
            except Exception as e:
                app.logger.error(f"Error querying The Verge: {str(e)}")
            
            try:
                # Get The Hacker News results
                thn_results = thn.main_thn()
                # Filter by query
                filtered_thn = [
                    {"title": item[0], "content": item[2], "url": item[1], "date": "Recent"} 
                    for item in thn_results 
                    if query.lower() in item[0].lower() or query.lower() in item[2].lower()
                ][:3]
                sources.extend(filtered_thn)
            except Exception as e:
                app.logger.error(f"Error querying THN: {str(e)}")
            
            try:
                # Get VentureBeat results
                vb_results = venture_beat.main_venturebeat()
                # Filter by query
                filtered_vb = [
                    {"title": item[0], "content": item[2], "url": item[1], "date": "Recent"} 
                    for item in vb_results 
                    if query.lower() in item[0].lower() or query.lower() in item[2].lower()
                ][:3]
                sources.extend(filtered_vb)
            except Exception as e:
                app.logger.error(f"Error querying VentureBeat: {str(e)}")
            
            try:
                # Get Stanford AI results
                stanford_results = stanford_ai.main_stanford()
                # Filter by query
                filtered_stanford = [
                    {"title": item[0], "content": item[2], "url": item[1], "date": "Recent"} 
                    for item in stanford_results 
                    if query.lower() in item[0].lower() or query.lower() in item[2].lower()
                ][:3]
                sources.extend(filtered_stanford)
            except Exception as e:
                app.logger.error(f"Error querying Stanford AI: {str(e)}")
            
            # Sort by relevance if calculate_relevance is implemented correctly
            try:
                sources = sorted(sources, key=lambda x: analyze_relevance(query, x), reverse=True)
            except Exception as e:
                app.logger.error(f"Error calculating relevance: {str(e)}")
            
            # Cache the results
            save_to_cache(cache_key, sources)
        
        # Format sources for the AI prompt
        formatted_sources = ""
        for idx, source in enumerate(sources[:10]):  # Limit to top 10 most relevant
            title = source.get('title', 'Unknown Title')
            content = source.get('content', 'No content available')
            url = source.get('url', '#')
            date = source.get('date', 'Unknown date')
            
            # Truncate content if too long
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            formatted_sources += f"SOURCE {idx+1}:\n"
            formatted_sources += f"Title: {title}\n"
            formatted_sources += f"Date: {date}\n"
            formatted_sources += f"URL: {url}\n"
            formatted_sources += f"Content: {content}\n\n"
        
        # Create conversation history for OpenAI
        conversation = [
            {"role": "system", "content": f"""You are a helpful AI research assistant. You have access to the following research sources. 
            When answering questions, use these sources to provide accurate, cited information. 
            If you don't know something or can't find it in the sources, admit that you don't know.
            Always cite your sources by referencing the source number [SOURCE X] and provide quotations when directly quoting.
            
            SOURCES:
            {formatted_sources}"""}
        ]
        
        # Add previous messages for context (limited to last 10 to save tokens)
        history = session.get('chat_history', [])
        for msg in history[-10:]:
            if msg['role'] == 'user':
                conversation.append({"role": "user", "content": msg['content']})
            else:
                conversation.append({"role": "assistant", "content": msg['content']})
                
        # Generate response from OpenAI
        try:
            # Verwende moderne OpenAI API-Syntax
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            
            response = client.chat.completions.create(
                model=model,
                messages=conversation,
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
        except AttributeError:
            # Fallback für ältere OpenAI API-Versionen
            response = openai.ChatCompletion.create(
                model=model,
                messages=conversation,
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
        
        # Add AI response to chat history
        session['chat_history'].append({
            'role': 'assistant',
            'content': ai_response,
            'timestamp': now('%I:%M %p')
        })
        session.modified = True
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'sources_count': len(sources)
        })
        
    except Exception as e:
        app.logger.error(f"Error processing chat: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        })

@app.route('/settings')
def settings():
    """Settings page route"""
    # Get current settings
    settings = {
        'api_key_set': bool(OPENAI_API_KEY),
        'model': 'gpt-3.5-turbo'
    }
    return render_template('settings.html', settings=settings)

@app.route('/sources')
def sources():
    """Sources page route"""
    return render_template('sources.html')

@app.route('/api/fetch_data', methods=['POST'])
def fetch_data():
    """API endpoint to fetch data based on selected sources and settings"""
    try:
        # Parse the incoming JSON data
        data = request.get_json()
        sources = data.get('sources', [])
        arxiv_category = data.get('arxiv_category', 'cs.LG')
        max_articles = int(data.get('max_articles', 10))
        citation_styles = data.get('citation_styles', [])

        if not sources:
            return jsonify({
                'success': False,
                'message': 'No sources selected.'
            }), 400

        # Placeholder for fetched data
        fetched_data = {}

        # Fetch data from each selected source
        if 'arxiv' in sources:
            try:
                fetched_data['arxiv'] = arxiv_scraper.main_arxiv(categories=[arxiv_category], max_results=max_articles, citation_styles=citation_styles)
                app.logger.info(f"ArXiv data structure: {type(fetched_data['arxiv'])}")
            except Exception as e:
                app.logger.error(f"Error fetching ArXiv data: {str(e)}")
                fetched_data['arxiv'] = {}

        if 'techcrunch' in sources:
            try:
                tech_results = techcrunch.main_techcrunch()
                if tech_results:
                    fetched_data['techcrunch'] = tech_results[:max_articles]
                app.logger.info(f"TechCrunch data structure: {type(fetched_data['techcrunch'])}")
            except Exception as e:
                app.logger.error(f"Error fetching TechCrunch data: {str(e)}")
                fetched_data['techcrunch'] = []

        if 'venturebeat' in sources:
            try:
                vb_results = venture_beat.main_venturebeat()
                if vb_results:
                    fetched_data['venturebeat'] = vb_results[:max_articles]
                app.logger.info(f"VentureBeat data structure: {type(fetched_data['venturebeat'])}")
            except Exception as e:
                app.logger.error(f"Error fetching VentureBeat data: {str(e)}")
                fetched_data['venturebeat'] = []

        if 'stanford' in sources:
            try:
                stanford_results = stanford_ai.main_stanford()
                if stanford_results:
                    fetched_data['stanford'] = stanford_results[:max_articles]
                app.logger.info(f"Stanford data structure: {type(fetched_data['stanford'])}")
            except Exception as e:
                app.logger.error(f"Error fetching Stanford AI data: {str(e)}")
                fetched_data['stanford'] = []

        if 'theverge' in sources:
            try:
                verge_results = theverge.main_verge()
                if verge_results:
                    fetched_data['theverge'] = verge_results[:max_articles]
                app.logger.info(f"TheVerge data structure: {type(fetched_data['theverge'])}")
            except Exception as e:
                app.logger.error(f"Error fetching The Verge data: {str(e)}")
                fetched_data['theverge'] = []

        if 'thehackernews' in sources:
            try:
                thn_results = thn.main_thn()
                if thn_results:
                    fetched_data['thehackernews'] = thn_results[:max_articles]
                app.logger.info(f"THN data structure: {type(fetched_data['thehackernews'])}")
            except Exception as e:
                app.logger.error(f"Error fetching THN data: {str(e)}")
                fetched_data['thehackernews'] = []

        # Log the fetched data for debugging
        app.logger.info(f"Fetched data: {json.dumps(fetched_data, indent=2)}")

        # Return the fetched data
        return jsonify({
            'success': True,
            'data': fetched_data
        })

    except Exception as e:
        app.logger.error(f"Error in fetch_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500

@app.route('/get-data', methods=['GET', 'POST'])
def get_dashboard_data():
    """API endpoint to get data for the dashboard"""
    try:
        # Define how many articles we want to fetch
        max_results = 5
        
        # Get selected sources from request
        sources_to_fetch = []
        if request.method == 'POST':
            data = request.get_json() or {}
            sources_to_fetch = data.get('sources', [])
            
            # Validate sources to fetch
            valid_sources = ['arxiv', 'techcrunch', 'venturebeat', 'stanford', 'theverge', 'thehackernews']
            sources_to_fetch = [s for s in sources_to_fetch if s in valid_sources]
            
            # If no valid sources provided, return empty data
            if not sources_to_fetch:
                return jsonify({
                    'success': True,
                    'recentArticles': [],
                    'topKeywords': [],
                    'trendingTopics': [],
                    'sourceStats': {'sources': {}, 'totalArticles': 0},
                    'last_updated': now()
                })
        else:
            # For GET requests, return empty data and ask for source selection
            return jsonify({
                'success': True,
                'recentArticles': [],
                'topKeywords': [],
                'trendingTopics': [],
                'sourceStats': {'sources': {}, 'totalArticles': 0},
                'last_updated': now(),
                'message': 'Please select sources to fetch data'
            })
            
        app.logger.info(f"Fetching data for sources: {sources_to_fetch}")
        
        # Check if we have cached data for these exact sources
        cache_key = f"dashboard_data_{'-'.join(sorted(sources_to_fetch))}"
        cached_data = get_cached_data(cache_key)
        
        if cached_data:
            app.logger.info("Using cached dashboard data")
            return jsonify({
                'recentArticles': cached_data.get('recentArticles', []),
                'topKeywords': cached_data.get('topKeywords', []),
                'trendingTopics': cached_data.get('trendingTopics', []),
                'sourceStats': cached_data.get('sourceStats', {'sources': {}, 'totalArticles': 0}),
                'last_updated': cached_data.get('last_updated', now()),
                'fromCache': True
            })
        
        # If no cached data, fetch fresh data
        all_data = {}
        
        # Fetch data from each selected source
        if 'arxiv' in sources_to_fetch:
            try:
                all_data['arxiv'] = arxiv_scraper.main_arxiv(categories=['cs.AI', 'cs.LG'], max_results=max_results)
            except Exception as e:
                app.logger.error(f"Error fetching ArXiv data: {str(e)}")
            
        if 'techcrunch' in sources_to_fetch:
            try:
                tech_results = techcrunch.main_techcrunch()
                if tech_results:
                    all_data['techcrunch'] = tech_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching TechCrunch data: {str(e)}")
            
        if 'theverge' in sources_to_fetch:
            try:
                verge_results = theverge.main_verge()
                if verge_results:
                    all_data['theverge'] = verge_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching The Verge data: {str(e)}")
        
        if 'thehackernews' in sources_to_fetch:
            try:
                thn_results = thn.main_thn()
                if thn_results:
                    all_data['thehackernews'] = thn_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching THN data: {str(e)}")
            
        if 'venturebeat' in sources_to_fetch:
            try:
                vb_results = venture_beat.main_venturebeat()
                if vb_results:
                    all_data['venturebeat'] = vb_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching VentureBeat data: {str(e)}")
            
        if 'stanford' in sources_to_fetch:
            try:
                stanford_results = stanford_ai.main_stanford()
                if stanford_results:
                    all_data['stanford'] = stanford_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching Stanford AI data: {str(e)}")
        
        # Extract keywords for visualization
        keywords = {}
        sources_count = {}
        dates_count = {}
        
        # Process ArXiv data for keywords
        if 'arxiv' in all_data and all_data['arxiv']:
            sources_count['ArXiv'] = len(all_data['arxiv'])
            for title, article_data in all_data['arxiv'].items():
                # Process date
                pub_date = article_data.get('published', '')
                if pub_date:
                    date_str = pub_date[:10] if isinstance(pub_date, str) else pub_date.strftime('%Y-%m-%d')
                    dates_count[date_str] = dates_count.get(date_str, 0) + 1
                
                # Extract keywords from title and summary
                for keyword in extract_keywords(title + " " + article_data.get('summary', '')):
                    keywords[keyword] = keywords.get(keyword, 0) + 1
                    
        # Process other sources
        for source_name, articles in all_data.items():
            if source_name != 'arxiv' and articles:
                sources_count[source_name.capitalize()] = len(articles)
                for article in articles:
                    if isinstance(article, list) and len(article) >= 3:
                        title = article[0]
                        content = article[2]
                        for keyword in extract_keywords(title + " " + content):
                            keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Prepare flattened recentArticles list
        recent_articles_list = []
        # Process ArXiv articles
        if 'arxiv' in all_data and isinstance(all_data['arxiv'], dict):
            for title, art in all_data['arxiv'].items():
                recent_articles_list.append({
                    'title': title,
                    'summary': art.get('summary', ''),
                    'source': 'arxiv',
                    'url': art.get('link', '#'),
                    'date': art.get('published', ''),
                    'relevance': 0
                })
        # Process other sources (list of [title, link, summary])
        for src in sources_to_fetch:
            if src != 'arxiv' and src in all_data and isinstance(all_data[src], list):
                for art in all_data[src]:
                    title = art[0] if len(art) > 0 else ''
                    url = art[1] if len(art) > 1 else '#'
                    summary = art[2] if len(art) > 2 else ''
                    date = art[3] if len(art) > 3 else ''
                    recent_articles_list.append({
                        'title': title,
                        'summary': summary,
                        'source': src,
                        'url': url,
                        'date': date,
                        'relevance': 0
                    })
        
        # Limit to 20 articles
        limited_articles = recent_articles_list[:20]
        
        # Prepare topKeywords and trendingTopics
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [{'term': k, 'count': v} for k, v in sorted_keywords[:10]]
        trending = [{'term': k, 'count': v, 'trend': v} for k, v in sorted_keywords[:7]]
        
        # Prepare sourceStats
        total_articles = sum(sources_count.values())
        source_stats = {'sources': sources_count, 'totalArticles': total_articles}
        
        # Prepare final dashboard data
        dashboard_data = {
            'recentArticles': limited_articles,
            'topKeywords': top_keywords,
            'trendingTopics': trending,
            'sourceStats': source_stats,
            'last_updated': now(),
            'selectedSources': sources_to_fetch
        }
        
        # Cache the data with sources in the key
        save_to_cache(cache_key, dashboard_data)
        
        # Return JSON matching front-end schema
        return jsonify(dashboard_data)
    
    except Exception as e:
        app.logger.error(f"Error in get_dashboard_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500

@app.route('/refresh-dashboard', methods=['POST'])
def refresh_dashboard_cache():
    """Force refresh the dashboard data cache"""
    try:
        # Get selected sources from request if available
        data = request.get_json() or {}
        sources_to_fetch = data.get('sources', [])
        
        # Validate sources to fetch
        valid_sources = ['arxiv', 'techcrunch', 'venturebeat', 'stanford', 'theverge', 'thehackernews']
        sources_to_fetch = [s for s in sources_to_fetch if s in valid_sources]
        
        # Wenn keine gültigen Quellen vorhanden sind, leere Daten zurückgeben
        if not sources_to_fetch:
            return jsonify({
                'success': False,
                'message': 'No valid sources selected.'
            }), 400
        
        app.logger.info(f"Refreshing dashboard with sources: {sources_to_fetch}")
        
        # Definiere Cache-Schlüssel basierend auf ausgewählten Quellen
        cache_key = f"dashboard_data_{'-'.join(sorted(sources_to_fetch))}"
        
        # Fetch fresh data for the dashboard
        max_results = 5
        all_data = {}
        
        # Fetch data only from selected sources
        if 'arxiv' in sources_to_fetch:
            try:
                all_data['arxiv'] = arxiv_scraper.main_arxiv(categories=['cs.AI', 'cs.LG'], max_results=max_results)
            except Exception as e:
                app.logger.error(f"Error fetching ArXiv data: {str(e)}")
            
        if 'techcrunch' in sources_to_fetch:
            try:
                tech_results = techcrunch.main_techcrunch()
                if tech_results:
                    all_data['techcrunch'] = tech_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching TechCrunch data: {str(e)}")
            
        if 'theverge' in sources_to_fetch:
            try:
                verge_results = theverge.main_verge()
                if verge_results:
                    all_data['theverge'] = verge_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching The Verge data: {str(e)}")
        
        if 'thehackernews' in sources_to_fetch:
            try:
                thn_results = thn.main_thn()
                if thn_results:
                    all_data['thehackernews'] = thn_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching THN data: {str(e)}")
            
        if 'venturebeat' in sources_to_fetch:
            try:
                vb_results = venture_beat.main_venturebeat()
                if vb_results:
                    all_data['venturebeat'] = vb_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching VentureBeat data: {str(e)}")
            
        if 'stanford' in sources_to_fetch:
            try:
                stanford_results = stanford_ai.main_stanford()
                if stanford_results:
                    all_data['stanford'] = stanford_results[:max_results]
            except Exception as e:
                app.logger.error(f"Error fetching Stanford AI data: {str(e)}")
        
        # Extract keywords, counts, etc. for dashboard visualizations
        keywords = {}
        sources_count = {}
        dates_count = {}
        
        # Process ArXiv data
        if 'arxiv' in all_data and all_data['arxiv']:
            sources_count['ArXiv'] = len(all_data['arxiv'])
            for title, article_data in all_data['arxiv'].items():
                # Process date
                pub_date = article_data.get('published', '')
                if pub_date:
                    date_str = pub_date[:10] if isinstance(pub_date, str) else pub_date.strftime('%Y-%m-%d')
                    dates_count[date_str] = dates_count.get(date_str, 0) + 1
                
                # Extract keywords from title and summary
                for keyword in extract_keywords(title + " " + article_data.get('summary', '')):
                    keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Process other sources
        for source_name, articles in all_data.items():
            if source_name != 'arxiv' and articles:
                sources_count[source_name.capitalize()] = len(articles)
                for article in articles:
                    if isinstance(article, list) and len(article) >= 3:
                        title = article[0]
                        content = article[2]
                        for keyword in extract_keywords(title + " " + content):
                            keywords[keyword] = keywords.get(keyword, 0) + 1
        
        # Prepare dashboard data object
        dashboard_data = {
            'success': True,
            'last_updated': now(),
            'arxiv': all_data.get('arxiv', {}),
            'techcrunch': all_data.get('techcrunch', []),
            'theverge': all_data.get('theverge', []),
            'thehackernews': all_data.get('thehackernews', []),
            'venturebeat': all_data.get('venturebeat', []),
            'stanford': all_data.get('stanford', []),
            'keywords': keywords,
            'sources': sources_count,
            'dates': dates_count,
            'selected_sources': sources_to_fetch  # Save selected sources in cache
        }
        
        # Save to cache
        save_to_cache(cache_key, dashboard_data)
        
        return jsonify({
            'success': True,
            'message': 'Dashboard data cache refreshed',
            'data': dashboard_data
        })
    
    except Exception as e:
        app.logger.error(f"Error refreshing dashboard cache: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"An error occurred: {str(e)}"
        }), 500

def extract_keywords(text):
    """Simple keyword extraction from text - replace with a more sophisticated method if needed"""
    if not text:
        return []
        
    # Common stopwords
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when', 
                'where', 'how', 'why', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 
                'do', 'does', 'did', 'doing', 'to', 'for', 'with', 'by', 'about', 'in', 'on',
                'at', 'of', 'from'}
    
    # Extract words, convert to lowercase, filter by length and stopwords
    words = ''.join(c if c.isalnum() else ' ' for c in text).lower().split()
    keywords = [word for word in words if len(word) > 3 and word not in stopwords]
    
    # Return only unique keywords
    return list(set(keywords))

if __name__ == '__main__':
    app.run(debug=True)