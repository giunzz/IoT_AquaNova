void reconnect() {
  int retries = 0;
  const int MAX_RETRIES = 5;

  // Bước 1: Cập nhật lại thời gian NTP
  timeClient.update();

  // Bước 2: Thử kết nối tối đa 5 lần
  while (!client.connected() && retries < MAX_RETRIES) {
    String clientId = "AquaNova_ESP32_" + WiFi.macAddress();
    clientId.replace(":", "");

    if (client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      client.subscribe(subscribe_topic);
      return;
    } else {
      retries++;
      delay(3000);
    }
  }
}
