import base64
import io
import os

from PIL import Image
from flask import Flask, jsonify, render_template, send_file, request, json
from flask_mqtt import Mqtt
import datetime
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from dotenv import load_dotenv

load_dotenv()

#DATABASE_FILE = 'data.db'
DATABASE_FILE = os.getenv('DB_PATH')
app = Flask(__name__)
fig, ax = plt.subplots()

# Ställ in MQTT-klienten
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5  # Sekunder
app.config['MQTT_TLS_ENABLED'] = False

topic = '/kyh/temp_sensor'

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
def handle_mqtt_message(client, user_data, message):
    m_topic = message.topic
    m_payload = message.payload.decode('utf-8')
    print(f'Received message on topic: {m_topic}: {m_payload}')

    # Time stamp, sensor data: value
    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    db_conn = user_data['db_conn']
    sql = 'INSERT INTO mqtt_data (payload, created_at) VALUES (?, ?)'
    cursor = db_conn.cursor()
    cursor.execute(sql, (m_payload, date))
    db_conn.commit()
    cursor.close()


def is_request_gateway():
    try:
        data = request
        sender = data.environ['HTTP_WHO_REQUEST']
        if sender == 'apisix':
            return True
    except KeyError:
        return False


def create_app(app):
    db_conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    sql = """
    CREATE TABLE IF NOT EXISTS mqtt_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payload INT NOT NULL,
        created_at TEXT NOT NULL
    )
    """

    cursor = db_conn.cursor()
    cursor.execute(sql)
    cursor.close()

    mqtt_client.client.user_data_set({'db_conn': db_conn})

    # Gör en route som skriver ut ett sparat meddelande
    @app.route('/api/v1/latest_data/')
    def get_latest_data():
        if is_request_gateway():
            return get_all_from_db(graph=False)
        else:
            return jsonify({'status': 'error, forbidden access'}), 403

    @app.route('/api/v1/all_data/')
    def get_all_data():
        if is_request_gateway():
            return get_all_from_db(last_data=False, graph=False)
        else:
            return jsonify({'status': 'error, forbidden access'}), 403

    @app.route('/data/latest')
    def view_latest_data():
        json_data = get_latest_data()
        data = json_data[0].json['all_data']
        return render_template('index.html', data=data)

    @app.route('/data/logs')
    def view_data_log():
        payload_list, date_list = get_all_from_db(last_data=False, graph=True)
        return render_template('log.html', payload_data=payload_list, date_data=date_list)

    @app.route('/plot')
    def plot_data():
        plt.clf()
        payload_list, date_list = get_all_from_db(last_data=False, graph=True)
        payload_list = [json.loads(data)['temp'] for data in payload_list]
        date_list = [date[11:] for date in date_list]

        plt.plot(date_list, payload_list)
        plt.xlabel('Time')
        plt.subplots_adjust(bottom=0.3)
        plt.xticks(date_list)
        plt.xticks(rotation=90)
        plt.ylabel("Temp")

        canvas = FigureCanvas(fig)
        data = io.BytesIO()
        fig.savefig(data)
        plt.show()
        data.seek(0)

        return send_file(data, mimetype='data/png')

    return app


def get_all_from_db(last_data=True, graph=True):
    global DATABASE_FILE
    db_conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM mqtt_data")
    rows = cursor.fetchall()
    if last_data:
        cursor.execute("SELECT * FROM mqtt_data ORDER BY id DESC LIMIT 1")
        data = cursor.fetchone()
    else:
        list_data = []
        for data in rows:
            list_data.append({'data': data})
        data = list_data
        if graph:
            payload_list = []
            db_conn.row_factory = lambda payload_data, row: row[0]
            payload_row = db_conn.execute('SELECT payload FROM mqtt_data').fetchall()
            for payload in payload_row:
                payload_list.append(payload)
            date_list = []
            db_conn.row_factory = lambda date_data, row: row[0]
            date_row = db_conn.execute('SELECT created_at FROM mqtt_data').fetchall()
            for date in date_row:
                date_list.append(date)
            cursor.close()
            return payload_list, date_list
    cursor.close()
    return jsonify({'all_data': data}), 200


if __name__ == "__main__":
    app = create_app(app=app)
    app.run()
