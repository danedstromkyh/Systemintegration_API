from flask import Flask, jsonify, render_template
from flask_mqtt import Mqtt
import datetime

app = Flask(__name__)


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

    # Time stamp, sensor data: value
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(file='storage.txt', mode='a', encoding='utf-8') as file:
        file.write(m_payload + '\t' + date + '\n')




def create_app(app):

    # Gör en route som skriver ut ett sparat meddelande
    @app.route('api/v1/latest_data/')
    def get_latest_data():
        return get_file_data()

    @app.route('api/v1/all_data/')
    def get_all_data():
        return get_file_data(False)

    #@app.route('/home_page')
    #def index():
    #    json_data = get_latest_data()
    #    return render_template(data=json_data)


    def get_file_data(last_data=True):
        with open(file='storage.txt', mode='r', encoding='utf-8') as file:
            if last_data:
                data = file.readlines()[-1]
            else:

                list_data = []
                for data in file.readlines():
                    list_data.append({'data': data})
        return jsonify({'all_data': list_data}), 200

    return app


if __name__ == "__main__":
    app = create_app(app=app)
    app.run(debug=True)
