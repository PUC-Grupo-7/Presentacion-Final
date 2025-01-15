import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from .db import db, db_config
from .models import User, Message
from .forms import ProfileForm
from .tmdb_api import get_streaming_platforms, get_movie_rating, get_similar_movies, get_all_movies, get_movies_by_year, extract_year_from_message
import openai
from openai.error import AuthenticationError, RateLimitError, OpenAIError
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import logging

# Cargar las variables del entorno desde el archivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialización de Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta_predeterminada")
db_config(app)
Bootstrap5(app)

# Configurar la API de OpenAI desde el entorno de Render
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurar Flask-Migrate
migrate = Migrate(app, db)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def landing():
    """
    Página principal con banners informativos y películas populares.
    """
    # Obtener datos para las películas populares (esto puede ser diferente de las películas del carrusel)
    popular_movies = get_all_movies(limit=6)

    # Obtener películas para el carrusel (con información diferente)
    carousel_banners = get_all_movies(limit=5)  # Podría ser un conjunto diferente de películas

    return render_template("landing.html", title="Página de Inicio", popular_movies=popular_movies, carousel_banners=carousel_banners)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            flash("El correo ya está registrado.", "danger")
        else:
            new_user = User(email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registro exitoso. Por favor, inicia sesión.", "success")
            return redirect(url_for("login"))
    return render_template("signup.html", title="Registro")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for("chat"))
        flash("Credenciales inválidas.", "danger")
    return render_template("login.html", title="Inicio de Sesión")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cierre de sesión exitoso.", "success")
    return redirect(url_for("login"))

@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    """
    Página de chat con MovieBot.
    Permite enviar mensajes al bot y guardar el historial.
    """
    try:
        if request.method == "POST":
            user_message = request.form.get("message")
            if not user_message or user_message.strip() == "":
                flash("El mensaje no puede estar vacío.", "danger")
                messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.timestamp.asc()).all()
                return render_template("chat.html", messages=messages, title="Chat")

            # Guardar el mensaje del usuario
            db.session.add(Message(content=user_message, author="user", user=current_user))
            db.session.commit()

            # Extraer el año de la película si se menciona
            year = extract_year_from_message(user_message)

            if year:
                # Consultar películas del año especificado
                result = get_movies_by_year(year, limit=5)
                if "error" in result:
                    bot_reply = result["error"]
                elif "message" in result:
                    bot_reply = result["message"]
                else:
                    movie_titles = [movie["title"] for movie in result]
                    bot_reply = f"Estas son algunas películas del año {year}: {', '.join(movie_titles)}."
            else:
                # Si no se menciona un año, mostramos todas las películas disponibles
                result = get_all_movies(limit=5)
                if "error" in result:
                    bot_reply = result["error"]
                elif "message" in result:
                    bot_reply = result["message"]
                else:
                    movie_titles = [movie["title"] for movie in result]
                    bot_reply = f"Estas son algunas de las películas disponibles: {', '.join(movie_titles)}."

            # Guardar respuesta del bot
            db.session.add(Message(content=bot_reply, author="assistant", user=current_user))
            db.session.commit()

        # Consultar mensajes del historial
        messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.timestamp.asc()).all()
        return render_template("chat.html", messages=messages, title="Chat")

    except Exception as e:
        logger.error(f"Error en /chat: {e}")
        return "Ha ocurrido un error interno en el servidor.", 500

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    try:
        form = ProfileForm(obj=current_user)

        if form.validate_on_submit():
            current_user.favorite_genre = form.favorite_genre.data
            current_user.disliked_genre = form.disliked_genre.data
            db.session.commit()
            flash("Perfil actualizado exitosamente.", "success")
            return redirect(url_for('perfil'))

        return render_template("perfil.html", form=form, title="Editar Perfil")
    except Exception as e:
        logger.error(f"Error en /perfil: {e}")
        return "Ha ocurrido un error interno en el servidor.", 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
