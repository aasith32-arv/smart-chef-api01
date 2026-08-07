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


class TestAuthServiceLoginLookup:
    def test_get_by_email_success(self, app, sample_user):
        found = AuthService.get_by_email(sample_user.email)
        assert found is not None
        assert found.id == sample_user.id
        assert found.check_password("secret12")

    def test_get_by_email_missing(self, app):
        assert AuthService.get_by_email("missing@example.com") is None

    def test_wrong_password_fails_check(self, app, sample_user):
        found = AuthService.get_by_email(sample_user.email)
        assert found.check_password("wrong-password") is False


class TestAuthServiceProfile:
    def test_update_profile_fields(self, app, sample_user):
        user, error, status = AuthService.update_profile(
            sample_user, {"full_name": "Updated Name"}
        )
        assert status == 200
        assert error is None
        assert user.full_name == "Updated Name"

    def test_update_duplicate_email(self, app, sample_user):
        AuthService.register(
            {
                "username": "other",
                "email": "other@example.com",
                "password": "secret12",
            }
        )
        user, error, status = AuthService.update_profile(
            sample_user, {"email": "other@example.com"}
        )
        assert user is None
        assert status == 409

    def test_delete_profile(self, app, sample_user):
        ok, error, status = AuthService.delete_profile(sample_user)
        assert ok is True
        assert status == 200
        assert AuthService.get_by_email("tester@example.com") is None
