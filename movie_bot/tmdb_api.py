import os
import requests

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

# Función para obtener películas populares para los banners informativos
def get_popular_movies(limit=5):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/movie/popular"
    params = {"api_key": api_key, "language": "es", "page": 1}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    movies = response.json().get("results", [])
    banners = []
    for movie in movies[:limit]:
        banners.append({
            "title": movie["title"],
            "description": movie.get("overview", "Sin descripción disponible."),
            "image_url": f"https://image.tmdb.org/t/p/w500{movie['backdrop_path']}" if movie.get("backdrop_path") else "/static/images/default_banner.jpg"
        })
    return banners

# Función para obtener películas para el carrusel, con descripciones cortas
def get_carousel_banners(limit=5):
    api_key = os.getenv("TMDB_API_KEY")
    base_url = "https://api.themoviedb.org/3"
    url = f"{base_url}/movie/popular"
    params = {"api_key": api_key, "language": "es", "page": 1}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return []

    movies = response.json().get("results", [])
    banners = []
    for movie in movies[:limit]:
        banners.append({
            "title": movie["title"],
            "short_description": movie.get("overview", "Sin descripción disponible.")[:150],  # Descripción corta
            "image_url": f"https://image.tmdb.org/t/p/w500{movie['backdrop_path']}" if movie.get("backdrop_path") else "/static/images/default_banner.jpg"
        })
    return banners
