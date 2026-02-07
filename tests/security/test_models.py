from app.database.models import APIKey, User


def test_api_key_defaults(db_session):
    user = User(email="user@example.com", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    api_key = APIKey(user_id=user.id, key_hash="hash")
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert api_key.is_active is True
    assert api_key.rate_limit == 100
    assert api_key.created_at is not None


def test_user_defaults(db_session):
    user = User(email="another@example.com", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.is_active is True
    assert user.created_at is not None
