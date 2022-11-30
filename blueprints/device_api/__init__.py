import os

import controllers.device_controller as device_controller
import controllers.user_controller as user_controller
from flask import Blueprint, Response, request
import jwt
import config
import json

bp_device_api = Blueprint('bp_device_api', __name__)


@bp_device_api.before_request
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
    user = user_controller.get_user_by_id(decoded_token['id'])
    if user is None:
        Response("Couldn't find user. Has it been Deleted?", 404, content_type='application/json')


@bp_device_api.post('users/<user_id>/devices')
def create_device(user_id):
    if request.is_json:
        sensor_type = request.json.get("sensor_type")
        if sensor_type is not None:
            device_controller.create_device(sensor_type, user_id=user_id)
            return Response("Device has been created!", 200, content_type='application/json')
        return Response('Missing Json Fields', 400, content_type='application/json')
    return Response('Invalid Json', 400, content_type='application/json')


@bp_device_api.get('users/<user_id>/devices')
def get_user_devices(user_id):
    devices = device_controller.get_devices(user_id=user_id)
    if devices is not None:
        device_list = []
        for device in devices:
            device_dict = {
                "device_id": device.id
            }
            device_list.append(device_dict)
        return Response(json.dumps(device_list), 200, content_type='application/json')
    return Response("Couldn't find any devices. Have they been deleted?", 404, content_type='application/json')


@bp_device_api.get('users/<user_id>/devices/<device_id>')
def get_device(user_id, device_id):
    device = device_controller.get_device_by_id(device_id=device_id)
    if device is not None:
        device_dict = {
            "device_id": device['device_id'],
            "sensor_type": device['sensor_type']
        }
        return Response(json.dumps(device_dict), 200, content_type='application/json')
    return Response("Couldn't find device. Has it been deleted?", 404, content_type='application/json')


@bp_device_api.put('users/<user_id>/devices/<device_id>')
def update_device(user_id, device_id):
    if request.is_json:
        new_sensor_type = request.json.get("sensor_type")
        if new_sensor_type is None:
            return Response('No update parameters were supplied: email, password, name', 400)
        if device_controller.update_device(new_sensor_type=new_sensor_type, device_id=device_id) is None:
            return Response("Couldn't find device. Has it been Deleted?", 404, content_type='application/json')
        return Response("Device has been updated", 200, content_type='application/json')
    return Response("Request is not json", 400)


@bp_device_api.delete('users/<user_id>/devices/<device_id>')
def delete_device(user_id, device_id):
    if device_controller.delete_device(device_id=device_id):
        return Response("Device has been deleted.", 200, content_type='application/json')
    return Response('Could not find user. Has it already been deleted?', 404, content_type='application/json')
