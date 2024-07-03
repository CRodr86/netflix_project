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
from api.models import Movie, MovieUserRating, User
from api import db

movie_bp = Blueprint("movie_bp", __name__)


@movie_bp.route("/first-movies", methods=["POST"])
def get_first_movies_by_genre():
    """
    Get movies by genre.

    Route: /first-movies
    Method: POST

    JSON Parameters:
        genre (list): A list of movie genres. Required.
        user_id (int): The ID of the user. Required.

    Returns:
        list: A list of dictionaries containing the details of the movies.

    Status Codes:
        200: Successfully retrieved the movies.
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
    genre_filters = [Movie.genres.contains(genre) for genre in genres]

    # Query the movies
    movies = (
        Movie.query.filter(or_(*genre_filters))
        .filter(Movie.popularity != None)
        .order_by(Movie.popularity.desc())
        .limit(90)
        .all()
    )

    # Filter movies based on user's age
    filtered_movies = []
    for movie in movies:
        movie_age_rating = age_restrictions.get(movie.age_rating, 18)
        if movie_age_rating <= user_age:
            filtered_movies.append(movie.serialize())

    return jsonify(filtered_movies)


@movie_bp.route("/movies", methods=["POST"])
def get_movies_by_genre():
    """
    Get movies by genre.

    Route: /movies
    Method: POST

    JSON Parameters:
        genre (list): A list of movie genres. Required.
        user_id (int): The ID of the user. Required.

    Returns:
        dict: A dictionary containing lists of movies by genre.

    Status Codes:
        200: Successfully retrieved the movies.
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

    all_movies = []
    seen_movies = set()

    # Retrieve user info
    user = User.query.get(user_id)
    if not user:
        raise APIException("User not found", status_code=404)

    user_age = user.age

    # Retrieve the movies rated by the user
    rated_movies = MovieUserRating.query.filter_by(user_id=user_id).all()
    rated_movie_ids = {rating.movie_id for rating in rated_movies}

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
            genre_movies = (
                Movie.query.filter(
                    Movie.genres.contains(genre),
                    Movie.popularity != None,
                    ~Movie.id.in_(seen_movies),
                    ~Movie.id.in_(rated_movie_ids),
                )
                .order_by(Movie.popularity.desc())
                .limit(30)
                .all()
            )
            for movie in genre_movies:
                movie_age_rating = age_restrictions.get(movie.age_rating, 18)
                if movie_age_rating <= user_age and movie.id not in seen_movies:
                    seen_movies.add(movie.id)
                    all_movies.append({"genre": genre, "movie": movie})

        # Organize movies by genre
        movies_by_genre = {genre: [] for genre in genres}
        for item in all_movies:
            movies_by_genre[item["genre"]].append(item["movie"].serialize())

        return jsonify(movies_by_genre)
    except SQLAlchemyError as e:
        raise APIException("Database error: " + str(e), status_code=500)


@movie_bp.route("/movie/<int:movie_id>/<int:user_id>", methods=["GET"])
def get_movie_by_id(movie_id, user_id):
    """
    Get a movie by its ID.

    Route: /movie/<int:movie_id>/<int:user_id>
    Method: GET

    Returns:
        dict: A dictionary containing the details of the movie. If the user has rated the movie,
                the dictionary will also contain the rating and the date and time of the rating.

    Status Codes:
        200: Successfully retrieved the movie.
        404: Movie not found.
    """
    # Check if the movie exists
    movie = Movie.query.get(movie_id)
    if not movie:
        raise APIException("Movie not found", status_code=404)

    # Check if the user has rated the movie
    rating = MovieUserRating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if rating:
        movie_data = {
            "movie": movie.serialize(),
            "rating": rating.rating,
            "date_rated": rating.date_rated,
        }
    else:
        movie_data = {"movie": movie.serialize()}

    return jsonify(movie_data)


@movie_bp.route("/rate-movie", methods=["POST"])
def rate_movie():
    """
    Rate a movie.

    Route: /rate-movie
    Method: POST

    JSON Parameters:
        movie_id (int): The ID of the movie to be rated. Required.
        user_id (int): The ID of the user rating the movie. Required.
        rating (str): The rating given by the user. Required.

    Returns:
        dict: A message indicating success or failure.

    Status Codes:
        200: Successfully rated the movie.
        400: Missing or invalid parameters.
        404: Movie or user not found.
        500: Internal server error.
    """
    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["movie_id", "user_id"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    movie_id = body["movie_id"]
    user_id = body["user_id"]
    rating = body.get("rating", None)

    if rating is None:
        raise APIException("The 'rating' field is required", status_code=400)

    try:
        # Check if the movie exists
        movie = Movie.query.get(movie_id)
        if not movie:
            raise APIException("Movie not found", status_code=404)

        # Check if the user exists
        user = User.query.get(user_id)
        if not user:
            raise APIException("User not found", status_code=404)

        # Check if the user has already rated this movie
        existing_rating = MovieUserRating.query.filter_by(
            user_id=user_id, movie_id=movie_id
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
                new_rating = MovieUserRating(
                    user_id=user_id,
                    movie_id=movie_id,
                    rating=rating,
                    date_rated=datetime.datetime.now(),
                )
                db.session.add(new_rating)

            db.session.commit()

            return jsonify({"message": "Successfully rated the movie"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        raise APIException("Database error: " + str(e), status_code=500)


@movie_bp.route("/user-ratings/<int:user_id>/movies", methods=["GET"])
def get_user_movies_ratings(user_id):
    """
    Get all movie ratings by a user.

    Route: /user-ratings/<int:user_id>/movies
    Method: GET

    Returns:
        list: A list of dictionaries containing the details of the rated movies,
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
        # Retrieve all movie ratings by the user
        ratings = (
            MovieUserRating.query.filter_by(user_id=user_id)
            .order_by(MovieUserRating.date_rated.desc())
            .all()
        )

        # Serialize the ratings and movies
        rated_movies = [
            {
                "movie": rating.movie.serialize(),
                "rating": rating.rating,
                "date_rated": rating.date_rated,
            }
            for rating in ratings
        ]

        return jsonify(rated_movies), 200

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


@movie_bp.route("/recommend-movies", methods=["POST"])
def recommend_movies():
    """
    Recommend movies based on user's favorite genres, age, and ratings.

    Route: /recommend-movies
    Method: POST

    JSON Parameters:
        user_id (int): The ID of the user. Required.

    Returns:
        dict: A dictionary containing lists of recommended movies by genre.

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

    # Retrieve the movies rated by the user
    rated_movies = MovieUserRating.query.filter_by(user_id=user_id).all()
    rated_movie_ids = {rating.movie_id for rating in rated_movies}

    # Categorize user's ratings
    user_loves = [
        rating.movie_id for rating in rated_movies if rating.rating == "Me encanta"
    ]
    user_likes = [
        rating.movie_id for rating in rated_movies if rating.rating == "Me gusta"
    ]
    user_dislikes = [
        rating.movie_id for rating in rated_movies if rating.rating == "No me gusta"
    ]

    # Fetch all movies from the database
    movies = Movie.query.all()
    movies_df = pd.DataFrame([movie.serialize() for movie in movies])

    # Combine the features for each movie
    def combine_features(row):
        return " ".join(
            str(row[col]).lower() for col in ["title", "director", "cast", "genres"]
        )

    movies_df["combined_features"] = movies_df.apply(combine_features, axis=1)

    # Initialize the TF-IDF Vectorizer
    tfidf_vectorizer = TfidfVectorizer(stop_words="english")

    # Fit and transform the combined features
    tfidf_matrix = tfidf_vectorizer.fit_transform(movies_df["combined_features"])

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
        loved_movie_indices = movies_df[movies_df["id"].isin(user_loves)].index.tolist()
        liked_movie_indices = movies_df[movies_df["id"].isin(user_likes)].index.tolist()
        disliked_movie_indices = movies_df[
            movies_df["id"].isin(user_dislikes)
        ].index.tolist()

        sim_scores_loves = np.sum(cosine_sim[loved_movie_indices], axis=0)
        sim_scores_likes = np.sum(cosine_sim[liked_movie_indices], axis=0)
        sim_scores_dislikes = np.sum(cosine_sim[disliked_movie_indices], axis=0)

        combined_sim_scores = (
            sim_scores_loves * 2 + sim_scores_likes - sim_scores_dislikes
        )

        sim_scores = list(enumerate(combined_sim_scores))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        all_liked_indices = set(
            loved_movie_indices + liked_movie_indices + disliked_movie_indices
        )
        sim_scores = [
            score for score in sim_scores if score[0] not in all_liked_indices
        ]

        movie_indices = [i[0] for i in sim_scores]

        return movies_df.iloc[movie_indices]

    recommended_movies = get_recommendations(user_loves, user_likes, user_dislikes)

    # Filter by age restrictions and genres
    def filter_movies(movie):
        movie_age_rating = age_restrictions.get(movie["age_rating"], 18)
        if movie_age_rating > user_age or movie["id"] in rated_movie_ids:
            return False
        for genre in user_favorite_genres:
            if genre.lower() in movie["genres"].lower():
                return True
        return False

    filtered_movies = recommended_movies[
        recommended_movies.apply(filter_movies, axis=1)
    ]

    # Organize movies by genre, ensuring no duplicates
    movies_by_genre = {genre: [] for genre in user_favorite_genres}
    seen_movies = set()

    for _, movie in filtered_movies.iterrows():
        for genre in user_favorite_genres:
            if (
                genre.lower() in movie["genres"].lower()
                and movie["id"] not in seen_movies
            ):
                movies_by_genre[genre].append(movie.to_dict())
                seen_movies.add(movie["id"])
                if len(movies_by_genre[genre]) == 30:
                    break

    return jsonify(movies_by_genre)
