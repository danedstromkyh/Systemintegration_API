from datetime import datetime, timezone

from app import db
from flask_bcrypt import generate_password_hash, check_password_hash


class DataPoint(db.EmbeddedDocument):
    timestamp = db.DateField(default=datetime.now(timezone.utc))
    unit_of_measurement = db.StringField(required=True)
    value = db.StringField(required=True)

    def get_timestamp(self):
        return self.timestamp


class Device(db.Document):
    device_id = db.StringField(primary_key=True)
    sensor_type = db.StringField(required=True)
    datapoints = db.EmbeddedDocumentListField(DataPoint)

    def get_device_id(self):
        return self.device_id


class User(db.Document):
    id = db.StringField(primary_key=True)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True, min_length=6)
    name = db.StringField(required=True)
    devices = db.ListField(db.ReferenceField(Device, reverse_delete_rule="CASCADE"))

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def hash_password(self):
        self.password = generate_password_hash(self.password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password, password)
