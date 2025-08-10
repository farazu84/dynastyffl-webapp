import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config)
    with app.app_context():
        setup_db(app)
        db.init_app(app)

        from app.endpoints import (
            test,
            users,
            teams,
            articles,
            matchups
        )

        app.register_blueprint(test.test)
        app.register_blueprint(users.users)
        app.register_blueprint(teams.teams)
        app.register_blueprint(articles.articles)

    return app

def setup_db(app):
    server_user = os.environ['SQL_USER']
    password = os.environ['SQL_PASSWORD']
    host = os.environ['SQL_HOST']
    database = os.environ['DB_NAME']
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{server_user}:{password}@{host}/{database}'