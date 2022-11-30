import models
import uuid

"""
This file helps our blueprints get the data 
from the database using our models.
"""


def create_device(sensor_type, user_id):
    from controllers.user_controller import get_user_by_id
    user = get_user_by_id(user_id)
    device = models.Device()
    device.id = str(uuid.uuid4())
    device.sensor_type = sensor_type
    user.devices.append(device)
    user.save()
    device.save()
    return True


def get_device_by_id(device_id):
    try:
        device = models.Device.objects.get(device_id=device_id)
        return device
    except BaseException:  # In case we can't find device by id
        return None


def get_devices(user_id):
    try:
        from controllers import user_controller
        user = user_controller.get_user_by_id(id=user_id)
        return user.devices
    except BaseException:  # In case we can't find devices by user_id
        return None


def update_device(device_id, new_sensor_type):
    device = get_device_by_id(device_id)

    new_values = {}

    if device is None:
        return None
    if new_sensor_type is not None:
        new_values['sensor_type'] = new_sensor_type
    try:
        device.update(**new_values)
    except BaseException:
        return False
    return True


def delete_device(device_id):
    device = get_device_by_id(device_id)
    if device is None:
        return False
    device.delete()
    return True
