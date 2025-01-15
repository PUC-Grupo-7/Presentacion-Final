import os
import requests
import re

# Función para obtener plataformas de streaming de una película
def get_streaming_platforms(movie_name, region="US"):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    # Buscar la película por nombre
    search_url = f"{base_url}/search/movie"
    params = {"api_key": api_key, "query": movie_name, "region": region}
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return {"error": "Error al conectar con TMDB."}

    results = response.json().get("results")
    if not results:
        return {"error": f"No se encontró la película '{movie_name}'."}

    # Tomar el primer resultado
    movie_id = results[0]["id"]

    # Obtener las plataformas de streaming
    watch_providers_url = f"{base_url}/movie/{movie_id}/watch/providers"
    response = requests.get(watch_providers_url, params={"api_key": api_key})
    if response.status_code != 200:
        return {"error": "Error al obtener información de streaming."}

    providers = response.json().get("results", {}).get(region, {}).get("flatrate", [])
    if not providers:
        return {"message": f"No se encontró información de streaming para '{movie_name}' en la región {region}."}

    # Formatear la respuesta
    platforms = [{"name": p["provider_name"], "logo": p["logo_path"]} for p in providers]
    return {"movie": movie_name, "platforms": platforms}

# Función para obtener la evaluación de una película
def get_movie_rating(movie_name):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    # Buscar la película por nombre
    search_url = f"{base_url}/search/movie"
    params = {"api_key": api_key, "query": movie_name}
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return {"error": "Error al conectar con TMDB."}

    results = response.json().get("results")
    if not results:
        return {"error": f"No se encontró la película '{movie_name}'."}

    # Tomar el primer resultado
    movie = results[0]
    rating = movie.get("vote_average", "No disponible")

    return {"movie": movie_name, "rating": rating}

# Función para obtener películas similares a una película dada
def get_similar_movies(movie_name):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"

    # Buscar la película por nombre
    search_url = f"{base_url}/search/movie"
    params = {"api_key": api_key, "query": movie_name}
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return {"error": "Error al conectar con TMDB."}

    results = response.json().get("results")
    if not results:
        return {"error": f"No se encontró la película '{movie_name}'."}

    # Tomar el primer resultado
    movie_id = results[0]["id"]

    # Obtener películas similares
    similar_url = f"{base_url}/movie/{movie_id}/similar"
    response = requests.get(similar_url, params={"api_key": api_key})
    if response.status_code != 200:
        return {"error": "Error al obtener recomendaciones de películas."}

    similar_movies = response.json().get("results", [])
    if not similar_movies:
        return {"message": f"No se encontraron recomendaciones para '{movie_name}'."}

    # Formatear la respuesta
    movies = [{"title": m["title"], "release_date": m.get("release_date", "Fecha desconocida")} for m in similar_movies]
    return {"movie": movie_name, "recommendations": movies}

# Función para obtener todas las películas disponibles en TMDB
def get_all_movies(limit=5):
    """
    Obtiene una lista de todas las películas disponibles en TMDB.
    """
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/discover/movie"
    params = {
        "api_key": api_key,
        "language": "es",  
        "sort_by": "popularity.desc",  # Ordenamos por popularidad
        "page": 1
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return {"error": "Error al obtener las películas de TMDB."}

    movies = response.json().get("results", [])
    if not movies:
        return {"message": "No se encontraron películas."}

    # Formateamos los resultados
    movie_list = [{"title": m["title"], "description": m.get("overview", "Sin descripción disponible."),
                   "release_date": m["release_date"], "image_url": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else "/static/images/default_movie.jpg"} for m in movies[:limit]]
    
    return movie_list

# Función para obtener películas de un año específico
def get_movies_by_year(year, limit=5):
    """
    Obtiene una lista de películas de un año específico.
    """
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/discover/movie"
    params = {
        "api_key": api_key,
        "language": "es",
        "primary_release_year": year,  # Filtramos por el año solicitado
        "sort_by": "release_date.desc",  # Ordenamos por fecha de estreno
        "page": 1
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return {"error": "Error al obtener las películas del año solicitado."}

    movies = response.json().get("results", [])
    if not movies:
        return {"message": f"No se encontraron películas del año {year}."}

    # Formateamos los resultados
    movie_list = [{"title": m["title"], "description": m.get("overview", "Sin descripción disponible."),
                   "release_date": m["release_date"], "image_url": f"https://image.tmdb.org/t/p/w500{m['poster_path']}" if m.get("poster_path") else "/static/images/default_movie.jpg"} for m in movies[:limit]]
    
    return movie_list

# Función para extraer el año de una cadena de texto
def extract_year_from_message(message):
    """
    Extrae el año de una cadena de texto.
    """
    match = re.search(r'\b(20\d{2})\b', message)  # Captura cualquier año entre 2000 y 2099
    if match:
        return int(match.group(1))
    return None
