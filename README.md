# Kinobody Greek God Program Fitness Tracker

A mobile-first web application designed specifically for tracking progress on the Kinobody Greek God muscle-building program.

## Features

- **Workout Tracking**: Log your Reverse Pyramid Training (RPT) workouts with automatic weight calculations
- **Nutrition Monitoring**: Track daily calories and macros with calorie cycling support
- **Progress Visualization**: Charts and graphs to monitor strength gains and body measurements
- **Mobile Optimized**: Designed for seamless use on mobile devices (425px+ width)
- **Offline Support**: Full functionality without internet connection
- **PWA Ready**: Can be installed as a mobile app

## Target User

- 23-year-old male, 6'5", 85kg → 90kg goal
- Following Kinobody Greek God Program
- 3x weekly training with 16:8 intermittent fasting

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/bulk_app.git
cd bulk_app

# Run with Python's built-in server
python3 -m http.server 8000

# Or use Node's http-server
npx http-server -p 8000
```

Then open http://localhost:8000/MD-Pilot-mobile-tracker%20(example)/

### Docker Deployment

```bash
# Build the Docker image
docker build -t kinobody-tracker .

# Run the container
docker run -d -p 80:80 kinobody-tracker
```

## Tech Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Data Visualization**: Chart.js
- **Storage**: Local Storage API
- **Backend Integration**: Supabase (PostgreSQL, OAuth)
- **Deployment**: Docker + DigitalOcean

## Project Structure

```
bulk_app/
├── MD-Pilot-mobile-tracker (example)/   # Main app files
│   ├── index.html                       # App structure
│   ├── app.js                          # Application logic
│   └── style.css                       # Mobile-first styling
├── MD-Pilot-mobile-app-docs.md         # Technical documentation
├── full dev & setup guide.md           # Deployment guide
└── test_supabase_table.sql            # Database schema
```

## Documentation

- [Technical Documentation](MD-Pilot-mobile-app-docs.md)
- [Full Deployment Guide](full%20dev%20&%20setup%20guide.md)

## License

This project is private and intended for personal use.