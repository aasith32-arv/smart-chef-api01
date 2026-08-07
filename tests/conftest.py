import pytest

from app import create_app
from app.extensions import db
from app.models import Ingredient, Recipe, User


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

