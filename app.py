import os
import random

import MongoEngine as MongoEngine
import pymongo
from flask import Flask, render_template, jsonify
from flask.cli import load_dotenv
from flask_login import LoginManager
from flask_mqtt import Mqtt


db = MongoEngine()


def create_app():
    """
    Initializes our API
    :return: app object
    """
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.environ.get('APP_SECRET_KEY')

    app.config['MONGODB_SETTINGS'] = {
        'host': os.environ.get('M_URI')
    }
    db.init_app(app)

    # Ställ in MQTT-klienten
    app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
    app.config['MQTT_BROKER_PORT'] = 1883
    app.config['MQTT_USERNAME'] = ''
    app.config['MQTT_PASSWORD'] = ''
    app.config['MQTT_KEEPALIVE'] = 5  # Sekunder
    app.config['MQTT_TLS_ENABLED'] = False

    topic = '/kyh/example_mqtt_flask'

    mqtt_client = Mqtt(app)

    # Hantera MQTT-connect
    @mqtt_client.on_connect()
    def handle_connect(client, userdata, flags, rc):
        if rc == 0:
            print('Connected successfully')
            mqtt_client.subscribe(topic)
        else:
            print('Something went wrong:', rc)

    # On-message-funktion
    @mqtt_client.on_message()
    def handle_mqtt_message(client, userdata, message):
        m_topic = message.topic
        m_payload = message.payload.decode('utf-8')
        print(f'Received message on topic: {m_topic}: {m_payload}')

        # Spara m_payload till en textfil
        # w = Skriv över hela innehållet varje gång filen öppnas
        # r = Får bara läsa från filer
        # a = Append, lägg till ny text på slutet av filen
        with open(file='storage.txt', mode='w', encoding='utf-8') as file:
            file.write(m_payload)

    # Gör en route som skriver ut ett sparat meddelande
    @app.route('/get/')
    def get_message():
        with open(file='storage.txt', mode='r', encoding='utf-8') as file:
            data = file.read()
        return jsonify({'text': data}), 200

    """ Exempel på en annan route:
    @app.route('/temperature/<room>')
    def get_temperature(room):
        pass
    """

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        import models
        user = models.User.objects.get(id=user_id)
        return user

    from blueprints.open_api import bp_open_api
    app.register_blueprint(bp_open_api, url_prefix='/api/v1.0/')
    from blueprints.user_api import bp_user_api
    app.register_blueprint(bp_user_api, url_prefix='/api/v1.0/')
    from blueprints.device_api import bp_device_api
    app.register_blueprint(bp_device_api, url_prefix='/api/v1.0/')
    from blueprints.datapoint_api import bp_datapoint_api
    app.register_blueprint(bp_datapoint_api, url_prefix='/api/v1.0/')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
