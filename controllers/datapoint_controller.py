from datetime import datetime, time

from mongoengine import Q

import models
import controllers.device_controller as device_controller

"""
This file helps our blueprints get the data 
from the database using our models.
"""


def create_datapoint(unit_of_measurement, value, user_id, device_id):
    from controllers.device_controller import get_device_by_id
    device = get_device_by_id(device_id)
    device.datapoints.append(models.DataPoint(unit_of_measurement=unit_of_measurement, value=value))
    device.save()
    return True


def get_datapoint_by_timestamp(device_id, timestamp):
    try:
        device = device_controller.get_device_by_id(device_id=device_id)
        for datapoint in device.datapoints:
            if datapoint.timestamp.strftime("%Y-%m-%d, %H:%M:%S") == timestamp:
                return datapoint
    except BaseException:  # In case we can't find datapoint by timestamp
        return None


def update_datapoint(device_id, timestamp, new_unit_of_measurement, new_value):
    device = device_controller.get_device_by_id(device_id=device_id)
    datapoint_index = -1
    for datapoint in device.datapoints:
        datapoint_index += 1
        if datapoint.timestamp.strftime("%Y-%m-%d, %H:%M:%S") == timestamp:
            break
    new_values = {}

    if datapoint_index == -1:
        return False
    if new_unit_of_measurement is not None:
        new_values[f'set__datapoints__{datapoint_index}__unit_of_measurement'] = new_unit_of_measurement
    if new_value is not None:
        new_values[f'set__datapoints__{datapoint_index}__value'] = new_value
    try:
        device.update(**new_values)
    except BaseException:
        return False
    return True


def delete_datapoint(device_id, timestamp):
    device = device_controller.get_device_by_id(device_id=device_id)
    datapoint = get_datapoint_by_timestamp(device_id=device_id, timestamp=timestamp)
    if datapoint is None:
        return False
    device.datapoints.remove(datapoint)
    device.save()
    return True
