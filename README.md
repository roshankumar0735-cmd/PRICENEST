PriceNest - AI Real Estate Price Predictor

AI-powered property valuation tool for Delhi & Delhi NCR, built with Flask, Scikit-learn, and a dataset-driven prediction engine.

Overview

PriceNest predicts real estate prices by analyzing property details (city, location, type, bedrooms, floor, facing, carpet area, amenities) against a real estate dataset. It combines dataset lookups with ML regression to generate realistic price estimates, and keeps the UI in sync with dynamic unit conversions and smart dropdown filtering.

Features
AI-based property price prediction using regression
Dataset-driven cascading dropdowns (only valid combinations shown)
Unit conversion support for sqft, sqm, and sqyrd
Amenities-based price adjustment (Gym, Lift, Security, Power Backup)
Google Sign-In authentication (Firebase)
Google Maps integration with nearby facilities section
Optional MongoDB Atlas persistence for users and prediction history
Tech Stack
Layer	Technology
Frontend	HTML, CSS, JavaScript, React-style components
Backend	Python, Flask
ML	Scikit-learn, Pandas, NumPy
Auth	Firebase Authentication
Maps	Google Maps API
Database	MongoDB Atlas (optional)
Installation
bash
git clone <your-repository-url>
cd PriceNest
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
python app.py

Visit http://127.0.0.1:5000

Environment Variables

Set these in a .env file:

GOOGLE_CLIENT_ID=
GOOGLE_MAPS_API_KEY=
MONGODB_URI=
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
API Endpoints (Sample)
Method	Endpoint	Description
GET	/options	Dataset-driven dropdown options
POST	/predict	Generates price prediction
GET	/maps/config	Map configuration
POST	/auth/google-login	Google login + user storage
Future Improvements
Full React/Vite frontend
Live Google Places nearby results
User dashboard for saved predictions
Pan-India dataset expansion
Author

Roshan Kumar — GitHub · LinkedIn
