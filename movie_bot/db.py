# movie_bot/db.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

class Base(DeclarativeBase):
    """
    Clase base para los modelos de SQLAlchemy.
    """
    pass

db = SQLAlchemy(model_class=Base)

def db_config(app):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'db.sqlite3')
    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{db_path}'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
