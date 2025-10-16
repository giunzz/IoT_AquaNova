#include<SoftwareSerial.h>
#include<ArduinoJson.h>

#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <time.h>

SoftwareSerial mySerial(20, 21);
// D20 - PA9
// D21 - PA10

#define MQTT_MAX_PACKET_SIZE 512

// --- THÔNG TIN WIFI ---
const char* ssid = "Wifi";
const char* password = "11111111";

// --- THÔNG TIN MQTT BROKER ---
const char* mqtt_server = "fdca86b156bf4f86973c13d0a7fe4e2c.s1.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char* mqtt_user = "aquanova_user";
const char* mqtt_pass = "Aquanova123";

// --- MQTT TOPICS ---
const char* publish_topic = "aquanova/devices/telemetry";
const char* subscribe_topic = "aquanova/devices/control";

// --- NTP CLIENT ---
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 25200); // UTC+7

// --- MQTT CLIENT ---
WiFiClientSecure espClient;
PubSubClient client(espClient);

// --- BIẾN TOÀN CỤC ---
unsigned long lastMsg = 0;
const unsigned long SEND_INTERVAL = 30000; // 30 giây

// === KHAI BÁO CHUYỂN TIẾP (FORWARD DECLARATIONS) ===
void sendAck(const char* command, bool success);
void reconnect(); // <--- SỬA LỖI 1: Thêm dòng này
void callback(char* topic, byte* payload, unsigned int length);

void setup() {
  Serial.begin(9600);
  delay(100);
  Serial.println("\n\n=== AquaNova ESP32 MQTT ===");

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
    Serial.println("\n[ERROR] WiFi connection failed!");
    return;
  }

  Serial.print("[NTP] Syncing time...");
  timeClient.begin();
  while (!timeClient.update()) {
    timeClient.forceUpdate();
    Serial.print(".");
    delay(500);
  }
  Serial.println("\n[NTP] Time synced successfully!");
  Serial.print("[NTP] Current Time: ");
  Serial.println(timeClient.getFormattedTime());

  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback); // Chỉ cần gọi 1 lần ở đây

  Serial.println("[SYSTEM] Setup complete!");
  mySerial.begin(9600);
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
  if (mySerial.available() > 0) {
    String input = mySerial.readStringUntil('\n');
    input.trim(); // Dọn dẹp chuỗi đầu vào

    if (input.length() > 0) {
      // SỬA LỖI 3: Gọi hàm 1 lần, lưu vào biến
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
  // SỬA LỖI 4: Làm cho hàm an toàn hơn
  payload.trim();
  StaticJsonDocument<256> doc;

  int firstComma = payload.indexOf(',');
  int secondComma = payload.indexOf(',', firstComma + 1);
  int thirdComma = payload.indexOf(',', secondComma + 1);

  // Chỉ xử lý nếu chuỗi có đủ 3 dấu phẩy
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
    // Nếu định dạng sai, tạo JSON báo lỗi
    doc["error"] = "Invalid payload format";
    doc["raw_payload"] = payload;
    Serial.println("[ERROR] Invalid payload format received from STM32: " + payload);
  }

  String jsonOutput;
  serializeJson(doc, jsonOutput);
  return jsonOutput;
}

// === CALLBACK: NHẬN TIN NHẮN TỪ MQTT ===
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

  // --- Xử lý lệnh điều khiển đèn ---
  if (doc.containsKey("light")) {
    int light_status = doc["light"];
    if (light_status == 1) {
      mySerial.write('L');
      Serial.println("[CONTROL] Sent 'L' (Light ON) to STM32");
    } else {
      mySerial.write('l');
      Serial.println("[CONTROL] Sent 'l' (Light OFF) to STM32");
    }
  }

  // --- Xử lý lệnh cho ăn ---
  if (doc.containsKey("feeding")) {
    int feeding_status = doc["feeding"];
    if (feeding_status != 0) {
      mySerial.write('F');
      Serial.println("[CONTROL] Sent 'F' (Start Feeding) to STM32");
    } else {
      mySerial.write('f');
      Serial.println("[CONTROL] Sent 'f' (Stop Feeding) to STM32");
    }
  }
} 

// === GỬI TIN NHẮN XÁC NHẬN (ACK) ===
void sendAck(const char* command, bool success) {
  DynamicJsonDocument ackDoc(128);
  ackDoc["device_id"] = "sensor-esp32-1";
  ackDoc["command"] = command;
  ackDoc["status"] = success ? "success" : "failed";
  ackDoc["timestamp"] = timeClient.getEpochTime();

  char ackBuffer[128];
  serializeJson(ackDoc, ackBuffer);
  
  client.publish("aquanova/devices/ack", ackBuffer);
  Serial.print("[ACK] Sent: ");
  Serial.println(ackBuffer);
}

// === KẾT NỐI LẠI MQTT ===
void reconnect() {
  int retries = 0;
  const int MAX_RETRIES = 5;

  Serial.println("[NTP] Re-syncing time before MQTT connection...");
  timeClient.update();
  
  while (!client.connected() && retries < MAX_RETRIES) {
    Serial.print("[MQTT] Attempting to connect... (");
    Serial.print(retries + 1);
    Serial.print("/");
    Serial.print(MAX_RETRIES);
    Serial.println(")");
    
    String clientId = "AquaNova_ESP32_";
    clientId += WiFi.macAddress();
    clientId.replace(":", "");
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("[MQTT] Connected!");
      client.subscribe(subscribe_topic);
      Serial.print("[MQTT] Subscribed to: ");
      Serial.println(subscribe_topic);
      return;
    } else {
      Serial.print("[MQTT] Connection failed, code: ");
      Serial.print(client.state());
      Serial.println(" - Retrying in 3 seconds...");
      retries++;
      delay(3000);
    }
  }
  
  if (!client.connected()) {
    Serial.println("[ERROR] MQTT connection failed after all retries. Will try again later.");
  }
}
