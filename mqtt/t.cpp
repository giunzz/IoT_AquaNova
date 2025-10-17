def on_disconnect(client, userdata, flags, reason_code, properties=None):
    write_log(f"[MQTT] DISCONNECTED (code={reason_code}) — attempting reconnect...")
    while True:
        try:
            client.reconnect()
            write_log("[MQTT] RECONNECTED successfully!")
            break
        except Exception as e:
            time.sleep(5)
