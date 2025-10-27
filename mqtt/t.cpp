2025-10-24T21:23:42.437787 [MQTT]  MESSAGE topic=aquanova/telemetry payload={'turbidity': 202.4, 'temperature': 28, 'feed': 0, 'thoi_gian': '21:22:39', 'ts': '2025-10-24T14:23:42.166958+00:00'}
127.0.0.1 - - [24/Oct/2025 21:23:49] "GET /dashboard/latest?n=200 HTTP/1.1" 200 -
127.0.0.1 - - [24/Oct/2025 21:24:18] "GET /dashboard/latest?n=200 HTTP/1.1" 200 -
127.0.0.1 - - [24/Oct/2025 21:24:20] "GET /dashboard/summary HTTP/1.1" 200 -
[DEBUG] Checking schedules at 21:24:22
[SCHEDULE] Feed → aquanova/control (repeat=none)
[SCHEDULE] Published feed successfully.
[SCHEDULE] Deleted one-time schedule f8c0b403ba81