# Quick Start Guide

## Your Current Setup Status

✅ **Supabase**: Connected and working
- Project: `alknwmhlkjmrsxzeiuqv`
- Database schema already created
- Authentication configured

❌ **Redis Cache**: Not configured (optional)
⏳ **CI/CD**: Not configured (optional)

## Start Development Now

### Option 1: With Docker (Recommended)
```bash
# Start the development environment
docker-compose up

# Access your app at http://localhost:8000
```

### Option 2: Without Docker
```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python3 app.py

# Access your app at http://localhost:8000
```

## Next Steps (When You're Ready)

### 1. Set Up Redis Caching (Optional but Recommended)
**Benefits**: Faster page loads, reduced database queries

1. Go to [upstash.com](https://upstash.com) and create a free account
2. Create a new Redis database (select closest region)
3. Copy the REST URL and REST Token
4. Update `.env.dev`:
   ```
   UPSTASH_REDIS_REST_URL=https://your-actual-url.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your-actual-token
   ```

### 2. Set Up Production Environment (When Ready to Deploy)
1. **Create Production Supabase Project**:
   - Create new project at [supabase.com](https://supabase.com)
   - Run your `database/schema.sql` in SQL editor
   - Copy credentials to `.env.prod`

2. **Create Production Redis**:
   - Create another Redis database on Upstash
   - Copy credentials to `.env.prod`

### 3. Enable CI/CD (For Automated Deployments)
1. Push your code to GitHub
2. Add secrets to GitHub repository settings
3. Create DigitalOcean account and apps
4. Push to `dev` branch to trigger deployment

## Testing Your Current Setup

```bash
# Run the test script
python3 test_setup.py

# Run the app with hot reload
python3 app.py

# Run with specific environment
export FLASK_ENV=development
python3 app.py
```

## Common Commands

```bash
# Start development with Docker
docker-compose up

# Rebuild after dependency changes
docker-compose build

# Run tests
docker-compose run web pytest

# Create a database migration
python3 scripts/setup_deployment.py development --create-migration

# Check logs
docker-compose logs -f web
```

## Troubleshooting

**Port 8000 already in use?**
```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
docker-compose run -p 8001:8000 web
```

**Database connection issues?**
- Check your Supabase project is active
- Verify your .env file has correct credentials
- Try the test script: `python3 test_setup.py`

**Docker issues?**
```bash
# Clean up Docker
docker system prune -a
docker-compose down -v
docker-compose up --build
```