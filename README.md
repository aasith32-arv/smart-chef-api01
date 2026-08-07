# AI Chef – Smart Food Quantity Calculator API

Backend REST API for the Final Year Project **AI Chef**, an AI-powered food quantity calculator that helps users scale ingredient quantities based on the number of people, recommend recipes from available ingredients, and manage favorite recipes.

## Tech Stack

- Python 3
- Flask
- Flask-JWT-Extended (Authentication)
- Flask-SQLAlchemy
- SQLite (default) / MySQL (configurable)
- Flask-CORS
- Werkzeug Password Hashing
- Flasgger (Swagger API documentation)

## Project Structure

```
flask-student-api/
├── app/
│   ├── __init__.py          # App factory, error handlers, Swagger
│   ├── config.py            # Environment-based configuration
│   ├── extensions.py        # SQLAlchemy & JWT extensions
│   ├── models/
│   │   ├── user.py
│   │   ├── recipe.py
│   │   ├── ingredient.py
│   │   └── favorite.py
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── recipe_routes.py
│   │   ├── calculator_routes.py
│   │   ├── recommendation_routes.py
│   │   └── favorite_routes.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── recipe_service.py
│   │   ├── calculator_service.py
│   │   ├── recommendation_service.py
│   │   └── favorite_service.py
│   ├── validators/
│   └── utils/
├── data/
│   └── recipes.json         # Sample recipes (10 recipes)
├── instance/                # SQLite database (auto-created)
├── run.py
├── run_seeders.py
└── requirements.txt
```

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env` and set your `JWT_SECRET_KEY`.

### 4. Run the application

```bash
python run.py
```

The API runs at `http://localhost:5000`.

Swagger documentation: `http://localhost:5000/apidocs`

### 5. Seed database (optional)

```bash
python run_seeders.py
```

## API Endpoints

### Authentication

| Method | Endpoint       | Auth | Description          |
|--------|----------------|------|----------------------|
| POST   | `/register`    | No   | Register new user    |
| POST   | `/login`       | No   | Login & get JWT      |
| GET    | `/profile`     | Yes  | Get user profile     |
| PUT    | `/profile`     | Yes  | Update profile       |
| DELETE | `/profile`     | Yes  | Delete account       |

### Recipes
