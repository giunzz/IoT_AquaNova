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
