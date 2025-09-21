#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

// ====== CONFIG ======
const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASS";

const char* MQTT_HOST = "192.168.1.100";  // IP broker
const uint16_t MQTT_PORT = 1883;
const char* MQTT_USER = "aquanova";
const char* MQTT_PASS = "yourpass";

String DEVICE_ID = "sensor-1";            // đặt khác nhau cho mỗi ESP
String TOPIC_TELE = "aquanova/devices/" + DEVICE_ID + "/telemetry";
String TOPIC_CTRL = "aquanova/devices/" + DEVICE_ID + "/control";

WiFiClient espClient;
PubSubClient mqtt(espClient);

// ====== SENSOR GIẢ LẬP ======
float readTemperature(){ return 24.0 + (float)(esp_random()%700)/100.0; } // 24–31
float readTurbidity() { return 10.0 + (float)(esp_random()%700)/10.0; }   // 10–80
float readFeed()      { return (float)(esp_random()%1000)/10.0; }         // 0–100

// ====== NTP để lấy UTC ISO ======
String nowISO(){
  time_t now; time(&now);
  struct tm t; gmtime_r(&now, &t);
  char buf[32];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &t);
  return String(buf);
}

void wifiConnect(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi connecting");
  while (WiFi.status()!=WL_CONNECTED){ delay(500); Serial.print("."); }
  Serial.println(" OK");
}

void ntpInit(){
  configTime(0, 0, "pool.ntp.org", "time.nist.gov"); // UTC
  Serial.print("Sync time");
  time_t now = 0; int retries=0;
  while(now < 1700000000 && retries<30){ delay(500); time(&now); Serial.print("."); retries++; }
  Serial.println(" OK");
}

void onMqttMessage(char* topic, byte* payload, unsigned int len){
  Serial.print("\n[CTRL] "); Serial.write(payload, len); Serial.println();
  // ví dụ parse lệnh feed
  // StaticJsonDocument<128> doc; deserializeJson(doc, payload, len);
  // if (doc["cmd"]=="feed") { int amount=doc["amount"]; /* thực thi */ }
}

void mqttConnect(){
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  String clientId = "esp32-" + DEVICE_ID + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);

  while(!mqtt.connected()){
    Serial.print("MQTT connecting...");
    if (mqtt.connect(clientId.c_str(), MQTT_USER, MQTT_PASS,
                     ("aquanova/devices/"+DEVICE_ID+"/status").c_str(),
                     1, true, "offline")) {
      Serial.println(" OK");
      mqtt.publish(("aquanova/devices/"+DEVICE_ID+"/status").c_str(), "online", true);
      mqtt.subscribe(TOPIC_CTRL.c_str(), 1);
    } else {
      Serial.print(" failed rc="); Serial.print(mqtt.state()); Serial.println(" retry in 2s");
      delay(2000);
    }
  }
}

void setup(){
  Serial.begin(115200);
  wifiConnect();
  ntpInit();
  mqttConnect();
}

unsigned long lastPub=0;
const unsigned long PERIOD_MS = 5000; // gửi mỗi 5s (tăng lên 10–30s để tiết kiệm quota)

void loop(){
  if (WiFi.status()!=WL_CONNECTED) wifiConnect();
  if (!mqtt.connected()) mqttConnect();
  mqtt.loop();

  unsigned long now = millis();
  if (now - lastPub >= PERIOD_MS){
    lastPub = now;

    // đóng gói JSON
    StaticJsonDocument<256> doc;
    doc["device_id"]   = DEVICE_ID;
    doc["ts"]          = nowISO();
    doc["temperature"] = readTemperature();
    doc["turbidity"]   = readTurbidity();
    doc["feed"]        = readFeed();

    char buf[256];
    size_t n = serializeJson(doc, buf, sizeof(buf));
    bool ok = mqtt.publish(TOPIC_TELE.c_str(), buf, n, false);
    Serial.printf("[PUB] %s | %.*s\n", ok?"OK":"FAIL", (int)n, buf);
  }
}
