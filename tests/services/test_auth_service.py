from app.services.auth_service import AuthService


class TestAuthServiceRegister:
    def test_register_success(self, app):
        user, error, status = AuthService.register(
            {
                "username": "chef1",
                "email": "chef1@example.com",
                "password": "secret12",
                "full_name": "Chef One",
            }
        )
        assert status == 201
        assert error is None
        assert user is not None
        assert user.email == "chef1@example.com"
        assert user.check_password("secret12")

    def test_duplicate_email(self, app, sample_user):
        user, error, status = AuthService.register(
            {
                "username": "other",
                "email": sample_user.email,
                "password": "secret12",
            }
        )
        assert user is None
        assert status == 409
        assert "Email" in error

    def test_duplicate_username(self, app, sample_user):
        user, error, status = AuthService.register(
            {
                "username": sample_user.username,
                "email": "unique@example.com",
                "password": "secret12",
            }
        )
        assert user is None
        assert status == 409
        assert "Username" in error

