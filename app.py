import random

from flask import Flask, render_template



def create_app():
    app = Flask(__name__)

    def get_data():
        return random.randint(0, 100)

    @app.get('/index')
    def get_index():
        data = get_data()
        return render_template('index.html', data=data)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
