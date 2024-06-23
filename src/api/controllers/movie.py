from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from api.utils import APIException
from api.models import Movie
from api import db

movie_bp = Blueprint("movie_bp", __name__)


@movie_bp.route("/movies", methods=["POST"])
def get_movies_by_genre():
    """
    Get movies by genre.

    Route: /movies
    Method: POST

    JSON Parameters:
        genre (list): A list of movie genres. Required.

    Returns:
        list: A list of dictionaries containing the details of the movies.

    Status Codes:
        200: Successfully retrieved the movies.
        400: Missing or invalid parameters.
    """
    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["genre"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    genres = body["genre"]

    if not isinstance(genres, list) or not genres:
        raise APIException(
            "The 'genre' field must be a non-empty list", status_code=400
        )

    # Create the filter conditions
    genre_filters = [Movie.genres.contains(genre) for genre in genres]

    # Query the movies
    movies = (
        Movie.query.filter(or_(*genre_filters))
        .filter(Movie.is_adult == 0, Movie.popularity != None)
        .order_by(Movie.popularity.desc())
        .limit(90)
        .all()
    )

    return jsonify([movie.serialize() for movie in movies])
