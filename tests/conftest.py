import pytest

from app import create_app
from app.extensions import db
from app.models import Ingredient, Recipe, User


@pytest.fixture(autouse=True)
def isolate_ai_credentials(monkeypatch):
    """Prevent a developer's local AI credentials from causing network calls in tests."""
    monkeypatch.setenv("AI_PROVIDER", "none")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_COOKIE_SECURE": False,
            "JWT_COOKIE_CSRF_PROTECT": False,
            "RATELIMIT_ENABLED": False,
        }
    )

    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_recipe(app):
    recipe = Recipe(
        name="Test Curry",
        category="Curry",
        description="A test curry",
        serving_size=4,
        steps=["Step 1", "Step 2"],
        image=None,
    )
    db.session.add(recipe)
    db.session.flush()
    db.session.add_all(
        [
            Ingredient(recipe_id=recipe.id, name="Chicken", quantity=500, unit="g"),
            Ingredient(recipe_id=recipe.id, name="Onion", quantity=2, unit="piece"),
            Ingredient(recipe_id=recipe.id, name="Oil", quantity=30, unit="ml"),
        ]
    )
    db.session.commit()
    return recipe


@pytest.fixture()
def sample_user(app):
    user = User(username="tester", email="tester@example.com", full_name="Test User")
    user.set_password("secret12")
    db.session.add(user)
    db.session.commit()
    return user
