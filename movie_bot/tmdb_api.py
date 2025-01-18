# movie_bot/tmdb_api.py
import os
import requests
import logging

logger = logging.getLogger(__name__)

def get_streaming_platforms(movie_name, region="US"):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    if not api_key:
        return {"error": "No se ha configurado la clave de TMDB (TMDB_API_KEY)."}

    search_url = f"{base_url}/search/movie"
    params = {
        "api_key": api_key,
        "query": movie_name,
        "region": region
    }
    try:
        response = requests.get(search_url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_streaming_platforms] Error HTTP: {e}")
        return {"error": "Error al conectar con TMDB."}

    if response.status_code != 200:
        return {"error": f"Error al conectar con TMDB (status code: {response.status_code})."}

    results = response.json().get("results", [])
    if not results:
        return {"error": f"No se encontró la película '{movie_name}' en TMDB."}

    # Seleccionamos la mejor coincidencia (por ej. la de mayor puntuación)
    movie = max(results, key=lambda x: x.get("vote_average", 0))
    movie_id = movie["id"]

    watch_providers_url = f"{base_url}/movie/{movie_id}/watch/providers"
    try:
        response = requests.get(watch_providers_url, params={"api_key": api_key})
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_streaming_platforms] Error HTTP: {e}")
        return {"error": "Error al obtener información de streaming."}

    if response.status_code != 200:
        return {"error": f"Error al obtener información de streaming (status code: {response.status_code})."}

    providers = response.json().get("results", {}).get(region, {}).get("flatrate", [])
    if not providers:
        return {"message": f"No se encontró información de streaming para '{movie_name}' en la región {region}."}

    platforms = [{"id": p["provider_id"], "name": p["provider_name"], "logo": p["logo_path"]} for p in providers]
    return {"movie_id": movie_id, "movie": movie_name, "platforms": platforms}


def get_movie_rating(movie_name):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    if not api_key:
        return {"error": "No se ha configurado la clave de TMDB (TMDB_API_KEY)."}

    search_url = f"{base_url}/search/movie"
    params = {"api_key": api_key, "query": movie_name}
    try:
        response = requests.get(search_url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_movie_rating] Error HTTP: {e}")
        return {"error": "Error al conectar con TMDB."}

    if response.status_code != 200:
        return {"error": f"Error al conectar con TMDB (status code: {response.status_code})."}

    results = response.json().get("results", [])
    if not results:
        return {"error": f"No se encontró la película '{movie_name}'."}

    # Seleccionamos la mejor coincidencia
    movie = max(results, key=lambda x: x.get("vote_average", 0))
    rating = movie.get("vote_average", "No disponible")

    return {"movie_id": movie["id"], "movie": movie_name, "rating": rating}


def get_similar_movies(movie_name, language="en"):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    if not api_key:
        return {"error": "No se ha configurado la clave de TMDB (TMDB_API_KEY)."}

    search_url = f"{base_url}/search/movie"
    params = {"api_key": api_key, "query": movie_name, "language": language}
    try:
        response = requests.get(search_url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_similar_movies] Error HTTP: {e}")
        return {"error": "Error al conectar con TMDB."}

    if response.status_code != 200:
        return {"error": f"Error al conectar con TMDB (status code: {response.status_code})."}

    results = response.json().get("results", [])
    if not results:
        return {"error": f"No se encontró la película '{movie_name}'."}

    # Tomamos la mejor coincidencia
    movie = max(results, key=lambda x: x.get("vote_average", 0))
    movie_id = movie["id"]

    similar_url = f"{base_url}/movie/{movie_id}/similar"
    try:
        response = requests.get(similar_url, params={"api_key": api_key, "language": language})
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_similar_movies] Error HTTP al obtener similares: {e}")
        return {"error": "Error al obtener recomendaciones."}

    if response.status_code != 200:
        return {"error": f"Error al obtener recomendaciones (status code: {response.status_code})."}

    similar_movies = response.json().get("results", [])
    if not similar_movies:
        return {"message": f"No se encontraron recomendaciones para '{movie_name}'."}

    movies = [
        {
            "id": m.get("id"),
            "title": m.get("title", "Sin título"),
            "release_date": m.get("release_date", "Fecha desconocida")
        }
        for m in similar_movies
    ]
    return {"movie_id": movie_id, "movie": movie_name, "recommendations": movies}


def get_movie_trailer(movie_name):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    if not api_key:
        return {"error": "No se ha configurado la clave de TMDB (TMDB_API_KEY)."}

    search_url = f"{base_url}/search/movie"
    params = {"api_key": api_key, "query": movie_name, "language": "es"}
    try:
        response = requests.get(search_url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_movie_trailer] Error HTTP al buscar la película: {e}")
        return {"error": "Error al conectar con TMDB."}

    if response.status_code != 200:
        return {"error": f"Error al conectar con TMDB (status code: {response.status_code})."}

    results = response.json().get("results", [])
    if not results:
        return {"error": f"No se encontró la película '{movie_name}'."}

    # Seleccionamos la mejor coincidencia
    movie = max(results, key=lambda x: x.get("vote_average", 0))
    movie_id = movie["id"]

    videos_url = f"{base_url}/movie/{movie_id}/videos"
    params = {"api_key": api_key, "language": "es"}
    try:
        response_videos = requests.get(videos_url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_movie_trailer] Error HTTP al obtener videos: {e}")
        return {"error": "Error al obtener los videos de la película."}

    if response_videos.status_code != 200:
        return {"error": f"Error al obtener videos (status code: {response_videos.status_code})."}

    videos_data = response_videos.json().get("results", [])
    if not videos_data:
        return {"message": "No hay tráiler disponible para esta película."}

    for video in videos_data:
        if video.get("type", "").lower() == "trailer" and video.get("site", "").lower() == "youtube":
            youtube_key = video["key"]
            youtube_url = f"https://www.youtube.com/watch?v={youtube_key}"
            return {"trailer_url": youtube_url}

    return {"message": "No se encontró un tráiler de YouTube para esta película."}


def get_popular_movies(limit=5, region="US", language="es", page=1):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/movie/popular"

    if not api_key:
        logger.warning("[get_popular_movies] TMDB_API_KEY no configurada.")
        return []

    params = {
        "api_key": api_key,
        "language": language,
        "region": region,
        "page": page
    }
    try:
        response = requests.get(url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_popular_movies] Error HTTP al obtener películas populares: {e}")
        return []

    if response.status_code != 200:
        logger.error(f"[get_popular_movies] Código de estado inesperado: {response.status_code}")
        return []

    movies = response.json().get("results", [])
    banners = []
    for movie in movies[:limit]:
        title = movie.get("title", "Sin título")
        description = movie.get("overview", "Sin descripción disponible.")
        backdrop_path = movie.get("backdrop_path")

        image_url = f"https://image.tmdb.org/t/p/w500{backdrop_path}" if backdrop_path else "/static/images/default_banner.jpg"
        banners.append({
            "id": movie.get("id"),
            "title": title,
            "description": description,
            "image_url": image_url
        })

    return banners


def get_carousel_banners(limit=5, region="US", language="es", page=1):
    """
    Similar a get_popular_movies, pero podemos usar la misma fuente (películas populares),
    cambiando la página para evitar duplicar los mismos resultados.
    """
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/movie/popular"

    if not api_key:
        logger.warning("[get_carousel_banners] TMDB_API_KEY no configurada.")
        return []

    params = {
        "api_key": api_key,
        "language": language,
        "region": region,
        "page": page
    }
    try:
        response = requests.get(url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_carousel_banners] Error HTTP al obtener películas populares: {e}")
        return []

    if response.status_code != 200:
        logger.error(f"[get_carousel_banners] Código de estado inesperado: {response.status_code}")
        return []

    movies = response.json().get("results", [])
    banners = []
    for movie in movies[:limit]:
        title = movie.get("title", "Sin título")
        overview = movie.get("overview", "Sin descripción disponible.")
        short_desc = overview[:150]
        backdrop_path = movie.get("backdrop_path")

        image_url = f"https://image.tmdb.org/t/p/w500{backdrop_path}" if backdrop_path else "/static/images/default_banner.jpg"
        banners.append({
            "id": movie.get("id"),
            "title": title,
            "short_description": short_desc,
            "image_url": image_url
        })

    return banners


def get_now_playing_movies(limit=5, region="US", language="es"):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/movie/now_playing"

    if not api_key:
        return {"error": "No se ha configurado la clave de TMDB (TMDB_API_KEY)."}

    params = {
        "api_key": api_key,
        "language": language,
        "region": region,
        "page": 1
    }
    try:
        response = requests.get(url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[get_now_playing_movies] Error HTTP: {e}")
        return {"error": "Error al conectar con TMDB."}

    if response.status_code != 200:
        logger.error(f"[get_now_playing_movies] Código de estado inesperado: {response.status_code}")
        return {"error": f"Error al conectar con TMDB (status code: {response.status_code})."}

    data = response.json()
    results = data.get("results", [])
    if not results:
        return {"message": "No hay películas recientes en cartelera disponibles."}

    results = results[:limit]
    movies = []
    for movie in results:
        title = movie.get("title", "Título desconocido")
        release_date = movie.get("release_date", "Fecha desconocida")
        overview = movie.get("overview", "Sin descripción disponible.")
        backdrop_path = movie.get("backdrop_path")

        image_url = f"https://image.tmdb.org/t/p/w500{backdrop_path}" if backdrop_path else "/static/images/default_banner.jpg"
        movies.append({
            "id": movie.get("id"),
            "title": title,
            "release_date": release_date,
            "overview": overview,
            "image_url": image_url
        })

    return {"movies": movies}


def discover_movies_by_genre(genre_id, limit=5, region="US", language="es", page=1):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    discover_url = f"{base_url}/discover/movie"

    if not api_key:
        return {"error": "No se ha configurado la clave de TMDB (TMDB_API_KEY)."}

    params = {
        "api_key": api_key,
        "language": language,
        "region": region,
        "sort_by": "popularity.desc",
        "with_genres": genre_id,
        "page": page
    }
    try:
        response = requests.get(discover_url, params=params)
    except requests.exceptions.RequestException as e:
        logger.error(f"[discover_movies_by_genre] Error HTTP al buscar: {e}")
        return {"error": "Error al conectar con TMDB."}

    if response.status_code != 200:
        logger.error(f"[discover_movies_by_genre] Código de estado inesperado: {response.status_code}")
        return {"error": f"Error al obtener películas por género (status code: {response.status_code})."}

    data = response.json()
    results = data.get("results", [])
    if not results:
        return {"message": "No se encontraron películas para este género en este momento."}

    results = results[:limit]
    movies = []
    for movie in results:
        title = movie.get("title", "Título desconocido")
        release_date = movie.get("release_date", "Fecha desconocida")
        overview = movie.get("overview", "Sin descripción disponible.")
        backdrop_path = movie.get("backdrop_path")
        movie_id = movie.get("id")

        image_url = f"https://image.tmdb.org/t/p/w500{backdrop_path}" if backdrop_path else "/static/images/default_banner.jpg"
        movies.append({
            "id": movie_id,
            "title": title,
            "release_date": release_date,
            "overview": overview,
            "image_url": image_url
        })

    return {"movies": movies}
