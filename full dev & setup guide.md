MD Pilot Fitness Tracker: Full Deployment & Setup Guide

This guide will walk you through building, deploying, and securing your own private, mobile-optimized fitness tracker app using Docker, DigitalOcean, Supabase (with OAuth), and a simple, responsive HTML/CSS/JS frontend. All features are tailored for seamless use on your mobile device (minimum width: 425px).

---

## Table of Contents

1. [Project Features](#project-features)
2. [Supabase Setup (Database & OAuth)](#supabase-setup-database--oauth)
3. [Frontend: Responsive HTML/CSS/JS](#frontend-responsive-htmlcssjs)
4. [Dockerizing the App](#dockerizing-the-app)
5. [Deploying to DigitalOcean](#deploying-to-digitalocean)
6. [Securing Your Deployment](#securing-your-deployment)
7. [Mobile Experience & PWA](#mobile-experience--pwa)
8. [Maintenance & Best Practices](#maintenance--best-practices)

---

## Project Features

- **Personalized Workout Logging**: Track sets, reps, and weights for each session (RPT progression supported).
- **Nutrition Tracking**: Log daily calories, protein, carbs, and fats.
- **Progress Photos & Measurements**: Upload and view progress photos, track weight and body stats.
- **Supabase OAuth Authentication**: Secure login via Google/Apple (or other providers).
- **Mobile-First Responsive Design**: Optimized for 425px width and up.
- **Offline Support**: PWA with Service Worker for offline access and caching.
- **Private & Secure**: Only accessible to you, with all data stored in your private Supabase project.
- **Analytics**: Simple charts for strength and weight progress.
- **Easy Export**: Download your logs and data as CSV for backup or analysis.

---

## Supabase Setup (Database & OAuth)

### 1. Create Your Supabase Project

- Go to [Supabase](https://supabase.com) and create a new project.
- Note your `SUPABASE_URL` and `SUPABASE_ANON_KEY`.

### 2. Enable OAuth Authentication

- In the Supabase dashboard, go to **Authentication > Providers**.
- Enable Google (and/or Apple, GitHub, etc.).
- For Google:
  - Go to Google Cloud Console, create OAuth credentials.
  - Add your app’s domain or DigitalOcean droplet IP to **Authorized JavaScript Origins** and **Redirect URIs** (e.g., `https://your-domain.com` or `http://your-droplet-ip`).
  - Paste the Client ID and Secret into Supabase.
  - [See Supabase Docs for Google OAuth](https://supabase.com/docs/guides/auth/social-login/auth-google)[8][9][10][15].

### 3. Database Tables

In Supabase SQL Editor, run:

-- Workouts
create table workouts (
id serial primary key,
user_id uuid references auth.users,
date date not null,
exercise text not null,
sets jsonb not null
);

-- Nutrition
create table nutrition (
id serial primary key,
user_id uuid references auth.users,
date date not null,
calories integer,
protein integer,
carbs integer,
fats integer
);

-- Progress Photos
create table progress_photos (
id serial primary key,
user_id uuid references auth.users,
date date not null,
photo_url text not null
);

-- Measurements
create table measurements (
id serial primary key,
user_id uuid references auth.users,
date date not null,
weight numeric,
chest numeric,
waist numeric,
arms numeric
);

text

- Enable **Row Level Security** and add policies to allow users to access only their own data.

---

## Frontend: Responsive HTML/CSS/JS

### 1. Project Structure

/app
/public
index.html
style.css
app.js
sw.js
/assets
(icons, images)

text

### 2. Responsive HTML (index.html)

<!DOCTYPE html> <html lang="en"> <head> <meta name="viewport" content="width=device-width, initial-scale=1.0"> <title>Kinobody Fitness Tracker</title> <link rel="manifest" href="manifest.json"> <link rel="stylesheet" href="style.css"> </head> <body> <div id="auth"> <button id="login-google">Sign in with Google</button> </div> <main id="app" style="display:none;"> <header> <h1>Kinobody Tracker</h1> <button id="logout">Logout</button> </header> <section id="workout-log"></section> <section id="nutrition-log"></section> <section id="progress"></section> </main> <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js"></script> <script src="app.js"></script> </body> </html> ```
3. Mobile-First CSS (style.css)
text
html, body {
  margin: 0;
  padding: 0;
  font-family: system-ui, sans-serif;
  background: #f8f8f8;
}

#auth, #app {
  max-width: 425px;
  margin: auto;
  padding: 1rem;
}

button {
  width: 100%;
  min-height: 48px;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  border-radius: 6px;
  border: none;
  background: #2d6cdf;
  color: #fff;
  cursor: pointer;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

section {
  margin-bottom: 2rem;
}

@media (min-width: 426px) {
  #auth, #app {
    max-width: 600px;
  }
}
All touch targets are at least 48px tall for mobile usability.

4. JS: Supabase Auth & Core Features (app.js)
text
const SUPABASE_URL = 'https://YOUR_PROJECT.supabase.co';
const SUPABASE_KEY = 'YOUR_SUPABASE_ANON_KEY';
const supabase = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// Auth
document.getElementById('login-google').onclick = async () => {
  await supabase.auth.signInWithOAuth({ provider: 'google' });
};

supabase.auth.onAuthStateChange(async (event, session) => {
  if (session) {
    document.getElementById('auth').style.display = 'none';
    document.getElementById('app').style.display = '';
    loadApp();
  } else {
    document.getElementById('auth').style.display = '';
    document.getElementById('app').style.display = 'none';
  }
});

document.getElementById('logout').onclick = async () => {
  await supabase.auth.signOut();
};

// Load and render workout, nutrition, progress logs...
async function loadApp() {
  // Fetch and render data from Supabase
}
Dockerizing the App
1. Dockerfile
text
FROM nginx:alpine
COPY public /usr/share/nginx/html
EXPOSE 80
Keep the image minimal for security and speed.

2. Nginx Config (optional)
If you want custom routes or HTTPS, mount a config file and SSL certs.

Deploying to DigitalOcean
1. Create a DigitalOcean Droplet
Use the Docker 1-Click App for easiest setup.

Or, SSH into your droplet and install Docker:

text
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
2. Deploy Your App
SCP or Git clone your project to the droplet.

Build and run:

text
docker build -t kinobody-tracker .
docker run -d -p 80:80 kinobody-tracker
For SSL/HTTPS, see this guide.

Securing Your Deployment
Supabase OAuth: All app access is gated by Supabase Auth (Google, Apple, etc.).

HTTPS: Strongly recommended for all production deployments (Let’s Encrypt or DigitalOcean SSL).

Firewall: Use DigitalOcean’s firewall to restrict access to your IP if desired.

Stateless Containers: All persistent data is in Supabase, not the Docker container.

Mobile Experience & PWA
Responsive Design: All UI elements adapt for 425px width and up.

Add to Home Screen: Add a manifest.json for PWA installability.

Service Worker: Register a service worker for offline access and caching.

public/manifest.json

text
{
  "name": "Kinobody Tracker",
  "short_name": "Kinobody",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#f8f8f8",
  "theme_color": "#2d6cdf",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
public/sw.js

text
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('kinobody-cache').then(cache =>
      cache.addAll([
        '/',
        '/index.html',
        '/style.css',
        '/app.js'
      ])
    )
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response =>
      response || fetch(event.request)
    )
  );
});
Register the service worker in app.js:

text
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}
Maintenance & Best Practices
Update Images: Rebuild and redeploy Docker images for updates.

Stateless Containers: Never store data in the container; all user data is in Supabase.

Version Control: Tag Docker images for easy rollback.

Security: Regularly update dependencies, use HTTPS, and enable RLS in Supabase.

Backups: Use Supabase’s backup features for your database.

Summary
By following this guide, you will have a secure, private, mobile-optimized fitness tracker app with all your data safely managed in Supabase, OAuth-protected for exclusive access, and easily accessible from your phone or any device. All deployment is containerized for reliability and portability, and the app is designed for a seamless mobile experience with offline support.

For further customization, expand the frontend UI, add analytics, or integrate notifications as needed.



------------------------------



## Additional features to check out in the future:

- barcode reader
- weight loss section
- api integration with your local supserstores