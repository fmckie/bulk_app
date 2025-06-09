# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Kinobody Greek God Program Fitness Tracker - a mobile-first web application for tracking fitness progress using the Kinobody methodology. 

**Note**: The folders marked with "(example)" are demo/reference implementations, not the actual app. The actual app will be built with:
- **Frontend**: Flask framework serving HTML, CSS, and JavaScript
- **Backend**: Python with Flask for API endpoints and business logic

## Commands

### Local Development
```bash
# Start Flask application
python3 app.py

# Or run with Flask development server
flask run --debug --port 8000

# Set Flask environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
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

### DigitalOcean Deployment (Using MCP Tools)

**IMPORTANT**: Use DigitalOcean MCP tools for deployment instead of manual commands.

```python
# Using DigitalOcean MCP for App Platform deployment
# 1. Create app with Docker container
mcp__digitalocean__create_app({
    "spec": {
        "name": "kinobody-tracker",
        "region": "nyc",
        "services": [{
            "name": "web",
            "image": {
                "registry_type": "DOCKER_HUB",
                "repository": "your-dockerhub-username/kinobody-tracker",
                "tag": "latest"
            }
        }]
    }
})

# 2. Or deploy from DigitalOcean Container Registry
mcp__digitalocean__create_app({
    "spec": {
        "name": "kinobody-tracker",
        "region": "nyc",
        "services": [{
            "name": "web",
            "image": {
                "registry_type": "DOCR",
                "repository": "kinobody-tracker",
                "tag": "latest"
            }
        }]
    }
})

# 3. Monitor deployment status
mcp__digitalocean__get_app({"id": "app-id"})
mcp__digitalocean__get_deployment_logs_url({"app_id": "app-id", "type": "DEPLOY"})
```

### Manual Deployment (Fallback)
```bash
# Using DigitalOcean App Platform CLI
doctl apps create --spec app.yaml

# Or deploy with Docker on Droplet
ssh root@<your-droplet-ip>
docker pull registry.digitalocean.com/<your-registry>/kinobody-tracker:latest
docker run -d -p 80:80 --restart always --name kinobody-app registry.digitalocean.com/<your-registry>/kinobody-tracker:latest
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

# After testing in dev, move to production:
# Option 1: Using GitHub PR (Recommended)
gh pr create --title "Feature: Your feature name" --body "Description of changes" --base main --head dev

# Option 2: Using GitHub MCP tools
mcp__github__create_pull_request({
    "owner": "your-username",
    "repo": "bulk_app",
    "title": "Feature: Your feature name",
    "head": "dev",
    "base": "main",
    "body": "Description of changes and testing completed"
})

# After PR approval, merge using GitHub MCP
mcp__github__merge_pull_request({
    "owner": "your-username",
    "repo": "bulk_app",
    "pull_number": PR_NUMBER,
    "merge_method": "merge"
})
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

### Application Structure
- **Flask Application**: Single Python app serving both frontend templates and backend API
- **Frontend**: Flask templates (Jinja2) with HTML, CSS, and JavaScript
- **Backend API**: Flask routes handling data processing and Supabase integration
- **Database**: Supabase PostgreSQL with authentication
- **API Design**: RESTful endpoints for workouts, nutrition, measurements, and progress tracking

## Supabase Database & Authentication

### Primary Database
Supabase serves as the main database for all user data:
- **User Authentication**: Built-in OAuth providers (Google, GitHub, email/password)
- **Personal Data Storage**: All workout history, nutrition logs, and progress tracking
- **Row Level Security (RLS)**: Ensures users can only access their own data
- **Real-time Subscriptions**: Live updates for collaborative features

### Authentication Setup
```python
from supabase import create_client, Client

# Initialize Supabase client
supabase: Client = create_client(
    "https://YOUR-PROJECT.supabase.co",
    "YOUR-ANON-KEY"
)

# User sign up with email
def sign_up_user(email, password):
    response = supabase.auth.sign_up({
        "email": email,
        "password": password
    })
    return response.user

# User sign in
def sign_in_user(email, password):
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    return response.session

# OAuth sign in (Google, GitHub, etc.)
def oauth_sign_in(provider):
    response = supabase.auth.sign_in_with_oauth({
        "provider": provider  # "google", "github", etc.
    })
    return response.url
```

### Data Access Functions
```python
# Get authenticated user
def get_current_user(token):
    supabase.auth.set_session(token)
    return supabase.auth.get_user()

# Store workout data
def save_workout(user_id, workout_data):
    response = supabase.table('workouts').insert({
        'user_id': user_id,
        'date': workout_data['date'],
        'exercises': workout_data['exercises'],
        'notes': workout_data['notes']
    }).execute()
    return response.data

# Fetch user's nutrition history
def get_nutrition_history(user_id, start_date=None):
    query = supabase.table('nutrition').select('*').eq('user_id', user_id)
    if start_date:
        query = query.gte('date', start_date)
    response = query.order('date', desc=True).execute()
    return response.data

# Update user measurements
def update_measurements(user_id, measurements):
    response = supabase.table('measurements').upsert({
        'user_id': user_id,
        'date': measurements['date'],
        'weight': measurements['weight'],
        'body_fat': measurements.get('body_fat'),
        'measurements': measurements.get('body_measurements')
    }).execute()
    return response.data
```

### Row Level Security (RLS) Policies
```sql
-- Users can only view their own data
CREATE POLICY "Users can view own workouts" ON workouts
    FOR SELECT USING (auth.uid() = user_id);

-- Users can only insert their own data
CREATE POLICY "Users can insert own workouts" ON workouts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only update their own data
CREATE POLICY "Users can update own workouts" ON workouts
    FOR UPDATE USING (auth.uid() = user_id);

-- Apply similar policies to all tables
```

### Frontend Structure
- **templates/**: Flask HTML templates using Jinja2
  - `base.html`: Base template with common layout
  - `index.html`: Main application page
  - Other feature-specific templates
- **static/**: Static assets served by Flask
  - `css/`: Stylesheets including mobile-first responsive design
  - `js/`: JavaScript files for frontend logic
  - `img/`: Images and icons
- **Example References**:
  - `MD-Pilot-mobile-tracker (example)/`: Demo implementation for reference
  - `example web app/`: Another reference implementation

### Key Features
- Reverse Pyramid Training (RPT) workout tracking
- Calorie cycling nutrition monitoring
- Progress visualization with Chart.js
- Offline-first with Local Storage fallback
- PWA capabilities for mobile installation

## Database Schema

Supabase PostgreSQL database serves as the primary data store with the following tables:

### Core Tables
- **`users`**: User profiles linked to Supabase Auth
  - Stores profile data, preferences, and program settings
  - Automatically created on OAuth/email signup
  
- **`workouts`**: Exercise session logs
  - Complete workout history with RPT sets/reps/weights
  - Linked to user_id for data isolation
  
- **`nutrition`**: Daily nutrition tracking
  - Calories, protein, carbs, fats per day
  - Supports calorie cycling patterns
  
- **`measurements`**: Body composition tracking
  - Weight, body fat %, measurements
  - Progress photos with secure storage
  
- **`exercises`**: Exercise library
  - Pre-populated with Kinobody exercises
  - Personal records and strength standards

### Data Privacy
- All user data is isolated using Row Level Security (RLS)
- Users can only access their own data
- OAuth tokens expire and refresh automatically
- No data sharing between users

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
- Flask serves both frontend templates and backend API endpoints
- Frontend JavaScript communicates with Flask backend via AJAX/fetch
- No npm/yarn dependencies - uses CDN for libraries like Chart.js
- Flask sessions handle user state with Supabase for persistent storage
- Local Storage provides offline functionality when backend is unavailable
- Example folders are for reference only - build the actual app in the main directory

## Puppeteer Visual Testing

### Setup Puppeteer MCP for Testing
```javascript
// Visual testing for new features
async function testFeatureVisually(feature) {
    // Navigate to local development
    await mcp__puppeteer__puppeteer_navigate({
        url: "http://localhost:8000/app/"
    });
    
    // Take before screenshot
    await mcp__puppeteer__puppeteer_screenshot({
        name: `${feature}_before`,
        width: 425,  // Mobile width
        height: 800
    });
    
    // Test feature interactions
    // Example: Test workout logging
    await mcp__puppeteer__puppeteer_click({
        selector: "#log-workout-btn"
    });
    
    await mcp__puppeteer__puppeteer_fill({
        selector: "#exercise-weight",
        value: "185"
    });
    
    // Take after screenshot
    await mcp__puppeteer__puppeteer_screenshot({
        name: `${feature}_after`,
        width: 425,
        height: 800
    });
}
```

### Visual Test Checklist
1. **Mobile Responsiveness**: Test at 425px width
2. **Form Interactions**: Test all input fields
3. **Navigation Flow**: Test menu and page transitions
4. **Data Display**: Verify charts and progress displays
5. **PWA Features**: Test offline mode and app installation

## Kinobody Program Knowledge Base

### Source Document
The `sources/kinobody.md` file contains the complete Greek God Program methodology and should be used as the authoritative source for:

### Key Program Principles
- **Reverse Pyramid Training (RPT)**: Primary training methodology
- **Indicator Exercises**: Core lifts for strength progression
- **Assistance Movements**: Supporting exercises for muscle development
- **Strength Standards**: Target weights relative to body weight
- **Training Frequency**: 3 days per week optimal schedule

### Nutrition Guidelines from Kinobody
- **Intermittent Fasting**: 16:8 protocol recommended
- **Calorie Cycling**: Higher calories on training days
- **Protein Targets**: Based on lean body mass
- **Strategic Carb/Fat Distribution**: Optimized for muscle growth

### Implementation Notes
When building features, always reference `sources/kinobody.md` for:
- Exercise selection and programming
- Set/rep schemes for RPT
- Progression protocols
- Nutrition calculations
- Recovery recommendations

### Example Usage
```python
# Load Kinobody principles
def load_kinobody_config():
    with open('sources/kinobody.md', 'r') as f:
        kinobody_text = f.read()
    
    # Extract key metrics
    # - Indicator exercises
    # - RPT protocols
    # - Strength standards
    # - Nutrition guidelines
    
    return kinobody_config
```

## Deployment Checklist

**IMPORTANT**: All deployments use Docker containers and DigitalOcean MCP tools.

1. **Local Testing**
   - Build Docker image: `docker build -t kinobody-tracker .`
   - Run container locally: `docker run -d -p 8080:80 kinobody-tracker`
   - Test all features at http://localhost:8080
   - Check mobile responsiveness at 425px width

2. **Push to Dev Branch**
   - Create feature branch from dev
   - Test thoroughly
   - Commit with descriptive message
   - Push Docker image to registry

3. **Deploy to DigitalOcean (Using MCP)**
   ```python
   # List existing apps
   mcp__digitalocean__list_apps({"query": {}})
   
   # Create new deployment
   mcp__digitalocean__create_deployment({
       "app_id": "your-app-id",
       "force_build": true
   })
   
   # Monitor deployment
   mcp__digitalocean__get_deployment({
       "app_id": "your-app-id",
       "deployment_id": "deployment-id"
   })
   ```

4. **Production Deployment**
   - Create PR from dev to main using GitHub MCP:
     ```python
     mcp__github__create_pull_request({
         "owner": "your-username",
         "repo": "bulk_app",
         "title": "Release: v1.0.0",
         "head": "dev",
         "base": "main",
         "body": "Production release with tested features"
     })
     ```
   - Review and merge PR using GitHub MCP:
     ```python
     mcp__github__merge_pull_request({
         "owner": "your-username",
         "repo": "bulk_app",
         "pull_number": PR_NUMBER
     })
     ```
   - Deploy production app using DigitalOcean MCP
   - Monitor logs and performance
   - Rollback if needed using `mcp__digitalocean__rollback_app`