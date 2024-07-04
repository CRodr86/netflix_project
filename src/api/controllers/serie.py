from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, or_
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import datetime
from api.utils import APIException
from api.models import Serie, SerieUserRating, User
from api import db

serie_bp = Blueprint("serie_bp", __name__)


@serie_bp.route("/first-series", methods=["POST"])
def get_first_series_by_genre():
    """
    Get series by genre.

    Route: /first-series
    Method: POST

    JSON Parameters:
        genre (list): A list of serie genres. Required.
        user_id (int): The ID of the user. Required.

    Returns:
        list: A list of dictionaries containing the details of the series.

    Status Codes:
        200: Successfully retrieved the series.
        400: Missing or invalid parameters.
    """
    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["genre", "user_id"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    genres = body["genre"]
    user_id = body["user_id"]

    if not isinstance(genres, list) or not genres:
        raise APIException(
            "The 'genre' field must be a non-empty list", status_code=400
        )

    # Retrieve user info
    user = User.query.get(user_id)
    if not user:
        raise APIException("User not found", status_code=404)

    user_age = user.age

    # Define the minimum age required for each rating
    age_restrictions = {
        "TV-Y": 0,
        "TV-Y7": 7,
        "TV-Y7-FV": 7,
        "TV-G": 0,
        "TV-PG": 10,
        "TV-14": 14,
        "TV-MA": 17,
        "G": 0,
        "PG": 10,
        "PG-13": 13,
        "R": 17,
        "NC-17": 18,
        "NR": 18,
        "UR": 18,
        "": 18,
    }

    # Create the filter conditions
    genre_filters = [Serie.genres.contains(genre) for genre in genres]

    # Query the series
    series = (
        Serie.query.filter(or_(*genre_filters))
        .filter(Serie.popularity != None)
        .order_by(Serie.popularity.desc())
        .limit(90)
        .all()
    )

    # Filter series based on user's age
    filtered_series = []
    for serie in series:
        serie_age_rating = age_restrictions.get(serie.age_rating, 18)
        if serie_age_rating <= user_age:
            filtered_series.append(serie.serialize())

    return jsonify(filtered_series)


@serie_bp.route("/series", methods=["POST"])
def get_series_by_genre():
    """
    Get series by genre.

    Route: /series
    Method: POST

    JSON Parameters:
        genre (list): A list of serie genres. Required.
        user_id (int): The ID of the user. Required.

    Returns:
        dict: A dictionary containing lists of series by genre.

    Status Codes:
        200: Successfully retrieved the series.
        400: Missing or invalid parameters.
    """
    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["genre", "user_id"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    genres = body["genre"]
    user_id = body["user_id"]

    if not isinstance(genres, list) or not genres:
        raise APIException(
            "The 'genre' field must be a non-empty list", status_code=400
        )

    all_series = []
    seen_series = set()

    # Retrieve user info
    user = User.query.get(user_id)
    if not user:
        raise APIException("User not found", status_code=404)

    user_age = user.age

    # Retrieve the series rated by the user
    rated_series = SerieUserRating.query.filter_by(user_id=user_id).all()
    rated_serie_ids = {rating.serie_id for rating in rated_series}

    # Define the minimum age required for each rating
    age_restrictions = {
        "TV-Y": 0,
        "TV-Y7": 7,
        "TV-Y7-FV": 7,
        "TV-G": 0,
        "TV-PG": 10,
        "TV-14": 14,
        "TV-MA": 17,
        "G": 0,
        "PG": 10,
        "PG-13": 13,
        "R": 17,
        "NC-17": 18,
        "NR": 18,
        "UR": 18,
        "": 18,
    }

    try:
        for genre in genres:
            genre_series = (
                Serie.query.filter(
                    Serie.genres.contains(genre),
                    Serie.popularity != None,
                    ~Serie.id.in_(seen_series),
                    ~Serie.id.in_(rated_serie_ids),
                )
                .order_by(Serie.popularity.desc())
                .limit(30)
                .all()
            )
            for serie in genre_series:
                serie_age_rating = age_restrictions.get(serie.age_rating, 18)
                if serie_age_rating <= user_age and serie.id not in seen_series:
                    seen_series.add(serie.id)
                    all_series.append({"genre": genre, "serie": serie})

        # Organize series by genre
        series_by_genre = {genre: [] for genre in genres}
        for item in all_series:
            series_by_genre[item["genre"]].append(item["serie"].serialize())

        return jsonify(series_by_genre)
    except SQLAlchemyError as e:
        raise APIException("Database error: " + str(e), status_code=500)


@serie_bp.route("/serie/<int:serie_id>/<int:user_id>", methods=["GET"])
def get_serie_by_id(serie_id, user_id):
    """
    Get a serie by its ID.

    Route: /serie/<int:serie_id>/<int:user_id>
    Method: GET

    Returns:
        dict: A dictionary containing the details of the serie. If the user has rated the serie,
                the dictionary will also contain the rating and the date and time of the rating.

    Status Codes:
        200: Successfully retrieved the serie.
        404: Serie not found.
    """
    # Check if the serie exists
    serie = Serie.query.get(serie_id)
    if not serie:
        raise APIException("Serie not found", status_code=404)

    # Check if the user has rated the serie
    rating = SerieUserRating.query.filter_by(user_id=user_id, serie_id=serie_id).first()
    if rating:
        serie_data = {
            "serie": serie.serialize(),
            "rating": rating.rating,
            "date_rated": rating.date_rated,
        }
    else:
        serie_data = {"serie": serie.serialize()}

    return jsonify(serie_data)


@serie_bp.route("/rate-serie", methods=["POST"])
def rate_serie():
    """
    Rate a serie.

    Route: /rate-serie
    Method: POST

    JSON Parameters:
        serie_id (int): The ID of the serie to be rated. Required.
        user_id (int): The ID of the user rating the serie. Required.
        rating (str): The rating given by the user. Required.

    Returns:
        dict: A message indicating success or failure.

    Status Codes:
        200: Successfully rated the serie.
        400: Missing or invalid parameters.
        404: Serie or user not found.
        500: Internal server error.
    """
    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["serie_id", "user_id"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    serie_id = body["serie_id"]
    user_id = body["user_id"]
    rating = body.get("rating", None)

    if rating is None:
        raise APIException("The 'rating' field is required", status_code=400)

    try:
        # Check if the serie exists
        serie = Serie.query.get(serie_id)
        if not serie:
            raise APIException("Serie not found", status_code=404)

        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            raise APIException("User not found", status_code=404)

        # Check if the user has already rated this serie
        existing_rating = SerieUserRating.query.filter_by(
            user_id=user_id, serie_id=serie_id
        ).first()

        if rating == "":
            # If the rating is empty, remove the existing rating
            if existing_rating:
                db.session.delete(existing_rating)
                db.session.commit()
                return jsonify({"message": "Rating removed"}), 200
            else:
                return jsonify({"message": "No existing rating to remove"}), 200
        else:
            # Validate rating
            if not isinstance(rating, str):
                raise APIException("Invalid rating value", status_code=400)

            if existing_rating:
                # Update the existing rating
                existing_rating.rating = rating
                existing_rating.date_rated = datetime.datetime.now()
            else:
                # Add a new rating
                new_rating = SerieUserRating(
                    user_id=user_id,
                    serie_id=serie_id,
                    rating=rating,
                    date_rated=datetime.datetime.now(),
                )
                db.session.add(new_rating)

            db.session.commit()

            return jsonify({"message": "Successfully rated the serie"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        raise APIException("Database error: " + str(e), status_code=500)


@serie_bp.route("/user-ratings/<int:user_id>/series", methods=["GET"])
def get_user_series_ratings(user_id):
    """
    Get all serie ratings by a user.

    Route: /user-ratings/<int:user_id>/series
    Method: GET

    Returns:
        list: A list of dictionaries containing the details of the rated series,
              the rating given, and the date and time of the rating.

    Status Codes:
        200: Successfully retrieved the ratings.
        404: User not found.
    """

    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        raise APIException("User not found", status_code=404)

    try:
        # Retrieve all serie ratings by the user
        ratings = (
            SerieUserRating.query.filter_by(user_id=user_id)
            .order_by(SerieUserRating.date_rated.desc())
            .all()
        )

        # Serialize the ratings and series
        rated_series = [
            {
                "serie": rating.serie.serialize(),
                "rating": rating.rating,
                "date_rated": rating.date_rated,
            }
            for rating in ratings
        ]

        return jsonify(rated_series), 200

    except SQLAlchemyError as e:
        raise APIException("Database error: " + str(e), status_code=500)


def combine_features(row):
    try:
        return " ".join(
            str(row[col]).lower()
            for col in ["title", "director", "cast", "genres", "listed_in"]
            if not pd.isnull(row[col])
        )
    except Exception as e:
        print(f"Error combining features for row: {row.name}, error: {e}")
        return ""


@serie_bp.route("/recommend-series", methods=["POST"])
def recommend_series():
    """
    Recommend series based on user's favorite genres, age, and ratings.

    Route: /recommend-series
    Method: POST

    JSON Parameters:
        user_id (int): The ID of the user. Required.

    Returns:
        dict: A dictionary containing lists of recommended series by genre.

    Status Codes:
        200: Successfully retrieved the recommendations.
        400: Missing or invalid parameters.
        404: User not found.
        500: Internal server error.
    """
    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["user_id"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    user_id = body["user_id"]

    # Retrieve user info
    user = User.query.get(user_id)
    if not user:
        raise APIException("User not found", status_code=404)

    user_age = user.age
    user_favorite_genres = user.favorite_genres.split(", ")

    # Retrieve the series rated by the user
    rated_series = SerieUserRating.query.filter_by(user_id=user_id).all()
    rated_serie_ids = {rating.serie_id for rating in rated_series}

    # Categorize user's ratings
    user_loves = [
        rating.serie_id for rating in rated_series if rating.rating == "Me encanta"
    ]
    user_likes = [
        rating.serie_id for rating in rated_series if rating.rating == "Me gusta"
    ]
    user_dislikes = [
        rating.serie_id for rating in rated_series if rating.rating == "No me gusta"
    ]

    # Fetch all series from the database
    series = Serie.query.all()
    series_df = pd.DataFrame([serie.serialize() for serie in series])

    # Combine the features for each serie
    def combine_features(row):
        return " ".join(
            str(row[col]).lower() for col in ["title", "director", "cast", "genres"]
        )

    series_df["combined_features"] = series_df.apply(combine_features, axis=1)

    # Initialize the TF-IDF Vectorizer
    tfidf_vectorizer = TfidfVectorizer(stop_words="english")

    # Fit and transform the combined features
    tfidf_matrix = tfidf_vectorizer.fit_transform(series_df["combined_features"])

    # Calculate the cosine similarity matrix
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    # Define the minimum age required for each rating
    age_restrictions = {
        "TV-Y": 0,
        "TV-Y7": 7,
        "TV-Y7-FV": 7,
        "TV-G": 0,
        "TV-PG": 10,
        "TV-14": 14,
        "TV-MA": 17,
        "G": 0,
        "PG": 10,
        "PG-13": 13,
        "R": 17,
        "NC-17": 18,
        "NR": 18,
        "UR": 18,
        "": 18,
    }

    # Function to get recommendations
    def get_recommendations(
        user_loves, user_likes, user_dislikes, cosine_sim=cosine_sim
    ):
        loved_serie_indices = series_df[series_df["id"].isin(user_loves)].index.tolist()
        liked_serie_indices = series_df[series_df["id"].isin(user_likes)].index.tolist()
        disliked_serie_indices = series_df[
            series_df["id"].isin(user_dislikes)
        ].index.tolist()

        sim_scores_loves = np.sum(cosine_sim[loved_serie_indices], axis=0)
        sim_scores_likes = np.sum(cosine_sim[liked_serie_indices], axis=0)
        sim_scores_dislikes = np.sum(cosine_sim[disliked_serie_indices], axis=0)

        combined_sim_scores = (
            sim_scores_loves * 2 + sim_scores_likes - sim_scores_dislikes
        )

        sim_scores = list(enumerate(combined_sim_scores))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        all_liked_indices = set(
            loved_serie_indices + liked_serie_indices + disliked_serie_indices
        )
        sim_scores = [
            score for score in sim_scores if score[0] not in all_liked_indices
        ]

        serie_indices = [i[0] for i in sim_scores]

        return series_df.iloc[serie_indices]

    recommended_series = get_recommendations(user_loves, user_likes, user_dislikes)

    # Filter by age restrictions and genres
    def filter_series(serie):
        serie_age_rating = age_restrictions.get(serie["age_rating"], 18)
        if serie_age_rating > user_age or serie["id"] in rated_serie_ids:
            return False
        for genre in user_favorite_genres:
            if genre.lower() in serie["genres"].lower():
                return True
        return False

    filtered_series = recommended_series[
        recommended_series.apply(filter_series, axis=1)
    ]

    # Organize series by genre, ensuring no duplicates
    series_by_genre = {genre: [] for genre in user_favorite_genres}
    seen_series = set()

    for _, serie in filtered_series.iterrows():
        for genre in user_favorite_genres:
            if (
                genre.lower() in serie["genres"].lower()
                and serie["id"] not in seen_series
            ):
                series_by_genre[genre].append(serie.to_dict())
                seen_series.add(serie["id"])
                if len(series_by_genre[genre]) == 30:
                    break

    return jsonify(series_by_genre)


@serie_bp.route("last-rated-serie/<int:user_id>", methods=["GET"])
def get_last_rated_serie(user_id):
    """
    Get the last serie rated by a user.

    Route: /last-rated-serie/<int:user_id>
    Method: GET

    Returns:
        dict: A dictionary containing the details of the last rated serie. First check if the rating is "Me encanta",
              then "Me gusta", if not, return an empty dictionary.

    Status Codes:
        200: Successfully retrieved the last rated serie.
        404: User not found.
    """
    
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        raise APIException("User not found", status_code=404)

    # Retrieve the last serie rated "Me encanta" by the user
    last_loved_serie = SerieUserRating.query.filter_by(user_id=user_id, rating="Me encanta").order_by(SerieUserRating.date_rated.desc()).first()
    
    if last_loved_serie:
        serie = Serie.query.get(last_loved_serie.serie_id)
        return jsonify(serie.serialize())

    # If no "Me encanta" serie found, retrieve the last serie rated "Me gusta" by the user
    last_liked_serie = SerieUserRating.query.filter_by(user_id=user_id, rating="Me gusta").order_by(SerieUserRating.date_rated.desc()).first()
    
    if last_liked_serie:
        serie = Serie.query.get(last_liked_serie.serie_id)
        return jsonify(serie.serialize())
    
    # If no "Me encanta" or "Me gusta" serie found, return an empty dictionary
    return jsonify({})
