import os
from urllib.parse import quote_plus
from flask_mongoengine import MongoEngine
from flask_pymongo import pymongo
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_mqtt import Mqtt

app = Flask(__name__)
#db = MongoEngine()



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

def create_app(app):
    """
    Initializes our API
    :return: app object
    """
    load_dotenv()
    app.secret_key = os.environ.get('APP_SECRET_KEY')
    #mongo_uri = "mongodb+srv://edvin:" + urllib.parse.quote("Xih*hLy@gWqc2&9dmCCDTbdBumJdcWz") + "@kyhdb.tmgj0.mongodb.net/?retryWrites=true&w=majority"
    #app.config['MONGODB_SETTINGS'] = {
    #    'host': mongo_uri }
    #db.init_app(app)

    username = quote_plus('edvin')

    password = quote_plus('Xih*hLy@gWqc2&9dmCCDTbdBumJdcWz')


    uri = 'mongodb+srv://edvin:' + password + '@kyhdb.tmgj0.mongodb.net/?retryWrites=true&w=majority'

    client = pymongo.MongoClient(uri)

    #CONNECTION_STRING = "mongodb+srv://edvin:" + urllib.parse.quote("Xih*hLy@gWqc2&9dmCCDTbdBumJdcWz") + "@kyhdb.tmgj0.mongodb.net/?retryWrites=true&w=majority"
    #client = pymongo.MongoClient(CONNECTION_STRING)
    db = client.get_database('flask_mongodb_atlas')
    user_collection = pymongo.collection.Collection(db, 'user_collection')



    @app.route("/test/")
    def test():
        db.db.collection.insert_one({"name": "John"})
        return "Connected to the data base!"

    # Gör en route som skriver ut ett sparat meddelande
    @app.route('/get/')
    def get_message():
        with open(file='storage.txt', mode='r', encoding='utf-8') as file:
            data = file.read()
        return jsonify({'text': data}), 200

    return app


if __name__ == "__main__":
    app = create_app(app=app)
    app.run(debug=True)
