"""
Upstash Redis caching service with MCP tools integration
"""
import os
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import redis
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class UpstashRedisCache:
    """Redis caching service using Upstash with fallback to local Redis"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.cache_enabled = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
        
        if not self.cache_enabled:
            logger.info("Cache is disabled")
            return
        
        # Try Upstash first, fallback to local Redis in development
        self.client = self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Redis client with Upstash or local Redis"""
        # Try Upstash REST API first
        upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')
        upstash_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        
        if upstash_url and upstash_token:
            logger.info(f"Using Upstash Redis for {self.environment}")
            return UpstashRestClient(upstash_url, upstash_token)
        
        # Fallback to local Redis in development
        if self.environment == 'development':
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            try:
                client = redis.from_url(redis_url, decode_responses=True)
                client.ping()
                logger.info("Using local Redis for development")
                return LocalRedisClient(client)
            except Exception as e:
                logger.warning(f"Failed to connect to local Redis: {e}")
        
        logger.warning("No Redis cache available")
        return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache_enabled or not self.client:
            return None
        
        try:
            prefixed_key = self._prefix_key(key)
            value = self.client.get(prefixed_key)
            
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value) if isinstance(value, str) else value
            
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds"""
        if not self.cache_enabled or not self.client:
            return False
        
        try:
            prefixed_key = self._prefix_key(key)
            # Always JSON encode the value for consistency
            json_value = json.dumps(value)
            
            result = self.client.setex(prefixed_key, ttl, json_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.cache_enabled or not self.client:
            return False
        
        try:
            prefixed_key = self._prefix_key(key)
            result = self.client.delete(prefixed_key)
            logger.debug(f"Cache delete: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.cache_enabled or not self.client:
            return 0
        
        try:
            prefixed_pattern = self._prefix_key(pattern)
            deleted = self.client.delete_pattern(prefixed_pattern)
            logger.debug(f"Cache delete pattern: {pattern} (deleted: {deleted})")
            return deleted
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def clear_user_cache(self, user_id: str):
        """Clear all cache for a specific user"""
        patterns = [
            f"user:{user_id}:*",
            f"workout:{user_id}:*",
            f"nutrition:{user_id}:*",
            f"progress:{user_id}:*",
            f"measurements:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = self.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Cleared {total_deleted} cache keys for user {user_id}")
        return total_deleted
    
    def _prefix_key(self, key: str) -> str:
        """Add environment prefix to key"""
        return f"{self.environment}:{key}"
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()


class UpstashRestClient:
    """Upstash Redis REST API client"""
    
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.headers = {'Authorization': f'Bearer {token}'}
    
    def get(self, key: str) -> Optional[str]:
        response = requests.get(f"{self.url}/get/{key}", headers=self.headers)
        if response.status_code == 200:
            try:
                data = response.json()
                return data.get('result')
            except json.JSONDecodeError:
                # Upstash might return plain text for some operations
                return response.text if response.text != 'null' else None
        return None
    
    def setex(self, key: str, seconds: int, value: str) -> bool:
        # Upstash REST API format: /set/key/value/ex/seconds
        # URL encode the value to handle special characters
        encoded_value = quote(value, safe='')
        response = requests.post(
            f"{self.url}/set/{key}/{encoded_value}/ex/{seconds}",
            headers=self.headers
        )
        return response.status_code == 200 and response.json().get('result') == 'OK'
    
    def delete(self, key: str) -> bool:
        response = requests.post(f"{self.url}/del/{key}", headers=self.headers)
        return response.status_code == 200
    
    def delete_pattern(self, pattern: str) -> int:
        # Get all keys matching pattern
        cursor = 0
        deleted = 0
        
        while True:
            response = requests.get(
                f"{self.url}/scan/{cursor}/match/{pattern}/count/100",
                headers=self.headers
            )
            
            if response.status_code != 200:
                break
            
            data = response.json()
            cursor = data.get('result', [0])[0]
            keys = data.get('result', [0, []])[1]
            
            # Delete found keys
            for key in keys:
                if self.delete(key):
                    deleted += 1
            
            if cursor == 0:
                break
        
        return deleted


class LocalRedisClient:
    """Wrapper for local Redis client to match Upstash interface"""
    
    def __init__(self, client: redis.Redis):
        self.client = client
    
    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)
    
    def setex(self, key: str, seconds: int, value: str) -> bool:
        return self.client.setex(key, seconds, value)
    
    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))
    
    def delete_pattern(self, pattern: str) -> int:
        keys = list(self.client.scan_iter(match=pattern))
        if keys:
            return self.client.delete(*keys)
        return 0


# Cache decorator
def cache_result(ttl: int = 3600, key_prefix: str = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache instance
            cache = kwargs.pop('_cache', None) or UpstashRedisCache()
            
            # Generate cache key
            cache_key_parts = [key_prefix or func.__name__]
            cache_key_parts.extend(str(arg) for arg in args)
            cache_key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(cache_key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Initialize default cache instance
default_cache = UpstashRedisCache()


# MCP Tool Integration Functions
async def create_redis_database(name: str, region: str, read_regions: List[str] = None):
    """Create new Upstash Redis database using MCP tools"""
    # This would be called from a separate MCP integration module
    pass


async def get_redis_stats(database_id: str, period: str = "1h"):
    """Get Redis usage statistics using MCP tools"""
    # This would be called from a separate MCP integration module
    pass