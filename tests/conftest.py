import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db
from app.models.auth import User
from app.models.config import Project, FoldType, SimType


@pytest.fixture()
def app():
    app = create_app('testing')
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture()
def user(db_session):
    user = User(username='tester', email='tester@example.com', valid=1)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def auth_headers(app, user):
    with app.app_context():
        token = create_access_token(identity=str(user.id))
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture()
def project(db_session):
    project = Project(name='Demo Project', code='DEMO', valid=1, sort=1)
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture()
def fold_type(db_session):
    fold_type = FoldType(name='Default', code='DEFAULT', angle=0, valid=1, sort=1)
    db_session.add(fold_type)
    db_session.commit()
    return fold_type


@pytest.fixture()
def sim_type(db_session):
    sim_type = SimType(name='Static', code='STATIC', category='STRUCTURE', valid=1, sort=1)
    db_session.add(sim_type)
    db_session.commit()
    return sim_type
