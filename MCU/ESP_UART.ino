#include <ArduinoJson.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <time.h>

// --- CẤU HÌNH PHẦN CỨNG ---

const int STM32_RX_PIN = 20; // Chân RX của ESP32 (kết nối với TX của STM32)
const int STM32_TX_PIN = 21; // Chân TX của ESP32 (kết nối với RX của STM32)

#define MQTT_MAX_PACKET_SIZE 512

// --- THÔNG TIN WIFI ---
const char* ssid = "Zun";
const char* password = "23456788";

// --- THÔNG TIN MQTT BROKER ---
const char* mqtt_server = "fdca86b156bf4f86973c13d0a7fe4e2c.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "aquanova_user";
const char* mqtt_pass = "Aquanova123";

// --- MQTT TOPICS ---
const char* publish_topic = "aquanova/telemetry";
const char* subscribe_topic = "aquanova/control";

// --- NTP CLIENT ---
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 25200);

// --- MQTT CLIENT ---
WiFiClientSecure espClient;
PubSubClient client(espClient);

// --- BIẾN TOÀN CỤC ---
unsigned long lastMsg = 0;
const unsigned long SEND_INTERVAL = 30000; // 30 giây

// --- KHAI BÁO HÀM ---
void reconnect(); 
void callback(char* topic, byte* payload, unsigned int length);
void publishSensorData();
String convertPayloadToJson(String payload);

void setup() { 
  // Bắt đầu Serial cho monitor (kết nối máy tính) ở tốc độ cao hơn
  Serial.begin(115200);
  delay(1000); // Đợi để ổn định
  Serial.println("\n\n=== AquaNova ESP32-C3 MQTT (Fixed Code) ===");

  // Bắt đầu Serial1 để giao tiếp với STM32
  Serial1.begin(9600, SERIAL_8N1, STM32_RX_PIN, STM32_TX_PIN);
  Serial.printf("[UART] Serial1 started for STM32 on RX:%d, TX:%d\n", STM32_RX_PIN, STM32_TX_PIN);

  // --- Kết nối WiFi ---
  Serial.print("[WiFi] Connecting to ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int wifiRetries = 0;
  while (WiFi.status() != WL_CONNECTED && wifiRetries < 20) {
    delay(500);
    Serial.print(".");
    wifiRetries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[ERROR] WiFi connection failed! Restarting...");
    delay(1000);
    ESP.restart();
  }

  // --- Đồng bộ thời gian NTP ---
  Serial.print("[NTP] Syncing time...");
  timeClient.begin();
  timeClient.forceUpdate();
  Serial.println("\n[NTP] Time synced!");

  // --- Cấu hình MQTT ---
  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  Serial.println("[SYSTEM] Setup complete!");
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  unsigned long now = millis();
  if (now - lastMsg > SEND_INTERVAL) {
    lastMsg = now;
    if(client.connected()) {
      timeClient.update();
      publishSensorData();
    }
  }
}

void publishSensorData() {
  if (Serial1.available() > 0) {
    String input = Serial1.readStringUntil('\n');
    input.trim(); 

    if (input.length() > 0) {
      String jsonPayload = convertPayloadToJson(input);

      Serial.print("From STM32: ");
      Serial.println(input);
      Serial.print("[PUBLISH] ");
      Serial.println(jsonPayload);
      
      if (!client.publish(publish_topic, jsonPayload.c_str())) {
        Serial.println("[ERROR] Publish failed.");
      }
    }
  }
}

String convertPayloadToJson(String payload) {
  payload.trim();
  StaticJsonDocument<256> doc;

  int firstComma = payload.indexOf(',');
  int secondComma = payload.indexOf(',', firstComma + 1);
  int thirdComma = payload.indexOf(',', secondComma + 1);

  if (firstComma > 0 && secondComma > firstComma && thirdComma > secondComma) {
    String doDucStr = payload.substring(0, firstComma);
    String nhietDoStr = payload.substring(firstComma + 1, secondComma);
    String phanTramStr = payload.substring(secondComma + 1, thirdComma);
    String thoiGianStr = payload.substring(thirdComma + 1);

    doc["turbidity"] = doDucStr.toFloat();
    doc["temperature"] = nhietDoStr.toFloat();
    doc["feed"] = phanTramStr.toInt();
    doc["thoi_gian"] = thoiGianStr;
  } else {
    doc["error"] = "Invalid payload format";
    doc["raw_payload"] = payload;
    Serial.println("[ERROR] Invalid payload format from STM32: " + payload);
  }

  String jsonOutput;
  serializeJson(doc, jsonOutput);
  return jsonOutput;
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("\n[MQTT] Message arrived on topic: ");
  Serial.println(topic);

  char message[length + 1];
  memcpy(message, payload, length);
  message[length] = '\0';
  
  Serial.print("[MQTT] Payload: ");
  Serial.println(message);

  DynamicJsonDocument doc(128);
  DeserializationError error = deserializeJson(doc, message);

  if (error) {
    Serial.print("[ERROR] JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (doc.containsKey("light")) {
    int light_status = doc["light"];
    if (light_status == 1) {
      Serial1.write('L');
      Serial.println("[CONTROL] Sent 'L' (Light ON) to STM32");
    } else {
      Serial1.write('l');
      Serial.println("[CONTROL] Sent 'l' (Light OFF) to STM32");
    }
  }

  if (doc.containsKey("feeding")) {
    int feeding_status = doc["feeding"];
    if (feeding_status != 0) {
      Serial1.write('F');
      Serial.println("[CONTROL] Sent 'F' (Start Feeding) to STM32");
    } else {
      Serial1.write('f');
      Serial.println("[CONTROL] Sent 'f' (Stop Feeding) to STM32");
    }
  }
} 

void reconnect() {
  while (!client.connected()) {
    Serial.print("[MQTT] Attempting connection...");
    
    String clientId = "AquaNova_ESP32_C3_";
    clientId += WiFi.macAddress();
    clientId.replace(":", "");
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println(" connected!");
      if(client.subscribe(subscribe_topic)) {
          Serial.print("[MQTT] Subscribed to: ");
          Serial.println(subscribe_topic);
      } else {
          Serial.println("[ERROR] Subscribe failed!");
      }
    } else {
      Serial.print(" failed, rc=");
      Serial.print(client.state());
      Serial.println(" - trying again in 5 seconds");
      delay(5000);
    }
  }
}

