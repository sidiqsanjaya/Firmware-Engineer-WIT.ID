# Firmware Engineer WIT.ID

### Overview
This Flask application integrates with MySQL for database operations and MQTT for messaging services. It provides a web interface and an API endpoint for handling specific client requests based on the mode specified in the URL.
Features
#### Web Interface: Serve an HTML page at the root endpoint.
#### API Endpoint: Handle API requests dynamically based on the mode specified.
#### MySQL Integration: Connect to a MySQL database for data persistence.
#### MQTT Integration: Connect to an MQTT server for real-time messaging.

#### Environment Setup
1. Clone the repository: ```git clone https://github.com/sidiqsanjaya/Firmware-Engineer-WIT.ID```
2. Install dependencies:

    Ensure Python is installed on your system, then run: ```pip install -r requirements.txt```

     This will install Flask, PyMySQL, Flask-Session, python-dotenv, and other necessary packages.
3. Environment Variables:

   Create a .env file in the root directory of the project and add the following variables:
   ```
   MYSQL_HOST=your_mysql_host
      MYSQL_USER=your_mysql_user
      MYSQL_PASSWORD=your_mysql_password
      MYSQL_DB=your_database_name
      APP_IPS=your_app_ip
      APP_PORT=your_app_port
      MODE=PRODUCTION
      MQTT_SERVER=your_mqtt_server
      MQTT_PORT=your_mqtt_port
      MQTT_USER=your_mqtt_user
      MQTT_PASSWORD=your_mqtt_password
   ```

#### Running the Application
- Development Mode:
This will start the Flask server in development mode with hot reloading enabled.
- Production Mode:
Ensure the MODE in your .env file is set to PRODUCTION. Start the server with:
This will run the application in production mode with appropriate logging levels and without hot reloading.

#### API Usage
Access the API: ```GET or POST /api/v1/{mode}```
- Replace {mode} with the desired mode of operation which the API should handle. The response will vary based on the mode specified and the logic defined in handleAPI_v1.

#### MQTT Configuration
- The application connects to an MQTT server using the credentials and server details specified in the .env file. Ensure the MQTT server is accessible and the credentials are correct.

#### Logging
- Logs are configured to output different levels of messages based on the application mode. In PRODUCTION, only errors are logged, whereas in DEBUG mode, more verbose output is provided for debugging purposes.

Additional Information
- Ensure all paths and credentials are correctly set up in the .env file and the MySQL and MQTT servers are running before starting the application.
- For detailed function and class definitions, refer to the source code in app.py and any associated modules like helper.py.



