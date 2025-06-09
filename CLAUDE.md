# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Kinobody Greek God Program Fitness Tracker** - a mobile-first web application designed for tracking muscle-building progress. The app is specifically tailored for a 23-year-old male user following the Greek God muscle-building program with a goal of gaining lean muscle from 85kg to 90kg.

## Architecture

### Technology Stack
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Data Visualization**: Chart.js for progress tracking
- **Data Persistence**: Local Storage API
- **Backend Integration**: Supabase (PostgreSQL, OAuth authentication)
- **Deployment**: Docker + DigitalOcean

### Key Components

1. **Mobile Web App** (`MD-Pilot-mobile-tracker (example)/` and `example web app/`)
   - Single-page application with 4 main screens: Dashboard, Workouts, Nutrition, Progress
   - Mobile-first design (minimum 425px width)
   - Offline functionality with local storage

2. **Workout System**
   - Two workout programs (A & B) with Reverse Pyramid Training (RPT)
   - Automatic weight calculations for RPT sets (10% reduction)
   - Built-in rest timers (180s for main lifts, 120s for assistance)

3. **Nutrition Tracking**
   - Calorie cycling: 3,300 cal on training days, 3,100 cal on rest days
   - Macro tracking with daily targets (200g protein, 80g fats, 360-400g carbs)
   - Intermittent fasting timer (16:8 protocol)

## Development Commands

Since this is a vanilla HTML/CSS/JS project without a build system:

```bash
# Run locally (no build required)
# Option 1: Use Python's built-in server
python3 -m http.server 8000

# Option 2: Use Node's http-server (if installed)
npx http-server -p 8000

# Option 3: Open index.html directly in browser (limited functionality)
open MD-Pilot-mobile-tracker\ \(example\)/index.html
```

## Docker Commands

```bash
# Build Docker image
docker build -t kinobody-tracker .

# Run container
docker run -d -p 80:80 kinobody-tracker

# Deploy to production (see full dev & setup guide.md)
```

## Database Setup

When setting up Supabase, use the SQL schema in `test_supabase_table.sql` or the schema provided in `full dev & setup guide.md` lines 55-94.

## Important Notes

- The app uses Supabase environment variables that need to be configured in `app.js`:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
- OAuth providers (Google/Apple) need to be configured in Supabase dashboard
- For PWA functionality, ensure `manifest.json` and service worker (`sw.js`) are properly configured
- All touch targets should be at least 44px for mobile usability
- The app is designed to work offline with local storage fallback