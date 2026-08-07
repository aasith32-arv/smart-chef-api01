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

| Method | Endpoint                      | Description                    |
|--------|-------------------------------|--------------------------------|
| GET    | `/recipes`                    | List recipes (search, filter)  |
| GET    | `/recipes/<id>`               | Get recipe by ID               |
| POST   | `/recipes`                    | Create recipe                  |
| PUT    | `/recipes/<id>`               | Update recipe                  |
| DELETE | `/recipes/<id>`               | Delete recipe                  |
| GET    | `/recipes/category/<category>`| Filter by category             |

**Query params for GET /recipes:** `search`, `category`, `page`, `per_page`

### Calculator

| Method | Endpoint      | Description                         |
|--------|---------------|-------------------------------------|
| POST   | `/calculate`  | Scale ingredient quantities         |

**Example request:**
```json
{
  "recipe": "Chicken Biryani",
  "people": 50
}
```

**Example response:**
```json
{
  "success": true,
  "data": {
    "recipe": "Chicken Biryani",
    "people": 50,
    "serving_size": 4,
    "quantities": {
      "Rice": "7.5 kg",
      "Chicken": "10 kg",
      "Onion": "5 kg",
      "Tomato": "3 kg",
      "Oil": "2 L",
      "Salt": "250 g"
    }
  }
}
```

### Recommendation

| Method | Endpoint      | Description                          |
|--------|---------------|--------------------------------------|
| POST   | `/recommend`  | Recommend recipes by ingredients     |

**Example request:**
```json
{
  "ingredients": ["rice", "egg", "onion"]
}
```

### Favorites (JWT required)

| Method | Endpoint                  | Description           |
|--------|---------------------------|-----------------------|
| GET    | `/favorites`              | List favorites        |
| POST   | `/favorites`              | Add favorite          |
| DELETE | `/favorites/<recipe_id>`  | Remove favorite       |

## Switching to MySQL

Set in `.env`:

```env
USE_MYSQL=true
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aichef_db
```

Or use a full connection string:

```env
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/aichef_db
```

## Sample Recipes

The `data/recipes.json` file includes 10 recipes:

1. Chicken Biryani
2. Vegetable Fried Rice
3. Chicken Fried Rice
4. Egg Fried Rice
5. Kottu
6. Nasi Goreng
7. Vegetable Curry
8. Chicken Curry
9. Dhal Curry
10. Fish Curry

## License

Final Year Project – Educational Use
