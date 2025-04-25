import os
import logging
import streamlit as st

# Load .env file if it exists
# load_dotenv()

# def get_api_key(key_name):
#     """Get an API key from environment variables with fallback to key.py"""
#     env_key = os.getenv(key_name)
#     if env_key:
#         return env_key
    
    # # Fallback to key.py if environment variable is not set
    # try:
    #     import key
    #     if hasattr(key, key_name):
    #         logging.warning(f"Using {key_name} from key.py - consider moving to environment variables")
    #         return getattr(key, key_name)
    # except ImportError:
    #     pass
    
    # logging.error(f"{key_name} not found in environment variables or key.py")
    # return None

# def get_openai_key():
#     """Get OpenAI API key"""
#     return get_api_key("OPENAI_API_KEY")

def get_openai_key():
    """Get OpenAI API key"""
    return st.secrets["api"]["key"]