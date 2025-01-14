# movie_bot/db.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

# Cargar las variables de entorno
load_dotenv()

# Clase base para los modelos
class Base(DeclarativeBase):
    """
    Clase base para los modelos de SQLAlchemy.
    Permite que los modelos hereden funcionalidad común.
    """
    pass

# Instancia de SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Configuración de la base de datos
def db_config(app):
    """
    Configura la conexión de la base de datos para la aplicación Flask.

    Args:
        app: Instancia de Flask.
    """
    # Obtener el directorio base
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'db.sqlite3')
    app.config["SQLALCHEMY_DATABASE_URI"] = f'sqlite:///{db_path}'
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Inicializar la base de datos con la aplicación Flask
    db.init_app(app)
