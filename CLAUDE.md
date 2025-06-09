# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Kinobody Greek God Program Fitness Tracker - a mobile-first web application for tracking fitness progress using the Kinobody methodology. The app uses a Python backend with a vanilla JavaScript frontend.

## Commands

### Local Development
```bash
# Start Python backend server
python3 app.py

# Or run with Flask (if using Flask)
python3 -m flask run --port 8000

# For frontend development with hot reload
python3 -m http.server 8000
```

### Docker Commands
```bash
# Build Docker image
docker build -t kinobody-tracker .

# Run container locally for testing
docker run -d -p 8080:80 --name kinobody-app kinobody-tracker

# Test the container
curl http://localhost:8080

# View container logs
docker logs kinobody-app

# Stop and remove container
docker stop kinobody-app && docker rm kinobody-app

# Tag image for DigitalOcean registry
docker tag kinobody-tracker registry.digitalocean.com/<your-registry>/kinobody-tracker:latest

# Push to DigitalOcean registry
docker push registry.digitalocean.com/<your-registry>/kinobody-tracker:latest
```

### Database Setup
```bash
# Run Supabase table creation
psql -h <supabase-host> -U postgres -d postgres -f test_supabase_table.sql
```

### DigitalOcean Deployment
```bash
# Using DigitalOcean App Platform
doctl apps create --spec app.yaml

# Or deploy with Docker on Droplet
ssh root@<your-droplet-ip>
docker pull registry.digitalocean.com/<your-registry>/kinobody-tracker:latest
docker run -d -p 80:80 --restart always --name kinobody-app registry.digitalocean.com/<your-registry>/kinobody-tracker:latest

# Monitor deployment
docker ps
docker logs -f kinobody-app
```

## Git Workflow

### IMPORTANT: Always use development branch for new features
```bash
# Create and switch to dev branch
git checkout -b dev

# Make your changes and test thoroughly
# ... edit files ...

# Stage and commit changes
git add -A
git commit -m "feat: describe your feature here"

# Push to dev branch
git push origin dev

# After testing, create PR to merge dev -> main
gh pr create --title "Feature: Your feature name" --body "Description of changes" --base main --head dev

# Or merge locally after thorough testing
git checkout main
git merge dev
git push origin main
```

### Commit Guidelines
- Always commit to `dev` branch first
- Test thoroughly before merging to `main` (production)
- Use descriptive commit messages:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation
  - `refactor:` for code improvements
  - `test:` for test additions/changes

## Architecture

### Backend Structure
- **Python Backend**: Handles API endpoints, data processing, and Supabase integration
- **Supabase Integration**: PostgreSQL database with authentication
- **API Design**: RESTful endpoints for workouts, nutrition, measurements, and progress tracking

### Frontend Structure
- **app/**: Production-ready static files
- **MD-Pilot-mobile-tracker (example)/**: Development version with example implementation
- **Core Files**:
  - `app.js`: Main application logic with KinobodyApp class
  - `index.html`: Single page application structure
  - `style.css`: Mobile-first responsive design

### Key Features
- Reverse Pyramid Training (RPT) workout tracking
- Calorie cycling nutrition monitoring
- Progress visualization with Chart.js
- Offline-first with Local Storage fallback
- PWA capabilities for mobile installation

## Database Schema

The application uses Supabase with tables for:
- `users`: User profiles and authentication
- `workouts`: Exercise logs with RPT methodology
- `nutrition`: Daily calorie and macro tracking
- `measurements`: Body measurements and progress photos
- `exercises`: Exercise library with standards

## Upstash Redis Caching

### Setup
```python
# Initialize Upstash Redis client
import redis
from upstash_redis import Redis

# Connect using REST API
redis_client = Redis(
    url="https://YOUR-ENDPOINT.upstash.io",
    token="YOUR-UPSTASH-TOKEN"
)
```

### Common Caching Functions
```python
# Cache user data
def cache_user_data(user_id, data, ttl=3600):
    """Cache user data with 1 hour TTL"""
    key = f"user:{user_id}"
    redis_client.setex(key, ttl, json.dumps(data))

# Cache workout sessions
def cache_workout(user_id, workout_id, data, ttl=86400):
    """Cache workout data with 24 hour TTL"""
    key = f"workout:{user_id}:{workout_id}"
    redis_client.setex(key, ttl, json.dumps(data))

# Cache nutrition data
def cache_nutrition(user_id, date, data, ttl=86400):
    """Cache daily nutrition with 24 hour TTL"""
    key = f"nutrition:{user_id}:{date}"
    redis_client.setex(key, ttl, json.dumps(data))

# Cache progress calculations
def cache_progress_stats(user_id, stats, ttl=3600):
    """Cache calculated progress stats with 1 hour TTL"""
    key = f"progress:{user_id}"
    redis_client.setex(key, ttl, json.dumps(stats))

# Get cached data with fallback
def get_cached_or_fetch(key, fetch_function):
    """Get from cache or fetch from database"""
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    data = fetch_function()
    redis_client.setex(key, 3600, json.dumps(data))
    return data

# Invalidate cache patterns
def invalidate_user_cache(user_id):
    """Invalidate all user-related cache"""
    patterns = [
        f"user:{user_id}",
        f"workout:{user_id}:*",
        f"nutrition:{user_id}:*",
        f"progress:{user_id}"
    ]
    for pattern in patterns:
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
```

### Cache Strategy
- **User profiles**: 1 hour TTL
- **Workout data**: 24 hour TTL
- **Nutrition logs**: 24 hour TTL  
- **Progress stats**: 1 hour TTL (frequently recalculated)
- **Exercise library**: 7 day TTL (rarely changes)

### Redis Commands for Development
```bash
# Test Redis connection
redis-cli -u redis://default:YOUR_PASSWORD@YOUR_ENDPOINT:PORT ping

# Monitor cache hits/misses
redis-cli -u redis://default:YOUR_PASSWORD@YOUR_ENDPOINT:PORT monitor

# Clear all cache (development only)
redis-cli -u redis://default:YOUR_PASSWORD@YOUR_ENDPOINT:PORT flushall
```

## Development Notes

- The app is designed as a mobile-first PWA optimized for 425px+ width
- Frontend uses vanilla JavaScript with ES6+ class-based architecture
- No npm/yarn dependencies - uses CDN for Chart.js
- Python backend should handle Supabase authentication and data sync
- Local Storage provides offline functionality when backend is unavailable

## Deployment Checklist

1. **Local Testing**
   - Run Docker container locally
   - Test all features
   - Check mobile responsiveness

2. **Push to Dev Branch**
   - Create feature branch from dev
   - Test thoroughly
   - Commit with descriptive message

3. **Deploy to Staging (DigitalOcean)**
   - Build and push Docker image
   - Deploy to staging environment
   - Run integration tests

4. **Merge to Production**
   - Create PR from dev to main
   - Review changes
   - Merge after approval
   - Deploy to production DigitalOcean app