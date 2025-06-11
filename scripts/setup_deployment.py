#!/usr/bin/env python3
"""
Setup script for configuring deployment environments
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from services.supabase_mcp import SupabaseMCP, run_migrations
from services.digitalocean_mcp import DigitalOceanMCP, setup_new_app
from services.redis_cache import UpstashRedisCache
from migrations.migration_runner import MigrationRunner, create_initial_schema_migration


async def setup_supabase(environment: str):
    """Set up Supabase for environment"""
    print(f"\n🔧 Setting up Supabase for {environment}...")
    
    mcp = SupabaseMCP(environment)
    
    # Check connection
    try:
        project = await mcp.get_project_details()
        print(f"✅ Connected to Supabase project: {project.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False
    
    # Run migrations
    print("📋 Running database migrations...")
    migrations_applied = await run_migrations(environment)
    print(f"✅ Applied {migrations_applied} migrations")
    
    return True


async def setup_redis(environment: str):
    """Set up Redis cache for environment"""
    print(f"\n🔧 Setting up Redis cache for {environment}...")
    
    cache = UpstashRedisCache(environment)
    
    # Test connection
    if cache.client:
        test_key = f'{environment}:setup:test'
        if cache.set(test_key, 'ok', ttl=10):
            cache.delete(test_key)
            print("✅ Redis cache is working")
            return True
    
    print("❌ Redis cache is not configured or not working")
    return False


async def setup_digitalocean(environment: str):
    """Set up DigitalOcean app for environment"""
    print(f"\n🔧 Setting up DigitalOcean app for {environment}...")
    
    try:
        app = await setup_new_app(environment)
        print(f"✅ DigitalOcean app configured: {app.get('id')}")
        return True
    except Exception as e:
        print(f"❌ Failed to set up DigitalOcean app: {e}")
        return False


async def verify_environment(environment: str):
    """Verify environment configuration"""
    print(f"\n🔍 Verifying {environment} environment configuration...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'UPSTASH_REDIS_REST_URL',
        'UPSTASH_REDIS_REST_TOKEN'
    ]
    
    if environment == 'production':
        required_vars.extend([
            'SENTRY_DSN',
            'PROD_APP_ID'
        ])
    else:
        required_vars.append('DEV_APP_ID')
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables are set")
    return True


async def main():
    parser = argparse.ArgumentParser(description='Set up deployment environment')
    parser.add_argument('environment', choices=['development', 'production'],
                        help='Environment to set up')
    parser.add_argument('--component', choices=['all', 'supabase', 'redis', 'digitalocean'],
                        default='all', help='Component to set up')
    parser.add_argument('--create-migration', action='store_true',
                        help='Create initial schema migration')
    
    args = parser.parse_args()
    
    # Load environment file
    env_file = f'.env.{args.environment[:4]}'  # .env.dev or .env.prod
    if Path(env_file).exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"❌ Environment file {env_file} not found")
        return
    
    # Create initial migration if requested
    if args.create_migration:
        migration_file = create_initial_schema_migration()
        print(f"✅ Created migration: {migration_file}")
        return
    
    # Verify environment
    if not await verify_environment(args.environment):
        print("\n❌ Please set all required environment variables")
        return
    
    print(f"\n🚀 Setting up {args.environment} environment...")
    
    success = True
    
    # Set up components
    if args.component in ['all', 'supabase']:
        success &= await setup_supabase(args.environment)
    
    if args.component in ['all', 'redis']:
        success &= await setup_redis(args.environment)
    
    if args.component in ['all', 'digitalocean']:
        success &= await setup_digitalocean(args.environment)
    
    if success:
        print(f"\n✅ {args.environment} environment setup complete!")
    else:
        print(f"\n❌ Some components failed to set up")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())