import os
import logging
import dotenv

# Load .env file if it exists
dotenv.load_dotenv()

def get_api_key(key_name):
    """Get an API key from environment variables"""
    env_key = os.getenv(key_name)
    if env_key:
        return env_key
    
    logging.error(f"{key_name} not found in environment variables")
    return None

def get_openai_key():
    """Get OpenAI API key"""
    return get_api_key("OPENAI_API_KEY")