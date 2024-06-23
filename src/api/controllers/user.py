from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash

from api.utils import APIException
from api.models import User, MovieUserRating, SerieUserRating
from api import db

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/register", methods=["POST"])
def register_user():
    """
    Register a new user.

    Route: /user
    Method: POST

    JSON Parameters:
        username (str): The username of the user. Required.
        email (str): The email of the user. Required.
        password (str): The password of the user. Required.
        age (int): The age of the user. Required.

    Returns:
        dict: A dictionary containing:
            - msg (str): A message indicating the success of the operation.
            - user (dict): A dictionary containing the details of the newly created user.

    Status Codes:
        201: Successfully created a new user.
        400: Missing or invalid parameters.
        409: User with the given username already exists.

    """

    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["username", "email", "password", "age"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )
    user = User.query.filter_by(username=body["username"]).first()
    if user:
        raise APIException(
            "User with the given username already exists", status_code=409
        )
    user = User.query.filter_by(email=body["email"]).first()
    if user:
        raise APIException("User with the given email already exists", status_code=409)

    new_user = User(
        username=body["username"],
        email=body["email"],
        password=generate_password_hash(body["password"]),
        age=body["age"],
    )
    db.session.add(new_user)
    db.session.commit()

    return (
        jsonify({"msg": "User registered successfully", "user": new_user.serialize()}),
        201,
    )


@user_bp.route("/first-access", methods=["POST"])
def store_first_access_data():
    """
    Store the first access data of a user.

    Route: /user/first-access
    Method: POST

    JSON Parameters:
        user_id (int): The ID of the user. Required.
        genres: (str): A string with the genres the user is interested in. Required.
        movies (list): A list containing the id's of the movies. Required.
        series (list): A list containing the id's of the series. Required.

    Returns:
        dict: A dictionary containing:
            - msg (str): A message indicating the success of the operation.
            - user (dict): A dictionary containing the details of the user.

    Status Codes:
        201: Successfully stored the first access data.
        400: Missing or invalid parameters.
        404: User not found.
    """

    body = request.get_json()

    if not body:
        raise APIException("Missing JSON body", status_code=400)

    required_fields = ["user_id", "genres", "movies", "series"]
    missing_fields = [
        field for field in required_fields if field not in body or body[field] is None
    ]

    if missing_fields:
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )

    user = User.query.get(body["user_id"])
    if not user:
        raise APIException("User not found", status_code=404)

    genres = body["genres"]
    movies = body["movies"]
    series = body["series"]

    user.favorite_genres = genres

    for movie_id in movies:
        movie_rating = MovieUserRating(
            user_id=user.id,
            movie_id=movie_id,
            rating="Me gusta",
        )
        db.session.add(movie_rating)

    for series_id in series:
        series_rating = SerieUserRating(
            user_id=user.id,
            serie_id=series_id,
            rating="Me gusta",
        )
        db.session.add(series_rating)

    user.is_new_user = False
    db.session.commit()

    return (
        jsonify(
            {
                "msg": "First access data stored successfully",
                "user": user.serialize(),
            }
        ),
        201,
    )
