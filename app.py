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
from relevance import calculate_relevance
from cache_utils import get_cached_data, save_to_cache

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
def now_filter(format="%Y-%m-%d %H:%M:%S"):
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
                sources = sorted(sources, key=lambda x: calculate_relevance(query, x), reverse=True)
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

if __name__ == '__main__':
    app.run(debug=True)