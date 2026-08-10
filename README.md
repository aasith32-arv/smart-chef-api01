# AI Chef API

AI Chef is a Flask REST API for recipe management, ingredient-based recipe recommendations, food quantity calculation, favorites, and optional AI-assisted meal planning and translation.

The API supports SQLite for local development and MySQL for deployment. Authentication uses access and refresh JWTs through secure HTTP-only cookies, while Bearer-token authentication remains available for API clients.

## Features

- User registration, login, logout, profile management, and token refresh
- HTTP-only JWT cookies with CSRF protection
- Bearer-token support for tools such as Swagger and Postman
- Recipe CRUD operations with ingredients and preparation steps
- Backward-compatible category → dish family → recipe variety discovery
- Curated catalog of 23 families and 189 scalable recipes
- Ingredient quantity scaling for any number of people
- Recipe recommendations based on available ingredients
- Per-user favorite recipes
- Optional OpenAI meal plans, dish suggestions, and translations
- Local recipe fallback when OpenAI is not configured
- Pagination, filtering, search, request rate limiting, and CORS
- Swagger API documentation
- Database migrations and sample recipe seed data
- Health check, structured request logging, and optional Sentry monitoring
- Automated tests with pytest
- Database-backed Admin authorization, catalog management, account moderation, and audit logging
- AI Cooking Intelligence with structured sequences, heat/timing guidance, observable doneness,
  transformations, personalization, substitutions, troubleshooting, and deterministic fallback

## Dish families and recipe varieties

`DishFamily` groups related recipes while each final variety remains an ordinary `Recipe`. The
`family_id` relationship and recipe metadata are nullable, so existing user-created recipes,
favorites, calculator requests, and `/recipes/{id}` URLs continue working.

Apply all migrations through `d491b7a0c2e5`, then run the existing idempotent seeder. It adds or enriches records
by stable slug/name without deleting existing recipes or replacing IDs.

Endpoints:

- `GET /api/v1/dish-families`
- `GET /api/v1/dish-families/<slug>`
- `GET /api/v1/dish-families/<slug>/recipes`

`GET /api/v1/recipes` also supports family, cuisine, region, protein, diet, difficulty, spice, and
maximum-cooking-time filters. Search includes family and recipe discovery metadata.

## AI Cooking Intelligence

The cooking intelligence API extends existing recipes without replacing their original steps.
Plans use curated `cooking_steps` rows when present and otherwise generate clearly labeled
rule-based guidance from stored recipe instructions.

Endpoints:

- `GET|POST /api/v1/recipes/<id>/cooking-plan`
- `GET /api/v1/recipes/<id>/cooking-steps`
- `POST /api/v1/cooking/troubleshoot`
- `POST /api/v1/cooking/substitute`
- `POST /api/v1/cooking/explain`

Apply the additive schema migration before using these endpoints:

```bash
.venv/bin/python -m flask --app run:app db upgrade
python3 run.py
```

No new environment variables are required. Existing `AI_PROVIDER`, `OPENAI_API_KEY`, and
`GEMINI_API_KEY` settings optionally enhance explanation-oriented endpoints. Ordinary cooking-plan
generation remains deterministic and works without AI.

See [AI Cooking Intelligence Architecture](docs/AI_COOKING_INTELLIGENCE_ARCHITECTURE.md) for the
module flow, validation boundary, safety behavior, limitations, and extension points.

## Stripe billing

Authenticated users can purchase an LKR 1,200 monthly Premium subscription or an LKR 2,000
one-time advertising package through Stripe-hosted Checkout. Advertising payments create an order
in `under_review`; they never publish content automatically.

Billing endpoints:

- `POST /api/v1/billing/checkout/subscription`
- `POST /api/v1/billing/checkout/advertising`
- `POST /api/v1/billing/portal`
- `GET /api/v1/billing/status`
- `POST /api/v1/billing/webhook`

Configure `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `FRONTEND_URL`. Reusable Stripe Dashboard
prices can be set with `STRIPE_SUBSCRIPTION_PRICE_ID` and `STRIPE_ADVERTISING_PRICE_ID`; otherwise
the server supplies trusted inline LKR prices. `STRIPE_PUBLISHABLE_KEY` is retained for future
embedded payment UI, but Stripe-hosted Checkout does not expose or require it in the browser.

For a Vercel frontend proxying to Railway, configure Railway with `JWT_COOKIE_SECURE=true`,
`JWT_COOKIE_SAMESITE=Lax`, `JWT_COOKIE_CSRF_PROTECT=true`, and leave `JWT_COOKIE_DOMAIN` unset.
Set `FRONTEND_URL` to the canonical Vercel/custom-domain URL. The proxy keeps JWT and CSRF cookies
first-party; API responses are marked `private, no-store` to prevent CDN caching.

## Admin management

Admin APIs reuse the existing recipe and billing services and are protected by `@admin_required`.
The decorator verifies the JWT, reloads the current user, and requires both `role=admin` and an
active account. Public recipe APIs expose only records with `publication_status=published`.

Create the first Admin securely with the interactive CLI:

```bash
.venv/bin/python -m flask --app run:app create-admin
```

No default Admin password exists. Registration cannot set a role. Admin recipe edits retain the
same recipe ID and relationships; deactivation uses publication status instead of deleting catalog
content. Admin-managed seed records are not overwritten on subsequent seed runs.

Admin endpoints are rooted at `/api/v1/admin` and cover dashboard aggregates, recipes, dish
families, categories, users, advertisements, payments, and safe settings. Mutation actions are
recorded in `admin_audit_logs`.

For local webhook testing:

```bash
stripe listen --forward-to localhost:5000/api/v1/billing/webhook
```

In production, register the HTTPS webhook URL in Stripe and subscribe to `checkout.session.completed`,
`checkout.session.async_payment_succeeded`, `customer.subscription.created`,
`customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, and
`invoice.payment_failed`. Use the signing secret for that exact endpoint.

## Technology Stack

- Python 3.10+
- Flask 3
- Flask-SQLAlchemy and SQLAlchemy
- Flask-Migrate and Alembic
- Flask-JWT-Extended
- Flask-Limiter
- Flask-CORS
- Flasgger / Swagger
- SQLite or MySQL
- Gunicorn
- pytest

## Project Structure

```text
smart-chef-api01/
├── app/
│   ├── controllers/       # HTTP request and response handling
│   ├── models/            # SQLAlchemy database models
│   ├── routes/            # API route definitions
│   ├── seeders/           # Sample recipe seeder
│   ├── services/          # Business logic
│   ├── utils/             # Response and time helpers
│   ├── validators/        # Request validation
│   ├── __init__.py        # Application factory and extension setup
│   ├── config.py          # Environment-based configuration
│   ├── extensions.py      # Flask extension instances
│   └── middleware.py      # Shared middleware helpers
├── data/
│   └── recipes.json       # Sample recipes
├── instance/
│   └── aichef.db          # Local SQLite database (generated)
├── migrations/            # Alembic database migrations
├── postman/               # Postman collection files
├── tests/                 # Automated test suite
├── .env.example           # Example environment configuration
├── Procfile               # Gunicorn process declaration
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development dependencies
├── run.py                 # Application entry point
└── run_seeders.py         # Recipe seeding entry point
```

## Prerequisites

- Python 3.10 or newer
- `pip`
- MySQL only if you do not want to use the default SQLite database

## Installation

### 1. Clone and enter the project

```bash
git clone <repository-url>
cd smart-chef-api01
```

### 2. Create and activate a virtual environment

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

The development requirements are only needed for tests and code-quality tools.

### 4. Configure the environment

Linux or macOS:

```bash
cp .env.example .env
```

Windows:

```powershell
Copy-Item .env.example .env
```

Change at least `SECRET_KEY` and `JWT_SECRET_KEY` before using the application outside local development.

### 5. Apply database migrations

```bash
flask --app run:app db upgrade
```

SQLite is used by default and creates `instance/aichef.db` automatically.

### 6. Seed the curated recipe catalog

```bash
python run_seeders.py
```

Alternatively:

```bash
flask --app run:app seed
```

### 7. Start the API

Development server:

```bash
python run.py
```

Production-style server:

```bash
gunicorn run:app
```

The default URLs are:

- API home: `http://localhost:5000/`
- Health check: `http://localhost:5000/health`
- Swagger UI: `http://localhost:5000/apidocs`
- API base: `http://localhost:5000/api/v1`

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | Development fallback | Flask application secret; replace in production |
| `FLASK_DEBUG` | `True` in the example | Enables Flask debug behavior when recognized by Flask |
| `LOG_LEVEL` | `INFO` | Application logging level |
| `JWT_SECRET_KEY` | Development fallback | JWT signing secret; use a unique value in production |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | `15` | Access-token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | `30` | Refresh-token lifetime |
| `JWT_COOKIE_SECURE` | `false` | Use `true` when the frontend and API use HTTPS |
| `JWT_COOKIE_SAMESITE` | `Lax` | JWT cookie SameSite policy |
| `JWT_COOKIE_CSRF_PROTECT` | `true` | Enables CSRF checks for cookie authentication |
| `JWT_COOKIE_DOMAIN` | Empty | Optional shared cookie domain |
| `DATABASE_URL` | Empty | Complete SQLAlchemy connection URL; takes priority over other DB settings |
| `USE_MYSQL` | `false` | Switches from SQLite to MySQL |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | Empty | MySQL password |
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_NAME` | `aichef_db1` | MySQL database name |
| `DEFAULT_PAGE_SIZE` | `10` | Default recipe page size |
| `MAX_PAGE_SIZE` | `50` | Maximum recipe page size |
| `CORS_ORIGINS` | Local frontend URLs | Comma-separated allowed origins; wildcard is rejected |
| `RATELIMIT_STORAGE_URI` | `memory://` | Rate-limit storage backend |
| `AI_PROVIDER` | `auto` | Provider selection: `auto`, `openai`, or `gemini` |
| `OPENAI_API_KEY` | Empty | Enables OpenAI-backed AI features |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model used by AI endpoints |
| `GEMINI_API_KEY` | Empty | Enables Gemini-backed AI features |
| `GEMINI_MODEL` | `gemini-flash-latest` | Model used for Gemini requests |
| `SENTRY_DSN` | Empty | Enables Sentry when supplied |
| `SENTRY_ENVIRONMENT` | `development` | Sentry environment name |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.0` | Sentry trace sampling rate |

For production, use HTTPS, set `JWT_COOKIE_SECURE=true`, choose explicit CORS origins, use strong secrets, and configure persistent rate-limit storage such as Redis.

## Database Configuration

### SQLite

No additional configuration is required. Leave `USE_MYSQL=false` and do not set `DATABASE_URL`.

### MySQL

Create a database, then configure `.env`:

```env
USE_MYSQL=true
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aichef_db
```

You can instead provide one connection string:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/aichef_db
```

Apply migrations after changing databases:

```bash
flask --app run:app db upgrade
```

## Authentication

Registration and login set access and refresh tokens as HTTP-only cookies. Tokens are not returned in the JSON body.

Browser clients using cookies must:

1. Send requests with credentials enabled.
2. Read the non-HTTP-only CSRF cookie.
3. Send its value as `X-CSRF-TOKEN` on protected mutating requests.

API tools may authenticate protected routes with:

```http
Authorization: Bearer <access-token>
```

Accounts have a database-backed `user` or `admin` role and an active/suspended status. There is no
default Admin email or password; use the interactive `create-admin` command. Passwords are stored
as hashes and cannot be read back as plain text. Suspended accounts are rejected during login,
refresh, and protected-request token verification.

## API Response Format

Successful responses follow this general structure:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

Validation and other errors follow this structure:

```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "field": "Description of the problem."
  }
}
```

## API Endpoints

All business endpoints use the `/api/v1` prefix.

### General

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `GET` | `/` | No | API metadata and route summary |
| `GET` | `/health` | No | API and database health check |
| `GET` | `/apidocs` | No | Swagger UI |

### Authentication and Profile

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `POST` | `/api/v1/register` | No | Create an account and set JWT cookies |
| `POST` | `/api/v1/login` | No | Log in and set JWT cookies |
| `POST` | `/api/v1/refresh` | Refresh token | Issue a new access-token cookie |
| `POST` | `/api/v1/logout` | Access token | Revoke tokens and clear cookies |
| `GET` | `/api/v1/profile` | Access token | Get the current profile |
| `PUT` | `/api/v1/profile` | Access token | Update profile fields or password |
| `DELETE` | `/api/v1/profile` | Access token | Delete the current account |

### Recipes

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `GET` | `/api/v1/recipes` | No | List, search, filter, and paginate recipes |
| `GET` | `/api/v1/recipes/{id}` | No | Get one recipe |
| `GET` | `/api/v1/recipes/category/{category}` | No | List recipes in a category |
| `POST` | `/api/v1/recipes` | Access token | Create a recipe |
| `PUT` | `/api/v1/recipes/{id}` | Access token | Update a recipe |
| `DELETE` | `/api/v1/recipes/{id}` | Access token | Delete a recipe |

Recipe-list query parameters:

- `search`: partial recipe-name search
- `category`: category filter
- `page`: page number, starting at 1
- `per_page`: items per page, capped by `MAX_PAGE_SIZE`

### Calculator and Recommendations

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `POST` | `/api/v1/calculate` | No | Scale a stored recipe for a guest count |
| `POST` | `/api/v1/recommend` | No | Match recipes against pantry ingredients |

Set `partial=false` on `/recommend` to exclude recipes that are not complete ingredient matches.

### Favorites

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `GET` | `/api/v1/favorites` | Access token | List the current user's favorites |
| `POST` | `/api/v1/favorites` | Access token | Add a recipe to favorites |
| `DELETE` | `/api/v1/favorites/{recipe_id}` | Access token | Remove a recipe from favorites |

### AI Features

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `GET` | `/api/v1/ai/status` | No | Show AI configuration status |
| `POST` | `/api/v1/ai/plan` | No | Generate a scaled meal plan |
| `POST` | `/api/v1/ai/suggest` | No | Suggest dishes from pantry ingredients |
| `POST` | `/api/v1/ai/translate` | No | Translate structured recipe content |

Meal plans and suggestions fall back to locally stored recipes when OpenAI is unavailable. Translation returns the original content when no AI key is configured.

### Administration

| Method | Endpoint | Authentication | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/dashboard` | Admin | Aggregate statistics and recent activity |
| `GET`, `POST` | `/api/v1/admin/recipes` | Admin | Paginated recipes and transactional creation |
| `GET`, `PUT`, `DELETE` | `/api/v1/admin/recipes/{id}` | Admin | Detail, edit, and deactivate |
| `POST` | `/api/v1/admin/recipes/{id}/duplicate` | Admin | Duplicate as a new draft |
| `GET`, `POST` | `/api/v1/admin/dish-families` | Admin | List and create families |
| `PUT`, `DELETE` | `/api/v1/admin/dish-families/{id}` | Admin | Edit or safely delete an empty family |
| `GET`, `PATCH` | `/api/v1/admin/categories` | Admin | Aggregate and rename categories |
| `GET`, `PATCH` | `/api/v1/admin/users[/{id}]` | Admin | List and moderate accounts |
| `GET`, `PATCH` | `/api/v1/admin/advertisements[/{id}]` | Admin | List and moderate paid ads |
| `GET` | `/api/v1/admin/payments` | Admin | Read-only subscription monitoring |
| `GET` | `/api/v1/admin/settings` | Admin | Non-sensitive configuration status |

## Request Examples

### Register

```bash
curl -i -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"username":"chefuser","email":"chef@example.com","password":"strongpass123","full_name":"Chef User"}' \
  http://localhost:5000/api/v1/register
```

Username must contain at least 3 characters and password must contain at least 6 characters.

### Login

```bash
curl -i -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"email":"chef@example.com","password":"strongpass123"}' \
  http://localhost:5000/api/v1/login
```

### List Recipes

```bash
curl "http://localhost:5000/api/v1/recipes?search=rice&category=Main&page=1&per_page=10"
```

### Create a Recipe

The following example uses a Bearer access token. Browser clients can use the authentication cookies and CSRF header instead.

```bash
curl -X POST http://localhost:5000/api/v1/recipes \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Vegetable Rice",
    "category": "Main",
    "description": "A simple vegetable rice dish.",
    "serving_size": 4,
    "image": "https://example.com/vegetable-rice.jpg",
    "ingredients": [
      {"name": "Rice", "quantity": 500, "unit": "g"},
      {"name": "Mixed vegetables", "quantity": 300, "unit": "g"}
    ],
    "steps": [
      "Wash and cook the rice.",
      "Cook the vegetables and combine with the rice."
    ]
  }'
```

### Calculate Ingredient Quantities

```bash
curl -X POST http://localhost:5000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"recipe":"Chicken Biryani","people":50}'
```

### Recommend Recipes

```bash
curl -X POST "http://localhost:5000/api/v1/recommend?partial=true" \
  -H "Content-Type: application/json" \
  -d '{"ingredients":["rice","egg","onion"]}'
```

### Add a Favorite

```bash
curl -X POST http://localhost:5000/api/v1/favorites \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipe_id":1}'
```

### Generate an AI Meal Plan

```bash
curl -X POST http://localhost:5000/api/v1/ai/plan \
  -H "Content-Type: application/json" \
  -d '{"dish":"Chicken Biryani","people":10,"language":"en"}'
```

### Suggest Dishes with AI or Local Fallback

```bash
curl -X POST http://localhost:5000/api/v1/ai/suggest \
  -H "Content-Type: application/json" \
  -d '{"ingredients":["rice","egg","onion"],"language":"en"}'
```

### Translate Recipe Content

```bash
curl -X POST http://localhost:5000/api/v1/ai/translate \
  -H "Content-Type: application/json" \
  -d '{
    "language":"ta",
    "content":{
      "dish":"Vegetable Rice",
      "description":"A simple rice dish.",
      "ingredients":[],
      "steps":["Cook the rice."],
      "tips":[]
    }
  }'
```

## Running Tests

Run the complete test suite:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

Run lint checks:

```bash
ruff check .
```

## Database Migration Commands

After changing a model, create and apply a migration:

```bash
flask --app run:app db migrate -m "describe the change"
flask --app run:app db upgrade
```

Inspect migration history:

```bash
flask --app run:app db history
```

Roll back the most recent migration:

```bash
flask --app run:app db downgrade
```

## Rate Limits

The application currently applies these route-specific limits:

- Registration: 5 requests per minute
- Login: 10 requests per minute
- Token refresh: 30 requests per minute
- AI meal plans: 20 requests per minute
- AI suggestions: 30 requests per minute
- AI translations: 40 requests per minute

Rate-limit responses use HTTP status `429`.

## Deployment Notes

The included `Procfile` starts the service with:

```text
web: gunicorn run:app
```

Before deploying:

- Use unique, high-entropy values for both secret keys.
- Enable secure cookies and HTTPS.
- Restrict `CORS_ORIGINS` to trusted frontend domains.
- Use MySQL or another managed production database through `DATABASE_URL`.
- Apply migrations before starting the new application version.
- Use Redis or another shared backend for rate limits with multiple workers.
- Keep `.env`, database files, and API keys out of version control.
- Configure Sentry only when monitoring is required.

## Troubleshooting

### Database tables do not exist

```bash
flask --app run:app db upgrade
```

### A recipe cannot be found by the calculator

Seed the database and use the stored recipe name:

```bash
python run_seeders.py
curl http://localhost:5000/api/v1/recipes
```

### Browser authentication returns a CSRF error

Ensure the frontend sends cookies, reads the CSRF cookie, and supplies its value in the `X-CSRF-TOKEN` header for protected state-changing requests.

### AI features use local results

Check `/api/v1/ai/status`, then verify that `AI_PROVIDER` and the matching API key/model are set in
`smart-chef-api01/.env`. Restart the Flask backend after changing environment variables.

### CORS fails at startup

Do not use `*` in `CORS_ORIGINS` because authentication cookies are enabled. Supply explicit comma-separated frontend origins.

## Security

- Never commit `.env` or real secrets.
- Do not expose JWTs, API keys, or database passwords in logs.
- Passwords are hashed with Werkzeug before storage.
- Rotate any secret that has been accidentally shared.
- Validate production cookie and CORS settings before release.

## License

No license file is currently included. Add a `LICENSE` file before distributing or open-sourcing the project.
