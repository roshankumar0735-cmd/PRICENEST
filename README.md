# PriceNest - AI Real Estate Price Predictor

**AI-Powered Property Valuation across Delhi & Delhi NCR with Real Market Insights and Data-Driven Analysis**

PriceNest is an AI + Machine Learning + Full Stack Web Application designed to predict real estate property prices across Delhi and Delhi NCR. It uses dataset-driven property filtering, machine learning regression, dynamic unit conversion, location-aware amenities logic, Google authentication, and map-based property context to deliver a modern real estate valuation experience.

The project is suitable for college projects, portfolio showcases, viva presentations, and practical demonstrations of how machine learning can be integrated into a professional web application.

---

## Table of Contents

1. [Project Introduction](#project-introduction)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Frontend Technologies](#frontend-technologies)
5. [Backend Technologies](#backend-technologies)
6. [AI/ML Concepts Used](#aiml-concepts-used)
7. [Dataset Information](#dataset-information)
8. [Prediction Logic](#prediction-logic)
9. [Unit Conversion Logic](#unit-conversion-logic)
10. [Dynamic Filtering Logic](#dynamic-filtering-logic)
11. [Authentication System](#authentication-system)
12. [Google Maps Integration](#google-maps-integration)
13. [Nearby Facilities Feature](#nearby-facilities-feature)
14. [Project Workflow](#project-workflow)
15. [Folder Structure](#folder-structure)
16. [Installation Guide](#installation-guide)
17. [Environment Variables](#environment-variables)
18. [API Information](#api-information)
19. [Future Improvements](#future-improvements)
20. [Screenshots Section](#screenshots-section)
21. [Author Information](#author-information)

---

## Project Introduction

PriceNest helps users estimate property prices by analyzing real estate data from Delhi and Delhi NCR. The application allows users to select property details such as city, location, property type, bedrooms, floor, facing, balcony, parking, carpet area, unit, and amenities.

The system then matches the selected details with the available dataset, applies machine learning-based prediction logic, preserves original dataset values, and displays a clean prediction result with dynamic area and rate conversion.

### Project Purpose

The main purpose of PriceNest is to provide a realistic, intelligent, and beginner-friendly property valuation platform that demonstrates:

- Machine learning regression for property price prediction
- Dataset-driven dropdown filtering
- Real estate feature engineering
- Dynamic area unit conversion
- Google authentication
- Google Maps-based property context
- Full-stack Flask + React-style frontend integration

---

## Features

- AI-powered property price prediction
- Delhi and Delhi NCR property valuation support
- Dataset-driven city and location filtering
- Cascading smart dropdowns for valid property combinations
- Searchable location field
- Property type detection from dataset property names
- Amenities section with dataset-based and artificial amenity logic
- Dynamic prediction price card
- Original dataset value preservation
- Unit conversion support for `sqft`, `sqm`, and `sqyrd`
- Rate display based on selected unit
- Carpet area and total area synchronization
- Google Sign-In using Firebase Authentication
- Mobile OTP login UI with Firebase limitation handling
- Profile popup and logout support
- Google Map section
- Nearby facilities cards
- Database insights section
- Property demand section
- FAQ and About sections
- Print details / report generation support
- Responsive premium UI
- Single Flask server architecture on `http://127.0.0.1:5000`

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript, React.js-style component structure |
| Backend | Python, Flask |
| Machine Learning | Scikit-learn, Pandas, NumPy |
| Dataset | CSV dataset |
| Authentication | Firebase Authentication, Google Sign-In |
| Maps | Google Maps Embed API, Nearby Places Integration |
| Future Database Support | MongoDB Atlas |

---

## Frontend Technologies

PriceNest uses a modern frontend structure with reusable UI sections and clean styling.

### Frontend Includes

- HTML for page structure
- CSS for responsive premium UI design
- JavaScript for form state, API calls, dynamic filtering, and UI updates
- React.js-style modular frontend organization
- Firebase client integration for authentication
- Utility functions for formatting and unit conversion

### Key Frontend Responsibilities

- Display the PriceNest landing page
- Manage Smart Property Analyzer form state
- Fetch dynamic dropdown values from backend APIs
- Display prediction results
- Convert carpet area, total area, and rate values dynamically
- Handle Google Sign-In and profile UI
- Render Google Map and nearby facility cards
- Maintain responsive layout across desktop, laptop, tablet, and mobile

---

## Backend Technologies

The backend is built using Python Flask and serves both the frontend and API routes from one server.

### Backend Includes

- Flask application server
- REST API endpoints
- Dataset loading and processing
- ML prediction service
- Dynamic filtering logic
- Unit normalization and conversion helpers
- Authentication configuration APIs
- Google Maps configuration APIs

### Backend Responsibilities

- Serve the main website from `/`
- Load and process the CSV dataset
- Train and run the machine learning model
- Return dataset-driven dropdown options
- Match selected values with dataset rows
- Generate predictions
- Apply amenities-based price adjustments
- Provide insights and property demand data

---

## AI/ML Concepts Used

PriceNest uses supervised machine learning for real estate price prediction.

### Concepts Applied

- **Supervised Learning**  
  The model learns from historical property records where property features and prices are already known.

- **Regression Model**  
  Since the target output is a continuous numeric value, property price prediction is handled as a regression problem.

- **Feature Engineering**  
  Important property attributes such as city, location, property type, bedrooms, floor, facing, parking, balcony, carpet area, and amenities are processed as model features.

- **Preprocessing**  
  The dataset is cleaned and transformed before being used by the model.

- **Categorical Encoding**  
  Text-based fields such as city, location, facing, and parking are converted into machine-readable numerical representations.

- **Numerical Feature Handling**  
  Numeric fields such as bedrooms, balcony, carpet area, rate, and price are validated and formatted before prediction.

- **Property Valuation Prediction**  
  The model estimates property value using both dataset records and learned pricing patterns.

---

## Dataset Information

The project uses a CSV dataset containing real estate records from Delhi and Delhi NCR.

### Dataset Contains

- Property name
- City
- Location
- Property type information
- Bedrooms
- Floor
- Facing
- Balcony
- Parking
- Carpet area
- Total area
- Price
- Rate
- Garden/Park
- Main Road
- Pool

### Dataset Role

The dataset is the primary source of truth for:

- Dropdown values
- Valid property combinations
- Base predicted price
- Rate values
- Carpet area values
- Total area values
- Dataset-based amenities

Important: the project does not add fake columns to the dataset. Missing amenities such as Gym, Lift, Security, and Power Backup are handled only as backend post-processing adjustments.

---

## Prediction Logic

PriceNest uses a dataset-first prediction approach.

### Prediction Flow

1. User selects property details.
2. Backend filters matching dataset records.
3. If an exact dataset row exists, the system preserves and displays original dataset values.
4. If needed, the ML model predicts the property price using processed inputs.
5. Amenities-based adjustments are applied as a post-processing layer.
6. Final values are formatted and returned to the frontend.

### Base Price Rule

If a matching dataset row exists:

- Predicted Price comes from the dataset `Price` column.
- Rate comes from the dataset `Rate` column.
- Carpet Area and Total Area come from the dataset.

### Amenities Price Boost Logic

Artificial amenities such as:

- Gym
- Lift
- Security
- Power Backup

can slightly increase the predicted price. These increments are applied only after the base dataset price or ML prediction is calculated.

The increment is locality-aware and city-aware. Premium areas receive higher adjustments, while normal localities receive smaller realistic adjustments.

---

## Unit Conversion Logic

PriceNest supports three area units:

- `sqft`
- `sqm`
- `sqyrd`

### Conversion Formulas

```text
1 sqm   = 10.7639 sqft
1 sqyrd = 9 sqft
```

### Internal Normalization Rule

The system uses `sqft` as the standard internal calculation unit.

If the selected unit is:

```text
sqm   -> sqft = sqm * 10.7639
sqyrd -> sqft = sqyrd * 9
sqft  -> use directly
```

### Original Dataset Preservation Logic

PriceNest always preserves the original dataset values first.

For example, if the dataset contains:

```text
Carpet Area = 3000 sqft
Total Area  = 4000 sqft
Rate        = Rs. 21,250 per sqft
Price       = Rs. 8.53 Cr
```

The initial prediction output displays exactly:

```text
Carpet Area: 3000 sqft
Total Area: 4000 sqft
Rate per sqft: Rs. 21,250
Predicted Price: Rs. 8.53 Cr
```

Only when the user changes the unit does the UI convert the display values.

### Centralized Utility Functions

The project uses reusable logic for:

- `normalizeToSqft()`
- `convertArea()`
- `convertRate()`
- `calculateTotalArea()`
- `formatDisplayValues()`

This keeps carpet area, total area, rate, and prediction display synchronized.

---

## Dynamic Filtering Logic

PriceNest prevents invalid selections by dynamically filtering dropdowns based on available dataset combinations.

### Filtering Order

```text
City
-> Location
-> Property Type
-> Bedrooms
-> Floor
-> Facing
-> Balcony
-> Parking
-> Carpet Area
```

Each field depends on the previous selected values.

### Why This Matters

Dynamic filtering ensures:

- Users see only valid dataset values.
- Wrong property combinations are avoided.
- Prediction accuracy improves.
- The form feels intelligent and dataset-aware.

### Not Available Logic

If a field has no valid dataset values for the selected combination, the UI displays:

```text
Not Available
```

and disables that field.

---

## Authentication System

PriceNest uses Firebase Authentication for login features.

### Google Sign-In

Google Sign-In is implemented using Firebase Authentication. Users can sign in with their Google account, and the app dynamically fetches:

- Full name
- Email address
- Profile session

### Mobile OTP Authentication

Mobile OTP authentication is partially implemented using Firebase Phone Auth UI flow.

However, Firebase SMS OTP requires billing to be enabled on the Firebase project. If billing is not enabled, the app displays a clean user-friendly message:

```text
Mobile OTP authentication is temporarily unavailable.
Please continue using Google Sign In.
```

Raw Firebase technical errors are not shown to users.

### Profile and Logout

After login, the user can:

- Open the profile popup
- View Google account details
- Log out safely
- Return to the default login state

---

## Google Maps Integration

The project includes a Google Map section that displays the selected property area.

### Map Features

- Location-based map rendering
- City and locality-based map context
- Responsive map card
- Clean premium UI styling

### APIs Mentioned

- Google Maps Embed API
- Google Maps JavaScript API
- Geocoding API
- Places API / Nearby Places Integration

Depending on API key availability and configuration, the project can be extended to fetch live nearby places dynamically.

---

## Nearby Facilities Feature

The Nearby Facilities section provides a clean view of important facilities around a selected property location.

### Facility Categories

- Hospital
- School
- Metro Station
- Mall

The UI is designed to remain clean and professional even when live Places API data is unavailable.

---

## Project Workflow

The complete PriceNest workflow is:

1. User opens the PriceNest web application.
2. User selects city and location.
3. Dynamic filters update based on the selected dataset records.
4. User selects property type, bedrooms, floor, facing, balcony, parking, carpet area, unit, and amenities.
5. Backend searches for matching dataset rows.
6. If a dataset match exists, original dataset values are preserved.
7. ML prediction logic processes the selected inputs when required.
8. Amenities adjustment is applied as a post-processing layer.
9. Unit conversion is applied only for display.
10. Prediction Price card updates dynamically.
11. Google Map and nearby facility sections display property context.
12. Database insights and demand sections provide additional market information.

---

## Folder Structure

```text
PriceNest/
|
|-- app.py
|
|-- backend/
|   |-- app.py
|   |-- config.py
|   |
|   |-- auth/
|   |   `-- README.md
|   |
|   |-- data/
|   |   |-- properties.csv
|   |   `-- README.md
|   |
|   |-- model/
|   |   |-- price_nest_model.py
|   |   `-- README.md
|   |
|   |-- routes/
|   |   |-- auth.py
|   |   |-- frontend.py
|   |   |-- insights.py
|   |   |-- maps.py
|   |   |-- prediction.py
|   |   `-- properties.py
|   |
|   |-- services/
|   |   |-- prediction_service.py
|   |   `-- README.md
|   |
|   |-- utils/
|   |   |-- request_helpers.py
|   |   `-- README.md
|   |
|   `-- requirements.txt
|
|-- frontend/
|   |-- App.jsx
|   |
|   |-- components/
|   |   |-- Navbar/
|   |   |-- Hero/
|   |   |-- PropertyForm/
|   |   |-- Amenities/
|   |   |-- PredictionPanel/
|   |   |-- MapSection/
|   |   |-- DatabaseInsights/
|   |   |-- PropertyDemand/
|   |   |-- About/
|   |   |-- HowItWorks/
|   |   |-- FAQ/
|   |   `-- Footer/
|   |
|   |-- assets/
|   |-- pages/
|   |-- styles/
|   `-- utils/
|
|-- static/
|   |-- css/
|   |   `-- styles.css
|   |
|   `-- js/
|       |-- app.js
|       `-- firebase.js
|
|-- templates/
|   `-- index.html
|
`-- README.md
```

### Structure Note

The Flask server serves the active frontend from:

- `templates/index.html`
- `static/css/styles.css`
- `static/js/app.js`
- `static/js/firebase.js`

The `frontend/` folder keeps a clean modular source structure for future React/Vite build expansion.

---

## Installation Guide

### 1. Clone or Download the Project

```bash
git clone <your-repository-url>
cd PriceNest
```

If you already have the project folder, open it directly in VS Code or your preferred editor.

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Run the Flask Application

```bash
python app.py
```

### 5. Open the Website

```text
http://127.0.0.1:5000
```

Important: do not run the project using VS Code Live Server on port `5500`. PriceNest is designed as a single Flask full-stack application running on port `5000`.

---

## Environment Variables

Create a `.env` file or set environment variables directly if you want to override default configuration values.

```env
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=True

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_firebase_app_id
FIREBASE_MEASUREMENT_ID=your_measurement_id
```

### Notes

- Google Sign-In requires a valid Google OAuth client ID.
- Google Maps features require a valid Google Maps API key.
- Firebase Phone OTP may require billing to be enabled for SMS delivery.

---

## API Information

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Loads the PriceNest frontend |
| `GET` | `/health` | Checks backend and model health |
| `GET` | `/options` | Returns dataset-driven dropdown options |
| `GET` | `/locations` | Returns locations by selected city |
| `GET` | `/filter-options` | Returns cascading filtered options |
| `POST` | `/match-row` | Finds matching dataset row |
| `POST` | `/predict` | Generates property price prediction |
| `GET` | `/inventory` | Returns database insight data |
| `GET` | `/demand` | Returns property demand data |
| `GET` | `/search` | Searches property records |
| `GET` | `/properties` | Returns property records |
| `GET` | `/top-properties` | Returns selected property listings |
| `GET` | `/auth/config` | Returns authentication configuration |
| `GET` | `/maps/config` | Returns map configuration |
| `POST` | `/nearby` | Nearby places integration endpoint |

### Example Prediction Request

```json
{
  "city": "Delhi",
  "location": "Vasant Vihar",
  "property_type": "Apartment/Flat",
  "bedrooms": "4",
  "floor": "2 out of 4",
  "facing": "North-East",
  "balcony": "3",
  "parking": "2 Covered",
  "carpet_area": "3000",
  "unit": "sqft",
  "amenities": {
    "gym": "No",
    "lift": "Yes",
    "security": "Yes",
    "power_backup": "No"
  }
}
```

---

## Future Improvements

- Full React/Vite frontend build pipeline
- MongoDB Atlas support for storing user reports and saved properties
- Live Google Places API nearby results with distance calculation
- Admin dashboard for dataset management
- User saved predictions
- PDF report export with enhanced branding
- More cities and pan-India property data
- Advanced model comparison and model versioning
- Better explainability using feature importance
- Payment or subscription-based premium insights

---

## Screenshots Section

Add your project screenshots here before publishing to GitHub.

### Home Page

```md
![Home Page](screenshots/home.png)
```

### Smart Property Analyzer

```md
![Smart Property Analyzer](screenshots/property-form.png)
```

### Prediction Price Panel

```md
![Prediction Price](screenshots/prediction-panel.png)
```

### Authentication Modal

```md
![Authentication Modal](screenshots/auth-modal.png)
```

### Google Map Section

```md
![Google Map](screenshots/google-map.png)
```

---

## Author Information

**Project Name:** PriceNest  
**Project Type:** AI + Machine Learning + Full Stack Web Application  
**Domain:** Real Estate Technology  
**Target Region:** Delhi and Delhi NCR  

### Developer

```text
Name: Your Name
GitHub: https://github.com/your-username
LinkedIn: https://linkedin.com/in/your-profile
Email: your-email@example.com
```

You can replace the placeholder author details with your own information before publishing the repository.

---

## Professional Conclusion

PriceNest demonstrates how machine learning, dataset-driven filtering, unit-aware calculations, authentication, and modern UI design can work together in a real-world full-stack application.

The project preserves original dataset values as the primary source of truth, applies dynamic conversions only at the display layer, and keeps prediction calculations internally consistent. This makes PriceNest a strong portfolio-ready AI real estate project with practical technical depth and a professional user experience.

---

## License

This project is created for educational and portfolio purposes. You may update this section with your preferred license before publishing.
