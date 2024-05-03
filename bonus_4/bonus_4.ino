#include <ESP8266WiFi.h>
#include <PubSubClient.h>

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
#define RELAY_PIN LED_BUILTIN

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("WiFi connected - IP address: ");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message diterima [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  
  if (strcmp(topic, "esp8266/relay") == 0) {
    if ((char)payload[0] == '1') {
      digitalWrite(RELAY_PIN, HIGH); // Turn on relay
    } else if ((char)payload[0] == '0') {
      digitalWrite(RELAY_PIN, LOW); // Turn off relay
    }
  }
}

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

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
