import os

import controllers.device_controller as device_controller
import controllers.user_controller as user_controller
import controllers.datapoint_controller as datapoint_controller
from flask import Blueprint, Response, request
import jwt
import config
import json

bp_datapoint_api = Blueprint('bp_datapoint_api', __name__)


@bp_datapoint_api.before_request
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


@bp_datapoint_api.post('users/<user_id>/devices/<device_id>/data')
def create_datapoint(user_id, device_id):
    if request.is_json:
        unit_of_measurement = request.json.get("unit_of_measurement")
        value = request.json.get("value")
        if unit_of_measurement and value is not None:
            datapoint_controller.create_datapoint(unit_of_measurement, value, user_id, device_id)
            return Response("Datapoint has been created!", 200, content_type='application/json')
        return Response('Missing Json Fields', 400, content_type='application/json')
    return Response('Invalid Json', 400, content_type='application/json')


@bp_datapoint_api.get('users/<user_id>/devices/<device_id>/data')
def get_datapoints_by_device(user_id, device_id):
    device = device_controller.get_device_by_id(device_id=device_id)
    if device is not None:
        if device.datapoints is not None:
            datapoint_list = []
            for datapoint in device.datapoints:
                datapoint_dict = {}
                datapoint_dict['timestamp'] = datapoint.timestamp.strftime("%Y/%m/%d, %H:%M:%S")
                datapoint_dict['unit_of_measurement'] = datapoint.unit_of_measurement
                datapoint_dict['value'] = datapoint.value
                datapoint_list.append(datapoint_dict)
            return Response(json.dumps(datapoint_list), 200, content_type='application/json')
        return Response("Couldn't find any device datapoints. Have they been deleted?", 404,
                        content_type='application/json')
    return Response("Couldn't find device. Has it been deleted?", 404, content_type='application/json')


@bp_datapoint_api.get('users/<user_id>/devices/<device_id>/data/timestamp')
def get_specific_datapoint(user_id, device_id):
    """
    In the body of request a json keyworded timestamp should be sent as a string in the following datetime.datetime
    format: "%Y/%m/%d, %H:%M:%S"
    :param user_id: Should be sent in the format received from function get_user without quotationmarks
    :param device_id: Should be sent in the format received from function get_device without quotationmarks
    :return: flask.Response containing representation of datapoint object in json format.
    """
    if request.is_json:
        data = request.json
        datapoint = datapoint_controller.get_datapoint_by_timestamp(device_id=device_id, timestamp=data['timestamp'])
        if datapoint is not None:
            datapoint_dict = {
            'timestamp': datapoint.timestamp.strftime("%Y-%m-%d, %H:%M:%S"),
            'unit_of_measurement': datapoint.unit_of_measurement,
            'value': datapoint.value
            }
            return Response(json.dumps(datapoint_dict), 200, content_type='application/json')
        return Response("Couldn't find any device datapoints. Have they been deleted?", 404,
                        content_type='application/json')
    return Response('Invalid Json', 400, content_type='application/json')


@bp_datapoint_api.put('users/<user_id>/devices/<device_id>/data/timestamp')
def update_datapoint(user_id, device_id):
    if request.is_json:
        unit_of_measurement = request.json.get('unit_of_measurement')
        value = request.json.get('value')
        timestamp = request.json.get('timestamp')
        if unit_of_measurement and value is None:
            return Response('No update parameters were supplied: value or unit_of_measurement', 400)
        if datapoint_controller.update_datapoint(device_id=device_id, timestamp=timestamp,
                                                 new_unit_of_measurement=unit_of_measurement, new_value=value) is None:
            return Response("Couldn't find device datapoint. Has it been Deleted?", 404,
                            content_type='application/json')
        return Response("Device has been updated", 200, content_type='application/json')
    return Response("Request is not json", 400, content_type='application/json')


@bp_datapoint_api.delete('users/<user_id>/devices/<device_id>/data/timestamp')
def delete_datapoint(user_id, device_id):
    if request.is_json:
        timestamp = request.json.get('timestamp')
        if timestamp is None:
            return Response(
                "Couldn't find datapoint due to no timestamp being provided. Supply timestamp string in the following datetime.datetime format: %Y/%m/%d, %H:%M:%S",
                404, content_type='application/json')
        if datapoint_controller.delete_datapoint(device_id=device_id, timestamp=timestamp):
            return Response("Datapoint has been deleted!", 200, content_type='application/json')
    return Response("Request is not json", 400, content_type='application/json')
