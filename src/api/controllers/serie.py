from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from api.utils import APIException
from api.models import Serie
from api import db

serie_bp = Blueprint("serie_bp", __name__)


@serie_bp.route("/series", methods=["POST"])
def get_series_by_genre():
    """
    Get series by genre.

    Route: /series
    Method: POST

    JSON Parameters:
        genre (list): A list of tv series genres. Required.

    Returns:
        list: A list of dictionaries containing the details of the series.

    Status Codes:
        200: Successfully retrieved the series.
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
    genre_filters = [Serie.genres.contains(genre) for genre in genres]

    # Query the movies
    series = (
        Serie.query.filter(or_(*genre_filters))
        .filter(Serie.is_adult == 0, Serie.popularity != None)
        .order_by(Serie.popularity.desc())
        .limit(60)
        .all()
    )

    return jsonify([serie.serialize() for serie in series])
