#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "ACS712.h"

// WiFi settings
const char* ssid = "change me";
const char* password = "change me";

// MQTT settings
const char* mqtt_server = "change me";
const int mqtt_port = 1883;
const char* mqtt_username = "change me";
const char* mqtt_password = "change me";
const char* mqtt_client_id = "change me";

// Relay settings
#define SENSOR_PIN A0
#define RELAY_PIN LED_BUILTIN
const float max_volt = 12.8; //anggap ini nilai battery AKI full
ACS712  ACS(SENSOR_PIN, 3.3, 1024, 66);

WiFiClient espClient;

// Create an instance of the PubSubClient class, passing the WiFiClient instance as a parameter.
// This class is used to connect to an MQTT broker and subscribe/publish messages.
// The PubSubClient class is part of the PubSubClient library, which is used for MQTT communication.
// The WiFiClient instance is created in the setup_wifi() function.
// The PubSubClient instance is used throughout the program to connect to the MQTT broker and publish/subscribe messages.
PubSubClient client(espClient);

/**
 * @brief Setup WiFi connection
 *
 * This function initializes the WiFi connection by providing the SSID and password. It continuously attempts to connect to the WiFi network until a successful connection is established.
 *
 * @param None
 * @return None
 */
void setup_wifi() {
  WiFi.begin(ssid, password);  // Begin WiFi connection with provided SSID and password
  while (WiFi.status() != WL_CONNECTED) {  // Continuously check if WiFi is connected
    delay(500);  // Delay of 500 milliseconds
    Serial.print(".");  // Print a dot to indicate the connection process
  }
  Serial.println("");  // Print an empty line to separate the connection status message
  Serial.println("WiFi connected");  // Print a message to indicate successful WiFi connection
  Serial.println("IP address: ");  // Print a message to indicate the IP address
  Serial.println(WiFi.localIP());  // Print the local IP address
}

/**
 * @brief Callback function for handling incoming MQTT messages
 *
 * This function is called whenever a message is received on a subscribed topic.
 * It prints the topic and payload of the received message.
 * If the topic is "esp8266/relay", it interprets the payload as a binary value and sets the state of the relay accordingly.
 *
 * @param topic The topic of the received message
 * @param payload The payload of the received message
 * @param length The length of the payload
 * @return None
 */
void callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived [");
    Serial.print(topic);
    Serial.print("] ");
    String message;
    for (int i = 0; i < length; i++) {
        message = (char)payload[i];
    }
    Serial.println("");
    if (strcmp(topic, "esp8266/relay") == 0) {
        if (message == "1") {
            digitalWrite(RELAY_PIN, HIGH);
        } else if (message == "0") {
            digitalWrite(RELAY_PIN, LOW);
        }
    }
}

/**
 * @brief Get the unique chip ID of the ESP32 device
 *
 * This function retrieves the unique chip ID of the ESP32 device. The ESP32 chip ID is a unique identifier for each ESP32 device and can be used for device identification and tracking.
 *
 * @return The unique chip ID of the ESP32 device
 */
int getIdDev() {
  return ESP.getChipId();
}

/**
 * @brief Get the current Ampere measurement and publish it to the MQTT broker
 *
 * This function retrieves the current Ampere measurement using the ACS712 sensor and publishes it to the MQTT broker with the topic "esp8266/Ampere". The measurement is also printed to the serial monitor.
 *
 * @return None
 */
void getMeasureAndPublish() {
  int mA = ACS.mA_DC();  // Get the current Ampere measurement using the ACS712 sensor
  if (mA < 0.30) {  // If the measurement is less than 0.30, set it to 0
    mA = 0;
  }
  Serial.println(mA);  // Print the current Ampere measurement to the serial monitor

  StaticJsonDocument<200> doc;  // Create a JSON document to store the measurement data

  doc["node"] = "EMS";  // Set the "node" field to "EMS"
  doc["dev_id"] = String(getIdDev());  // Set the "dev_id" field to the unique chip ID of the ESP32 device
  doc["measure"] = mA;  // Set the "measure" field to the current Ampere measurement

  String jsonString;  // Create a string variable to store the JSON data
  serializeJson(doc, jsonString);  // Serialize the JSON document to a string

  char messageBuffer[jsonString.length() + 1];  // Create a character array to store the JSON string
  jsonString.toCharArray(messageBuffer, jsonString.length() + 1);  // Convert the JSON string to a character array

  client.publish("esp8266/Ampere", messageBuffer);  // Publish the JSON string to the MQTT broker with the topic "esp8266/Ampere"
  delay(1000);  // Add a delay of 1 second before the next measurement
}

/**
 * @brief Attempts to establish an MQTT connection and subscribes to the "esp8266/relay" topic
 *
 * This function continuously attempts to connect to the MQTT broker using the provided credentials. Once connected, it subscribes to the "esp8266/relay" topic to receive messages related to relay control.
 *
 * @return None
 */
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(mqtt_client_id, mqtt_username, mqtt_password)) {
      Serial.println("connected");
      client.subscribe("esp8266/relay");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}


/**
 * @brief Setup ESP32 device
 *
 * This function initializes the ESP32 device by setting up the serial communication, configuring the ACS712 sensor, setting the relay pin mode, and initializing the WiFi connection.
 *
 * @param None
 * @return None
 */
void setup() {
  Serial.begin(115200);  // Initialize serial communication at 115200 baud rate
  ACS.autoMidPoint();  // Auto-calibrate the ACS712 sensor
  pinMode(RELAY_PIN, OUTPUT);  // Set the relay pin as an output
  setup_wifi();  // Initialize the WiFi connection
  client.setServer(mqtt_server, mqtt_port);  // Set the MQTT broker server and port
  client.setCallback(callback);  // Set the callback function for handling incoming MQTT messages
}

/**
 * @brief Main loop function of the ESP32 device
 *
 * This function is the main loop function of the ESP32 device. It continuously checks the MQTT connection and calls the `getMeasureAndPublish` function to retrieve and publish the current Ampere measurement to the MQTT broker.
 *
 * @return None
 */
void loop() {
  if (!client.connected()) {
    reconnect();  // Function to attempt an MQTT connection and subscribe to the "esp8266/relay" topic
  }
  client.loop();  // Function to handle MQTT communication
  getMeasureAndPublish();  // Function to retrieve and publish the current Ampere measurement to the MQTT broker
}
