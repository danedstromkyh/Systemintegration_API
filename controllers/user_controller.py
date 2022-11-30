import models
import uuid

"""
This file helps our blueprints get the data 
from the database using our models.
"""

def create_user(email, password, name):
    if get_user_by_email(email) is None:
        user = models.User()
        user.id = str(uuid.uuid4())
        user.email = email
        user.password = password
        user.hash_password()
        user.name = name
        user.save()
        return True
    else:
        return False


def verify_login_credentials(email, password):
    # Gets all users
    #users = models.User.objects()
    # Gets users with specific email.
    # Since it's unique, should always give only one.
    user = get_user_by_email(email)
    if user is None:
        return False
    return user.check_password(password)


def get_user_by_email(email):
    try:
        user = models.User.objects.get(email=email)
        return user
    except BaseException: # In case we can't find user by email
        return None


def get_user_by_id(id):
    try:
        user = models.User.objects.get(id=id)
        return user
    except BaseException:  # In case we can't find user by email
        return None


def update_user(user_id, new_email, new_password, new_name):
    user = get_user_by_id(user_id)

    new_values = {}

    if user is None:
        return None
    if new_email is not None:
        new_values['email'] = new_email
    if new_password is not None:
        new_values['password'] = new_password
    if new_name is not None:
        new_values['name'] = new_name
    try:
        user.update(**new_values)
    except BaseException:
        return False
    return True


def delete_user(id):
    user = get_user_by_id(id)
    if user is None:
        return False
    user.delete()
    return True
