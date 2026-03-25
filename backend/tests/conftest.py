import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.database import Base, get_db
from app.models.user import User, SwitchStatus
from app.models.beneficiary import Beneficiary
from app.models.trusted_verifier import TrustedVerifier
from app.models.secret import Secret, SecretType
from app.models.secret_assignment import SecretAssignment
import app.models  # noqa: F401

# ── In-memory SQLite engine ────────────────────────────────────────────────────
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    from app.main import app
    from unittest.mock import patch

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # Patch the scheduler to avoid event loop issues in tests
    with patch("app.main.scheduler") as mock_scheduler:
        mock_scheduler.start.return_value = None
        mock_scheduler.shutdown.return_value = None
        mock_scheduler.add_job.return_value = None
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_email():
    with patch("app.utils.email.send_checkin_reminder") as m1, \
         patch("app.utils.email.send_verifier_alert") as m2, \
         patch("app.utils.email.send_beneficiary_release") as m3, \
         patch("app.utils.email.send_no_verifier_warning") as m4, \
         patch("app.services.release_service.send_beneficiary_release") as m3b, \
         patch("app.services.scheduler.send_checkin_reminder") as m1b, \
         patch("app.services.scheduler.send_verifier_alert") as m2b:
        m1.return_value = None
        m2.return_value = None
        m3.return_value = None
        m4.return_value = None
        m1b.return_value = None
        m2b.return_value = None
        m3b.return_value = None
        yield {"reminder": m1, "verifier_alert": m2, "release": m3b, "no_verifier": m4}


@pytest.fixture()
def test_user(db_session):
    from app.services.auth_service import hash_password
    user = User(
        email="owner@test.com",
        password_hash=hash_password("password123"),
        name="Test Owner",
        is_active=True,
        switch_status=SwitchStatus.active,
        check_in_interval_days=30,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def test_user_b(db_session):
    from app.services.auth_service import hash_password
    user = User(
        email="other@test.com",
        password_hash=hash_password("password123"),
        name="Other User",
        is_active=True,
        switch_status=SwitchStatus.active,
        check_in_interval_days=30,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(test_user):
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}


@pytest.fixture()
def auth_headers_b(test_user_b):
    from app.services.auth_service import create_access_token
    token = create_access_token(test_user_b.id)
    return {"Authorization": f"Bearer {token}", "X-Requested-With": "XMLHttpRequest"}


@pytest.fixture()
def beneficiary_with_key(db_session, test_user):
    from app.services.encryption_service import generate_rsa_keypair
    public_pem, private_pem = generate_rsa_keypair()
    b = Beneficiary(
        user_id=test_user.id,
        name="Alice Beneficiary",
        email="alice@test.com",
        public_key=public_pem,
    )
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)
    return b, private_pem


@pytest.fixture()
def secret_with_assignment(db_session, test_user, beneficiary_with_key):
    from app.services.secret_service import create_secret
    beneficiary, private_pem = beneficiary_with_key
    password = "my-secret-password"
    secret = create_secret(
        db=db_session,
        user_id=test_user.id,
        title="Test Secret",
        content="super secret content",
        secret_type=SecretType.note,
        password=password,
        beneficiary_ids=[beneficiary.id],
    )
    return secret, beneficiary, private_pem, password


@pytest.fixture()
def verifier_alerted_user(db_session, test_user):
    import secrets as secrets_module
    test_user.switch_status = SwitchStatus.verifier_alerted
    v = TrustedVerifier(
        user_id=test_user.id,
        name="Verifier Person",
        email="verifier@test.com",
        verification_token=secrets_module.token_urlsafe(32),
        denial_token=secrets_module.token_urlsafe(32),
    )
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    db_session.refresh(test_user)
    return test_user, v
