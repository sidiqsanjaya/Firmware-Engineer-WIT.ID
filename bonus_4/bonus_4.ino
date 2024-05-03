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

/**
 * @brief Setup WiFi
 */
void setup_wifi() {
  delay(10);
  WiFi.begin(ssid, password); // Memulai koneksi WiFi dengan SSID dan kata sandi yang ditentukan
  while (WiFi.status() != WL_CONNECTED) { // Selama status WiFi bukan WL_CONNECTED
    delay(500);
    Serial.print(".");
  }
  Serial.println(""); // Mencetak baris kosong
  Serial.println("WiFi terhubung"); // Mencetak "WiFi terhubung"
  Serial.println("Alamat IP: "); // Mencetak "Alamat IP: "
  Serial.println(WiFi.localIP()); // Mencetak alamat IP lokal
}

/**
 * @brief fungsi jika ada pesan dari publis mqtt server
 */
void callback(char* topic, byte* payload, unsigned int length) {
    // Print message information
    Serial.print("Message arrived [");
    Serial.print(topic); // menampilkan topik pesan
    Serial.print("] ");
    for (int i = 0; i < length; i++) {
        Serial.print((char)payload[i]); // tipe data yg dikirimkan
    }
    Serial.println();

    if (strcmp(topic, "esp8266/relay") == 0) { // cek tipe topik, sama atau tidak

        String message = (char*)payload; //ubah ke string

        if (message == "1") {
            digitalWrite(RELAY_PIN, HIGH); // jika data payload tentang relay adalah 1 maka set High/hidupkan pin relay
        }

        else if (message == "0") {
            digitalWrite(RELAY_PIN, LOW); // jika data payload tentang relay adalah 0 maka set low/matikan pin relay
        }
    }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(mqtt_client_id, mqtt_username, mqtt_password)) { // uji coba koneksi ke mqtt server
      Serial.println("connected");
      client.subscribe("esp8266/relay");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state()); // menampilkan error jika gagal terhubung ke mqtt server
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port); // init server address dan port mqtt
  client.setCallback(callback); //
}

//fungsi ini bakal loop trs menerus, untuk mengecek koneksi mqtt, jika terhubung maka akan meloop fungsi 'client.loop() untuk menghandle pesan dan mqtt task.
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
