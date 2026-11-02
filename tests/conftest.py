import pytest
from werkzeug.security import generate_password_hash

import database.db as db


@pytest.fixture(scope="session")
def flask_app(tmp_path_factory):
    # app.py runs init_db()/seed_db() on import, so point DB_PATH away from spendly.db first.
    db.DB_PATH = str(tmp_path_factory.mktemp("import") / "import.db")
    from app import app
    return app


@pytest.fixture
def app(flask_app, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    flask_app.config.update(TESTING=True)
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make_user(name="Test User", email="test@example.com"):
        conn = db.get_db()
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash("password123")),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return user_id
    return _make_user


@pytest.fixture
def add_expense(app):
    def _add_expense(user_id, amount, category, date, description="Test"):
        conn = db.get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        conn.close()
    return _add_expense


@pytest.fixture
def login(client):
    def _login(user_id, name="Test User"):
        with client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["user_name"] = name
    return _login
