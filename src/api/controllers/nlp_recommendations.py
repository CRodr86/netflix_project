from flask import Blueprint, request, jsonify

import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from api.models import Movie, Serie, User

nlp_bp = Blueprint("nlp_bp", __name__)

# Configurações do modelo NLP
directorio_proyecto = os.path.dirname(os.path.abspath(__file__))
nlp_resources_dir = os.path.join(directorio_proyecto, "nlp_resources")

df_netflix_bd = pd.read_csv(os.path.join(nlp_resources_dir, "df_netflix_bd.csv"))
description_process = np.load(
    os.path.join(nlp_resources_dir, "description_process.npy")
)
genres_process = np.load(os.path.join(nlp_resources_dir, "genres_process.npy"))
director_process = np.load(os.path.join(nlp_resources_dir, "director_process.npy"))

cosine_sim_description = cosine_similarity(description_process, description_process)
cosine_sim_genres = cosine_similarity(genres_process, genres_process)
cosine_sim_director = cosine_similarity(director_process, director_process)

combined_embedding = (
    0.5 * cosine_sim_description + 0.3 * cosine_sim_director + 0.2 * cosine_sim_genres
)

titles = df_netflix_bd["id"]
indices = pd.Series(df_netflix_bd.index, index=df_netflix_bd["id"])


def get_recommendations(title, item_type, user_age, seen_ids, top_n=10):
    idx = indices[title]
    sim_scores = list(enumerate(combined_embedding[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:]  # Ignorar o primeiro, pois é o mesmo filme/série

    # Filtrar por tipo
    if item_type == "movie":
        filtered_scores = [
            score
            for score in sim_scores
            if df_netflix_bd.iloc[score[0]]["type"] == "movie"
        ]
    elif item_type == "tv-show":
        filtered_scores = [
            score
            for score in sim_scores
            if df_netflix_bd.iloc[score[0]]["type"] == "tv-show"
        ]
    else:
        filtered_scores = []

    # Filtrar por idade
    if user_age < 6:
        age_filters = ["all audiences"]
    elif 6 <= user_age < 12:
        age_filters = ["children", "all audiences"]
    elif 12 <= user_age < 15:
        age_filters = ["youngs", "children", "all audiences"]
    elif 15 <= user_age < 18:
        age_filters = ["teenagers", "youngs", "children", "all audiences"]
    else:
        age_filters = ["adults", "teenagers", "youngs", "children", "all audiences"]

    filtered_scores = [
        score
        for score in filtered_scores
        if df_netflix_bd.iloc[score[0]]["public"] in age_filters
    ]
    filtered_scores = [
        score
        for score in filtered_scores
        if df_netflix_bd.iloc[score[0]]["id"] not in seen_ids
    ]
    filtered_scores = filtered_scores[:top_n]

    movie_indices = [i[0] for i in filtered_scores]
    return titles.iloc[movie_indices].tolist()


@nlp_bp.route("/nlp-recommendations", methods=["POST"])
def nlp_recommendations():
    data = request.get_json()

    item_id = data.get("item_id")
    item_type = data.get("item_type")
    user_id = data.get("user_id")

    if not item_id or not item_type or user_id is None:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        item_id = int(item_id)
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid id or user_id parameter"}), 400

    if item_type not in ["movie", "serie"]:
        return jsonify({"error": "Invalid type parameter"}), 400

    # Recuperar idade do usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_age = user.age

    # Recuperar filmes e séries já avaliados pelo usuário
    seen_movie_ids = {rating.movie_id for rating in user.movies_ratings}
    seen_serie_ids = {rating.serie_id for rating in user.series_ratings}

    seen_ids = seen_movie_ids if item_type == "movie" else seen_serie_ids

    # Mapear 'serie' para 'tv-show' no dataframe
    df_item_type = "movie" if item_type == "movie" else "tv-show"

    # Buscar recomendações
    recommendations_ids = get_recommendations(item_id, df_item_type, user_age, seen_ids)

    # Recuperar dados do banco de dados
    if item_type == "movie":
        recommendations = Movie.query.filter(Movie.id.in_(recommendations_ids)).all()
    else:
        recommendations = Serie.query.filter(Serie.id.in_(recommendations_ids)).all()

    recommendations_data = [rec.serialize() for rec in recommendations]

    return jsonify(recommendations_data), 200
