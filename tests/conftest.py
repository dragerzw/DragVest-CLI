import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db as appdb
import app.models as models  # ensure models are imported and mappers registered


# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # create tables once per test session
    models.Base.metadata.create_all(bind=engine)
    # ensure the application uses the in-memory engine by default for tests
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    appdb.SessionLocal = TestSessionLocal
    yield
    # dispose engine to ensure connections are closed and avoid ResourceWarning
    try:
        engine.dispose()
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_session(monkeypatch):
    """
    Provide a SQLAlchemy Session bound to a transaction that's rolled back after each test.
    Also monkeypatch `app.db.SessionLocal` so application code uses sessions bound to the same
    transactional connection.
    """
    connection = engine.connect()
    transaction = connection.begin()

    SessionFactory = sessionmaker(bind=connection, autoflush=False, autocommit=False, expire_on_commit=False)

    # Monkeypatch the app's SessionLocal so that get_session() returns sessions bound to this connection
    monkeypatch.setattr(appdb, "SessionLocal", SessionFactory)

    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
        # rollback entire transaction and close connection after test
        transaction.rollback()
        connection.close()
