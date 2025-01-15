import os
import logging
import unicodedata

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv

import openai
from openai.error import AuthenticationError, RateLimitError, OpenAIError

# Ajusta según tu estructura de proyecto
from .db import db, db_config
from .models import User, Message
from .forms import ProfileForm
from .tmdb_api import (
    get_streaming_platforms,
    get_movie_rating,
    get_similar_movies,
    get_movie_trailer,
    get_now_playing_movies,
    get_popular_movies,
    get_carousel_banners
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta_predeterminada")

# Config DB
db_config(app)
Bootstrap5(app)
migrate = Migrate(app, db)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

openai.api_key = os.getenv("OPENAI_API_KEY")


# -----------------------------------------------------------
# Funciones de normalización de texto
# -----------------------------------------------------------

def remover_acentos(texto: str) -> str:
    """
    Elimina los acentos de cualquier carácter que los lleve.
    Ejemplo: 'evaluación' -> 'evaluacion', 'puntuación' -> 'puntuacion'
    """
    # Normalizamos a NFD para separar los acentos de las letras base
    normalized = unicodedata.normalize('NFD', texto)
    # Filtramos los caracteres de tipo Mn (mark nonspacing)
    sin_acentos = "".join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Volvemos a componer en NFC
    return unicodedata.normalize('NFC', sin_acentos)

def limpiar_texto(texto: str) -> str:
    """
    Convierte a minúsculas, elimina signos de puntuación básicos
    (¿ ? ¡ ! , . : ;) y elimina acentos de las palabras.
    """
    # 1. Convertimos a minúsculas
    texto = texto.lower()
    # 2. Eliminamos signos básicos de puntuación
    for ch in ["¿", "?", "¡", "!", ",", ".", ":", ";"]:
        texto = texto.replace(ch, "")
    # 3. Quitamos acentos (tildes)
    texto = remover_acentos(texto)
    # 4. Retornamos el string limpio y recortado
    return texto.strip()


# -----------------------------------------------------------
# Rutas de la aplicación
# -----------------------------------------------------------

@app.route("/")
def landing():
    """
    Página principal con banners informativos y películas populares.
    """
    popular_movies = get_popular_movies(limit=6)
    carousel_banners = get_carousel_banners(limit=5)
    return render_template(
        "landing.html",
        title="Página de Inicio",
        popular_movies=popular_movies,
        carousel_banners=carousel_banners
    )


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
        else:
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
    Envía mensajes, detecta intenciones y responde con datos de TMDB o GPT.
    """
    try:
        if request.method == "POST":
            user_message = request.form.get("message")

            # Validar mensaje vacío
            if not user_message or user_message.strip() == "":
                flash("El mensaje no puede estar vacío.", "danger")
                messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.timestamp.asc()).all()
                return render_template("chat.html", messages=messages, title="Chat")

            # Guardar el mensaje del usuario (tal cual)
            db.session.add(Message(content=user_message, author="user", user=current_user))
            db.session.commit()

            # Crear versión limpia para la detección de intenciones
            user_msg_clean = limpiar_texto(user_message)
            logger.info(f"[CHAT] Mensaje original: {user_message} | Mensaje limpio: {user_msg_clean}")

            # ---------------------------------------------------
            # 1. "donde puedo ver x"
            # ---------------------------------------------------
            if "donde puedo ver" in user_msg_clean:
                idx = user_msg_clean.find("donde puedo ver")
                offset = len("donde puedo ver")
                movie_name = user_msg_clean[idx + offset:].strip()

                result = get_streaming_platforms(movie_name, region="US")
                if "error" in result:
                    bot_reply = result["error"]
                elif "message" in result:
                    bot_reply = result["message"]
                else:
                    platforms = [p["name"] for p in result["platforms"]]
                    bot_reply = f"La película '{movie_name}' está disponible en: {', '.join(platforms)}."

            # ---------------------------------------------------
            # 2. "que evaluacion/puntuacion/rating tiene x"
            #    (tildes removidas => 'evaluacion', 'puntuacion', etc.)
            # ---------------------------------------------------
            elif (
                "que evaluacion tiene" in user_msg_clean or
                "que puntuacion tiene" in user_msg_clean or
                "que rating tiene" in user_msg_clean
            ):
                # Hallamos la frase coincidida
                possible_phrases = [
                    "que evaluacion tiene",
                    "que puntuacion tiene",
                    "que rating tiene"
                ]
                match_found = None
                for phrase in possible_phrases:
                    if phrase in user_msg_clean:
                        match_found = phrase
                        break

                if match_found:
                    idx = user_msg_clean.find(match_found)
                    offset = len(match_found)
                    movie_name = user_msg_clean[idx + offset:].strip()

                    result = get_movie_rating(movie_name)
                    if "error" in result:
                        bot_reply = result["error"]
                    else:
                        bot_reply = f"La película '{movie_name}' tiene una puntuación promedio de {result['rating']}."
                else:
                    bot_reply = "No entendí bien tu pregunta sobre la evaluación de la película."

            # ---------------------------------------------------
            # 3. "parecida a x"
            # ---------------------------------------------------
            elif "parecida a" in user_msg_clean:
                idx = user_msg_clean.find("parecida a")
                movie_name = user_msg_clean[idx + len("parecida a"):].strip()

                result = get_similar_movies(movie_name)
                if "error" in result:
                    bot_reply = result["error"]
                elif "message" in result:
                    bot_reply = result["message"]
                else:
                    recommendations = [
                        f"{m['title']} (estrenada el {m['release_date']})"
                        for m in result["recommendations"]
                    ]
                    bot_reply = (
                        f"Películas similares a '{movie_name}':\n" +
                        "\n".join(recommendations)
                    )

            # ---------------------------------------------------
            # 4. "muestras el trailer de x"
            # ---------------------------------------------------
            elif "muestras el trailer de" in user_msg_clean:
                idx = user_msg_clean.find("muestras el trailer de")
                offset = len("muestras el trailer de")
                movie_name = user_msg_clean[idx + offset:].strip()

                trailer_data = get_movie_trailer(movie_name)
                if "error" in trailer_data:
                    bot_reply = trailer_data["error"]
                elif "message" in trailer_data:
                    bot_reply = trailer_data["message"]
                else:
                    trailer_url = trailer_data["trailer_url"]
                    bot_reply = f"Aquí está el tráiler de '{movie_name}': {trailer_url}"

            # ---------------------------------------------------
            # 5. "me recomiendas x" / "recomiendame x"
            # ---------------------------------------------------
            elif "me recomiendas" in user_msg_clean or "recomiendame" in user_msg_clean:
                # Detección
                if "me recomiendas" in user_msg_clean:
                    idx = user_msg_clean.find("me recomiendas")
                    offset = len("me recomiendas")
                else:
                    idx = user_msg_clean.find("recomiendame")
                    offset = len("recomiendame")

                movie_name = user_msg_clean[idx + offset:].strip()

                if not movie_name or "pelicula" in movie_name or "reciente" in movie_name:
                    # Buscar estrenos
                    result = get_now_playing_movies(limit=5, region="US", language="es")
                    if "error" in result:
                        bot_reply = result["error"]
                    elif "message" in result:
                        bot_reply = result["message"]
                    else:
                        movie_list = result.get("movies", [])
                        if not movie_list:
                            bot_reply = "No encontré películas recientes en este momento."
                        else:
                            lines = [
                                f"{m['title']} (Estreno: {m['release_date']})"
                                for m in movie_list
                            ]
                            bot_reply = (
                                "Aquí tienes algunas películas recientes en cartelera:\n" +
                                "\n".join(lines)
                            )
                else:
                    # Buscar rating
                    result = get_movie_rating(movie_name)
                    if "error" in result:
                        bot_reply = result["error"]
                    else:
                        rating = result["rating"]
                        bot_reply = (
                            f"Para la película '{movie_name}', la puntuación promedio "
                            f"en TMDB es {rating}. ¿Te gustaría saber algo más?"
                        )

            # ---------------------------------------------------
            # 6. "peliculas mas recientes" / "estrenos"
            # ---------------------------------------------------
            elif "peliculas mas recientes" in user_msg_clean or "estrenos" in user_msg_clean:
                result = get_now_playing_movies(limit=5, region="US", language="es")
                if "error" in result:
                    bot_reply = result["error"]
                elif "message" in result:
                    bot_reply = result["message"]
                else:
                    movie_list = result.get("movies", [])
                    if not movie_list:
                        bot_reply = "No encontré películas recientes en este momento."
                    else:
                        lines = [
                            f"{m['title']} (Estreno: {m['release_date']})"
                            for m in movie_list
                        ]
                        bot_reply = (
                            "Aquí tienes algunas películas recientes en cartelera:\n" +
                            "\n".join(lines)
                        )

            # ---------------------------------------------------
            # 7. Caso genérico: GPT
            # ---------------------------------------------------
            else:
                system_prompt = f"""
                Eres un bot recomendador de películas llamado MovieBot.
                Género favorito del usuario: {current_user.favorite_genre or 'No especificado'}.
                Género que debe evitar: {current_user.disliked_genre or 'No especificado'}.
                Responde de forma breve y clara.
                """
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ]
                    )
                    bot_reply = response['choices'][0]['message']['content']
                except AuthenticationError:
                    bot_reply = "Error de autenticación con OpenAI. Verifica tu clave API."
                    logger.error("Error de autenticación con OpenAI.")
                except RateLimitError:
                    bot_reply = "Has excedido el límite de solicitudes a OpenAI. Intenta nuevamente más tarde."
                    logger.error("Límite de solicitudes excedido a OpenAI.")
                except OpenAIError as e:
                    bot_reply = f"Error general de OpenAI: {e}"
                    logger.error(f"Error general de OpenAI: {e}")
                except Exception as e:
                    bot_reply = f"Error inesperado: {e}"
                    logger.error(f"Error inesperado: {e}")

            # Guardar la respuesta del bot
            db.session.add(Message(content=bot_reply, author="assistant", user=current_user))
            db.session.commit()

        # Mostrar historial de mensajes
        messages = Message.query.filter_by(user_id=current_user.id).order_by(Message.timestamp.asc()).all()
        return render_template("chat.html", messages=messages, title="Chat")

    except Exception as e:
        logger.error(f"Error en /chat: {e}")
        return "Ha ocurrido un error interno en el servidor.", 500


@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    """
    Página para editar el perfil del usuario (género favorito, disliked_genre, etc.)
    """
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
    # En desarrollo, usa debug=True
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
