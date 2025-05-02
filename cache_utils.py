import functools
import pickle
import os
import hashlib
import time
import logging

CACHE_DIR = "cache"
DEFAULT_EXPIRY = 3600  # 1 hour in seconds

def setup_cache():
    """Ensure cache directory exists"""
    os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_key(func_name, args, kwargs):
    """Generate a cache key based on function name and arguments"""
    args_str = str(args) + str(kwargs)
    hash_key = hashlib.md5(args_str.encode()).hexdigest()
    return f"{func_name}_{hash_key}"

def cached(expiry=DEFAULT_EXPIRY):
    """Decorator to cache function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            setup_cache()
            cache_key = get_cache_key(func.__name__, args, kwargs)
            cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
            
            # Check if cache exists and is not expired
            if os.path.exists(cache_file):
                file_age = time.time() - os.path.getmtime(cache_file)
                if file_age < expiry:
                    try:
                        with open(cache_file, 'rb') as f:
                            result = pickle.load(f)
                            logging.info(f"Cache hit for {func.__name__}")
                            return result
                    except Exception as e:
                        logging.warning(f"Cache read error: {e}")
            
            # Cache miss or expired - execute function
            result = func(*args, **kwargs)
            
            # Save result to cache
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
            except Exception as e:
                logging.warning(f"Cache write error: {e}")
                
            return result
        return wrapper
    return decorator

def get_cached_data(key):
    """Retrieve data from cache by key"""
    setup_cache()
    cache_file = os.path.join(CACHE_DIR, f"{key}.pkl")
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logging.warning(f"Cache read error: {e}")
    
    return None

def save_to_cache(key, data, expiry=DEFAULT_EXPIRY):
    """Save data to cache with specified key"""
    setup_cache()
    cache_file = os.path.join(CACHE_DIR, f"{key}.pkl")
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        logging.warning(f"Cache write error: {e}")
        return False