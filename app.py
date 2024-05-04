from datetime import timedelta
import logging
import os
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, redirect, render_template, send_file, send_from_directory, session, url_for
from flask_session import Session

from helper import *

load_dotenv()
app = Flask(__name__)
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', None)
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', None)
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', None)
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', None)
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{app.config['MYSQL_USER']}:{app.config['MYSQL_PASSWORD']}@{app.config['MYSQL_HOST']}/{app.config['MYSQL_DB']}"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['URL_APP'] = os.getenv('APP_IPS')
app.config['URL_APP_PORT'] = os.getenv('APP_PORT')
app.config['debug'] = os.getenv('MODE', "PRODUCTION")
app.config['mqttserv'] = os.getenv('MQTT_SERVER')
app.config['mqttport'] = os.getenv('MQTT_PORT')
app.config['mqttuser'] = os.getenv('MQTT_USER', None)
app.config['mqttpass'] = os.getenv('MQTT_PASSWORD', None)
mysql = create_app(SQLALCHEMY_DATABASE_URI)


"""
This function serves the index.html page
"""
@app.route('/')
def index():
    """
    This function returns the index.html page
    """
    return render_template('index.html')

@app.route('/api/v1/<mode>', methods=['GET', 'POST'])
def api_v1(mode):
    """
    This function handles API version 1 requests. It takes the MySQL database connection, the Flask request object, and the MQTT client as parameters. It then calls the `handleAPI_v1` function, passing the MySQL connection, the request object, and the MQTT client as arguments. The result of the `handleAPI_v1` function's `API_engine` method, with the specified `mode` as argument, is returned.

    Parameters:
    - mode (str): The mode of the API request.

    Returns:
    - Response: The response from the `handleAPI_v1` function's `API_engine` method.
    """
    return handleAPI_v1(mysql, request, mqtt_client).API_engine(mode)

if __name__ == "__main__":
    with app.app_context():
        mqtt_client = handleMQTT(app.config['mqttserv'], app.config['mqttport'], mysql, 60, app.config['mqttuser'], app.config['mqttpass'])
        mqtt_client.loop_start()
        
        if app.config['debug'] == 'PRODUCTION':
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
            app.run(debug=False, host=app.config['URL_APP'], port=app.config['URL_APP_PORT'], threaded=True, use_reloader=False)
        else:
            logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
            app.run(debug=True, host=app.config['URL_APP'], port=app.config['URL_APP_PORT'], threaded=True)
        