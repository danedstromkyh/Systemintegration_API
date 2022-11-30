import json
import os

import flask_login
import jwt
from flask import Blueprint, request, Response, jsonify
from flask_login import login_required
import config
import controllers.user_controller

bp_user_api = Blueprint('bp_user', __name__)


@bp_user_api.before_request
def check_token():
    #Gets callers IP - Could be used to log api-calls later.
    #caller_address = request.remote_addr

    token = None
    if 'x-api-key' not in request.headers:
        return Response('Invalid header. key should be: x-api-key', 400, content_type='application/json')

    token = request.headers.get('x-api-key')
    try:
        decoded_token = jwt.decode(token, os.environ.get('JSON_SECRET_KEY'), algorithms="HS256")
    except BaseException:
        return Response('Invalid token. Request a new one at /api/v1.0/login', 401, content_type='application/json')

    # Token is valid and belongs to a user.
    user = controllers.user_controller.get_user_by_id(decoded_token['id'])
    if user is None:
        Response("Couldn't find user. Has it been Deleted?", 404, content_type='application/json')


@bp_user_api.get('users')
def get_user():
    token = request.headers.get('x-api-key')
    decoded_token = jwt.decode(token, config.json_secret_key, algorithms="HS256")
    user = controllers.user_controller.get_user_by_id(decoded_token['id'])
    return Response(json.dumps({'name': user.name, 'email': user.email, 'user_id': user.id}), 200, content_type='application/json')


@bp_user_api.put('/api/v1.0/users')
def update_user():
    if request.is_json:
        json_data = request.get_json()
        new_email = json_data.get('email')
        new_password = json_data.get('password')
        new_name = json_data.get('name')

        if new_email is None and new_password is None and new_name is None:
            return Response('No update parameters were supplied: email, password, name', 400, content_type='application/json')

        token = request.headers.get('x-api-key')
        decoded_token = jwt.decode(token, config.json_secret_key, algorithms="HS256")
        if controllers.user_controller.update_user(decoded_token['id'], new_email, new_password, new_name) is None:
            return Response("Couldn't find user. Has it been Deleted?", 404, content_type='application/json')
        return Response("User has been updated.", 200, content_type='application/json')
    return Response("Request is not json", 400, content_type='application/json')


@bp_user_api.delete('/api/v1.0/users')
def delete_user():
    token = request.headers.get('x-api-key')
    decoded_token = jwt.decode(token, config.json_secret_key, algorithms="HS256")
    if controllers.user_controller.delete_user(decoded_token['id']):
        return Response('User Deleted.', 200, content_type='application/json')
    return Response('Could not find user. Is it already deleted?', 404, content_type='application/json')
