# PriceNest Frontend

This folder is the modular React source workspace for the PriceNest UI.

The Flask app currently serves the production-compatible runtime bundle from `static/` so the project runs without a Node build step. Keep `frontend/` as the scalable source layout and mirror production-ready changes into `static/` until a bundler such as Vite is introduced.

## Structure

- `App.jsx` - current React application source mirror.
- `components/` - feature component ownership folders.
- `styles/` - frontend stylesheets.
- `utils/` - reusable browser utilities for API calls, formatting, auth, and unit conversion.
- `pages/` - page-level composition entry points.
- `assets/` - images, icons, and static frontend assets.
