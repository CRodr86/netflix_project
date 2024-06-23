from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

from api.utils import APIException
from api.models import User

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login a user.

    Route: /login
    Method: POST

    JSON Parameters:
        username (str): The username of the user. Required.
        password (str): The password of the user. Required.

    Returns:
        dict: A dictionary containing:
            - msg (str): A message indicating the success of the operation.
            - user (dict): A dictionary containing the details of the logged in user.
            - token (str): A JWT token to be used for authenticating future requests.

    Status Codes:
        200: Successfully logged in.
        400: Missing or invalid parameters.
        401: Invalid credentials.
    """
    body = request.get_json()

    if not body:
        raise APIException("No input data provided", status_code=400)

    required_fields = ["username", "password"]
    if not all(body.get(field) for field in required_fields):
        missing_fields = [field for field in required_fields if not body.get(field)]
        raise APIException(
            f'You need to specify the following fields: {", ".join(missing_fields)}',
            status_code=400,
        )
    user = User.query.filter_by(username=body["username"]).first()
    if not user:
        raise APIException("Invalid credentials", status_code=401)
    if not check_password_hash(user.password, body["password"]):
        raise APIException("Invalid credentials", status_code=401)
    token = create_access_token(identity=user.id)
    return (
        jsonify(
            {"msg": "Logged in successfully", "user": user.serialize(), "token": token}
        ),
        200,
    )
