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

# Run container
docker run -d -p 8080:80 --name kinobody-app kinobody-tracker

# Stop and remove container
docker stop kinobody-app && docker rm kinobody-app
```

### Database Setup
```bash
# Run Supabase table creation
psql -h <supabase-host> -U postgres -d postgres -f test_supabase_table.sql
```

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

## Development Notes

- The app is designed as a mobile-first PWA optimized for 425px+ width
- Frontend uses vanilla JavaScript with ES6+ class-based architecture
- No npm/yarn dependencies - uses CDN for Chart.js
- Python backend should handle Supabase authentication and data sync
- Local Storage provides offline functionality when backend is unavailable