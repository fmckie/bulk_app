#!/usr/bin/env python3
"""
Test script to verify your setup
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
env_file = '.env.dev'
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded {env_file}")
else:
    print(f"❌ {env_file} not found")
    sys.exit(1)

print("\n🔍 Checking environment variables...")

# Check Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
if supabase_url and supabase_key:
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Supabase Key: {supabase_key[:20]}...")
else:
    print("❌ Supabase credentials missing")

# Check Redis
redis_url = os.getenv('UPSTASH_REDIS_REST_URL')
redis_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
if redis_url and redis_token:
    print(f"✅ Upstash Redis URL: {redis_url}")
    print(f"✅ Upstash Redis Token: {redis_token[:20]}...")
else:
    print("⚠️  Upstash Redis not configured (optional)")

# Test Supabase connection
print("\n🔍 Testing Supabase connection...")
try:
    from database.connection import check_supabase_connection
    if check_supabase_connection():
        print("✅ Supabase connection successful")
    else:
        print("❌ Supabase connection failed")
except Exception as e:
    print(f"❌ Error testing Supabase: {e}")

# Test Redis cache
print("\n🔍 Testing Redis cache...")
try:
    from services.redis_cache import UpstashRedisCache
    cache = UpstashRedisCache()
    if cache.client:
        if cache.set('test:key', 'test-value', ttl=10):
            value = cache.get('test:key')
            if value == 'test-value':
                print("✅ Redis cache working")
                cache.delete('test:key')
            else:
                print("❌ Redis cache read failed")
        else:
            print("❌ Redis cache write failed")
    else:
        print("⚠️  Redis cache not available (will work without it)")
except Exception as e:
    print(f"⚠️  Redis cache error: {e}")

print("\n✨ Setup verification complete!")