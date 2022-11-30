from flask import Blueprint, Response, request, jsonify
from flask_login import login_user
import jwt
import datetime
import config
from flask import Blueprint, Response, request
import controllers.user_controller

"""
This file handles the url requests to our api
"""

bp_open_api = Blueprint('bp_open_api', __name__)


# TODO Write Open API Functions
# API Key
# Token
# OAuth

@bp_open_api.post('users')
def create_user():
    if request.is_json:
        json_data = request.get_json()
        email = json_data.get('email')
        password = json_data.get('password')
        name = json_data.get('name')

        if email is None or password is None or name is None:
            return Response('Missing Json Fields', 400)

        if controllers.user_controller.create_user(email, password, name):
            return Response('User Created', 200)
        else:
            return Response('Email Already Exists', 400)
    else:
        return Response('Invalid Json', 400)


@bp_open_api.post('login')
def verify_user():
    if request.is_json:
        json_data = request.get_json()
        email = json_data.get('email')
        password = json_data.get('password')
        if email is None or password is None:
            return Response('Invalid Json', 400)

        if controllers.user_controller.verify_login_credentials(email, password):
            user = controllers.user_controller.get_user_by_email(email)
            login_user(user)

            # We'll compare the user id to see if it exists in db and if the token is still valid.
            # If it is: User is authorized.
            token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1440)},
                               config.json_secret_key)

            return jsonify({
                'token': token}, 200)
        else:
            return Response('Email & Password did not match.', 400)

    else:
        return Response('Invalid Json', 400)


@bp_open_api.get('/api/v1.0/user/<name>')
def get_user_by_name():
    return Response('WIP', 503)
    #TODO
