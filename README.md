# Chaser Map (static)

This repo has a single-page map game (`index.html`). Open it over HTTPS, allow location, pick a character, and a chaser will track you on the map.

## Run locally for quick checks
- `python -m http.server 8000` then open http://localhost:8000 (geolocation works on localhost even without HTTPS).

## Deploy to the web (no build step)

### Option 1: GitHub Pages
1) Put `index.html` in a Git repo and push to GitHub.  
2) In the repo settings, enable GitHub Pages for the main branch, root.  
3) Visit the Pages URL (it will be served over HTTPS so geolocation works on mobile data).

### Option 2: Netlify (drag-and-drop)
1) Go to https://app.netlify.com/drop and drag `index.html` into the window.  
2) Netlify will give you an HTTPS URL in ~1 minute.

### Option 3: Vercel (CLI)
1) Install Vercel CLI (`npm i -g vercel`), run `vercel` in this folder, accept defaults.  
2) It deploys as static hosting with an HTTPS URL.

Once deployed, open the HTTPS URL on your phone (mobile data or Wi‑Fi), allow location, and play. Geolocation will not work on plain HTTP except for `localhost`.
