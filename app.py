import base64
import io
import os
from functools import wraps
from flask import Flask, jsonify, send_file, request, json, redirect, render_template, session, url_for
from flask_mqtt import Mqtt
import datetime
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# DATABASE_FILE = 'data.db'
DATABASE_FILE = os.getenv('DB_PATH')
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY")

# Ställ in MQTT-klienten
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5  # Sekunder
app.config['MQTT_TLS_ENABLED'] = False

topic = '/kyh/temp_sensor'
mqtt_client = Mqtt(app)

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


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


def is_request_gateway(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = request
            sender = data.environ['HTTP_WHO_REQUEST']
            if sender:
                return func(*args, **kwargs)
        except KeyError:
            return jsonify({'error': 'forbidden access'}), 403
    return wrapper



def get_valid_keys():
    with open('api_keys', mode='r', encoding='utf-8') as file:
        list_keys = [key.rstrip() for key in file.readlines()]
        return list_keys


def valid_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if session["user"]:
                return func(*args, **kwargs)
        except KeyError:
            return jsonify({'error': 'invalid or no token'}), 401

    return wrapper


def valid_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request
        system_keys = get_valid_keys()
        user_key = data.headers.environ['HTTP_X_API_KEY']
        for key in system_keys:
            if key == user_key:
                return func(*args, **kwargs)
        return jsonify({'error': 'invalid api key'}), 401

    return wrapper


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

    @app.route("/login")
    def login():
        return oauth.auth0.authorize_redirect(
            redirect_uri=url_for("callback", _external=True)
        )

    @app.route("/callback", methods=["GET", "POST"])
    def callback():
        token = oauth.auth0.authorize_access_token()
        session["user"] = token
        return redirect("/")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(
            "https://" + os.environ.get("AUTH0_DOMAIN")
            + "/v2/logout?"
            + urlencode(
                {
                    "returnTo": url_for("home", _external=True),
                    "client_id": os.environ.get("AUTH0_CLIENT_ID"),
                },
                quote_via=quote_plus,
            )
        )

    @app.route("/")
    def home():
        try:
            if session["user"]:
                return view_latest_data()
                # json_data = get_all_from_db(graph=False)
                # data = json_data[0].json['all_data']
                # temp = json.loads(data[1])['temp']
                # return render_template('latest.html', data=data, temp=temp)
        except KeyError:
            print('test')
        return render_template("index.html", session=session.get('user'),
                               pretty=json.dumps(session.get('user'), indent=4))

    # Gör en route som skriver ut ett sparat meddelande
    @app.route('/api/v1/latest_data')
    @is_request_gateway
    @valid_api_key
    def get_latest_data():
        return get_all_from_db(graph=False)


    @app.route('/api/v1/all_data')
    @is_request_gateway
    @valid_api_key
    def get_all_data():
        return get_all_from_db(last_data=False, graph=False)

    @app.route('/data/logs')
    @valid_user
    @is_request_gateway
    def view_data_log():
        payload_list, date_list = get_all_from_db(last_data=False, graph=True)
        payload_list = [json.loads(data)['temp'] for data in payload_list]
        payload_list.reverse()
        return render_template('log.html', payload_data=payload_list,
                               date_data=sorted(date_list, reverse=True))

    @app.route('/data/latest')
    @valid_user
    @is_request_gateway
    def view_latest_data():
        json_data = get_all_from_db(graph=False)
        data = json_data[0].json['all_data']
        temp = json.loads(data[1])['temp']
        return render_template('latest.html', data=data, temp=temp)

    @app.route('/plot')
    @valid_user
    @is_request_gateway
    def plot_data():
        plt.clf()
        fig, ax = plt.subplots()
        payload_list, date_list = get_all_from_db(last_data=False, graph=True)
        payload_list = [json.loads(data)['temp'] for data in payload_list]
        date_list = [date[11:] for date in date_list]

        plt.plot(date_list, payload_list)
        plt.xlabel('Time')
        plt.subplots_adjust(bottom=0.3)
        plt.xticks(date_list)
        plt.xticks(rotation=90)
        plt.ylabel("Temp C°")

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
    app.run(port=os.environ.get("PORT", 3000))
