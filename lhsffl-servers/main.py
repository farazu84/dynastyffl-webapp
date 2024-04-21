import time
from app import create_app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import DevConfig

app = create_app(DevConfig)

if __name__ == '__main__':
    app.run()
