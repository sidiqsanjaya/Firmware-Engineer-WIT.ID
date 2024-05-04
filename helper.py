from datetime import datetime, timedelta
import json
from flask import jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import paho.mqtt.client as mqtt

def create_app(app):
    """
    Create the core application object

    Args:
        app (Flask): The Flask application object

    Returns:
        mysql (SQLAlchemy): The SQLAlchemy engine object
    """
    mysql = create_engine(app)
    return mysql

def exec_query(engine, query, data=None):
    """
    Execute a SQL query against the specified SQLAlchemy engine.

    Args:
        engine (SQLAlchemy): The SQLAlchemy engine object
        query (str): The SQL query to execute
        data (str, optional): The data to pass to the query placeholders

    Returns:
        list: A list of tuples containing the query results

    Raises:
        SQLAlchemyError: If an error occurs while executing the query
    """
    try:
        with engine.connect() as connection:
            if data:
                result = connection.execute(text(query), text(data))
            else:
                result = connection.execute(text(query))
            connection.commit()
            rows = result.fetchall()
        return rows
    except SQLAlchemyError as e:
        return False, str(e)

def handleMQTT(serverMQTT, Port, mysql, interval=60, username=None, password=None):
    """
    Connects to an MQTT broker and subscribes to all topics.

    Args:
        serverMQTT (str): The IP address or domain name of the MQTT broker.
        Port (int): The port number of the MQTT broker.
        mysql (SQLAlchemy): The SQLAlchemy engine object.
        interval (int, optional): The interval in seconds between MQTT messages. Defaults to 60.
        username (str, optional): The username for authentication with the MQTT broker.
        password (str, optional): The password for authentication with the MQTT broker.

    Returns:
        mqtt.Client: The MQTT client object.

    Raises:
        Exception: If the MQTT broker cannot be connected to.

    """
    def on_connect(client, userdata, flags, rc):
        """
        Callback function for the MQTT client's on_connect event.

        Args:
            client (mqtt.Client): The MQTT client object.
            userdata (dict): User-defined data passed to the callback function.
            flags (int): Connection flags.
            rc (int): The result code of the connection attempt.

        """
        if rc == 0:
            print("Connected to broker")
        else:
            print("Connection failed")

    def on_message(client, userdata, msg):
        """
        Callback function for the MQTT client's on_message event.

        Args:
            client (mqtt.Client): The MQTT client object.
            userdata (dict): User-defined data passed to the callback function.
            msg (paho.mqtt.client.Message): The received MQTT message.

        """
        explode(mysql, msg.topic, msg.payload)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    if username is not None and password is not None:
        client.username_pw_set(username, password)
    client.connect(serverMQTT, int(Port), interval)
    client.subscribe("#")

    return client


def explode(mysql, topic, data):
    """
    Processes the incoming MQTT message and inserts the data into the database.

    Args:
    mysql (SQLAlchemy): The SQLAlchemy engine object.
    topic (str): The topic of the MQTT message.
    data (str): The payload of the MQTT message in JSON format.

    Returns:
    None

    Raises:
    Exception: If the MQTT broker cannot be connected to.

    This function first parses the JSON data from the MQTT message payload. It then extracts the node, dev_id, and dev_measure values from the data. After that, it checks if the device with the given chip_id and node exists in the database. If it does, it inserts the heartbeat and sensor log data into the respective tables.
    """
    data = json.loads(data)
    node = data['node']
    dev_id = data['dev_id']
    dev_measure = float(data['measure'])
    # print(data)
    # print(mysql)
    if len(exec_query(mysql, f"SELECT * FROM `device` WHERE `chip_id` = '{dev_id}' AND `node` = '{node}'")) == 1:  # verif chipid and node
        exec_query(mysql, f"INSERT INTO `heartbeat` (`id_hb`, `chip_id`, `last_seen`) VALUES (NULL, '{dev_id}', CURRENT_TIMESTAMP)")
        exec_query(mysql, f"INSERT INTO `log_sensor` (`id_log`, `chip_id`, `datetime`, `measure`) VALUES (NULL, '15879106', CURRENT_TIMESTAMP, '{dev_measure}')")

class handleAPI_v1:
    def __init__(self, mysql, request, mqtt_client):
        """
        Initialize the API_v1 class with the provided SQLAlchemy engine, Flask request object, and MQTT client.

        Args:
        mysql (SQLAlchemy): The SQLAlchemy engine object.
        request (Flask): The Flask request object.
        mqtt_client (paho.mqtt.client.Client): The MQTT client object.
        """
        self.mysql = mysql
        self.request = request
        self.mqtt_client = mqtt_client

    def API_engine(self, mode):
        """
        This function is used to handle different API requests based on the provided mode.

        Args:
            mode (str): The mode of the API request. It can be either 'device' or 'other' (for future use).

        Returns:
            dict: A dictionary containing the response to the API request.

        Raises:
            ValueError: If the provided mode is not 'device'.

        This function first checks if the provided mode is 'device'. If it is, it retrieves the chip_id from the request.args. It then checks if a 'get' parameter is provided in the request.args. Depending on the value of the 'get' parameter, it calls the corresponding API function (API_heartbeat, API_log_sensor, or API_relay) and returns the response. If the mode is not 'device', it returns a dictionary with a 'status' key set to 'invalid mode'.
        """
        if mode == 'device':
            chip_id = self.request.args.get('chip_id')
            if len(exec_query(self.mysql, f"SELECT * FROM `device` WHERE `chip_id` = '{chip_id}'")) == 1:
                get = self.request.args.get('get')
                if get == 'heartbeat':
                    return self.API_heartbeat(chip_id)
                elif get == 'log_sensor':
                    return self.API_log_sensor(chip_id)
                elif get == 'relay':
                    return self.API_relay(chip_id)
                else:
                    return jsonify(False, 'invalid get')
            else:
                return jsonify(False, 'chip_id not found')   
            
    def API_heartbeat(self, chip_id):
        """
        Checks the heartbeat status of a device with the given chip_id.

        Args:
            chip_id (str): A unique identifier for the device.

        Returns:
            dict: A dictionary containing a boolean value indicating whether the device is online or offline, and a message describing its status.
            If the device is not found in the database, a message indicating that the device is offline will be returned.

        This function calculates the number of jumps (intervals greater than 1 second between consecutive heartbeats) in the last 5 minutes, and compares it with a predefined percentage of jumps (30%). If the percentage of jumps exceeds the predefined value, the function returns a dictionary indicating that the device is offline. If not, it returns a dictionary indicating that the device is online.
        """
        val_5 = datetime.now() - timedelta(minutes=5)
        val_5_str = val_5.strftime('%Y-%m-%d %H:%M:%S')
        data = exec_query(self.mysql, f"SELECT * FROM `heartbeat` WHERE `chip_id` = '{chip_id}' AND `last_seen` BETWEEN '{val_5_str}' AND CURRENT_TIMESTAMP")
        if len(data) >= 220:
            return jsonify(True, 'normal')
        elif len(data) <= 210:
            return jsonify(True, 'device sering off')
        elif len(data) == 0:
            return jsonify(False, 'Perangkat mati')
        else:
            return jsonify(False, '?')
        
    def API_log_sensor(self, chip_id):
        """
        Retrieves sensor data from a device with the given chip_id.

        Args:
        chip_id (str): A unique identifier for the device.

        Returns:
        dict: A dictionary containing the sensor data for the specified device.

        This function retrieves sensor data from the database for the device with the given chip_id. It orders the data by the datetime column in descending order and limits the result to the last 300 records (or 1 record if 'realtime' parameter is provided). It then formats the data into a dictionary and returns it as a JSON response.
        """
        if self.request.args.get('realtime') is not None:
            val_5 = 1
        else:
            val_5 = 300
        result = exec_query(self.mysql, f"SELECT * FROM `log_sensor` WHERE `chip_id` = '{chip_id}' ORDER BY `log_sensor`.`datetime` DESC LIMIT 0, {val_5}")

        formatted_logs = []
        for log in result:
            formatted_log = {
                "measure": log[3],
            }
            formatted_logs.append(formatted_log)
        return jsonify(formatted_logs)

    def API_relay(self, chip_id):
        """
        This function is used to control the relay of a device with the given chip_id.

        Args:
        chip_id (str): A unique identifier for the device.

        Parameters relay (str): The state of the relay. It can be either 'on' or 'off'.

        Returns:
        dict: A dictionary containing a boolean value indicating whether the relay command was successfully sent, and a message describing its status.

        Raises:
        ValueError: If the provided chip_id is not found in the database.

        This function retrieves the MQTT client object from the class instance and publishes a message to the "esp8266/relay" topic with the value 1 or 0 depending on the relay parameter. It then returns a dictionary indicating that the relay command was successfully sent.
        """
        relay = self.request.args.get('set')
        if relay == 'on':
            self.mqtt_client.publish("esp8266/relay", 1)
        elif relay == 'off':
            self.mqtt_client.publish("esp8266/relay", 0)
        return jsonify(True, 'ok')
