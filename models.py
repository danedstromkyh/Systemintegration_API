from datetime import datetime, timezone
from app import db


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
