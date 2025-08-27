import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix


db = SQLAlchemy()

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config)
    setup_db(app)
    db.init_app(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Enable CORS for all routes and origins
    cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, origins=[origin.strip() for origin in cors_origins])

    from app.endpoints import (
        test,
        users,
        teams,
        articles,
        matchups,
        league
    )

    app.register_blueprint(test.test)
    app.register_blueprint(users.users)
    app.register_blueprint(teams.teams)
    app.register_blueprint(articles.articles)
    app.register_blueprint(matchups.matchups)
    app.register_blueprint(league.league)

    return app

def setup_db(app):
    try:
        server_user = os.environ['SQL_USER']
        password = os.environ['SQL_PASSWORD']
        host = os.environ['SQL_HOST']
        database = os.environ['DB_NAME']
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{server_user}:{password}@{host}/{database}'
        print(f"Database URI configured: mysql+pymysql://{server_user}:***@{host}/{database}")
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fallback.db'  # Fallback for testing