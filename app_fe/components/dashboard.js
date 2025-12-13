import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Button,
  ActivityIndicator,
  Switch,
  RefreshControl,
} from "react-native";
import { LineChart } from "react-native-chart-kit";
import { Dimensions } from "react-native";
import Footer from "./Footer";
import { BASE_URL } from "../../api";

const SCREEN_WIDTH = Dimensions.get("window").width;
const SAFE_MIN = 0;
const SAFE_MAX = 1000;

export default function Dashboard() {
  // =========================
  // DASHBOARD DATA
  // =========================
  const [feedPercent, setFeedPercent] = useState("--");
  const [feedHint, setFeedHint] = useState("No data.");
  const [announceCount, setAnnounceCount] = useState(0);

  const [turbLabels, setTurbLabels] = useState([]);
  const [turbData, setTurbData] = useState([]);
  const [tableItems, setTableItems] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // =========================
  // LIGHT STATE (ACK MODEL)
  // =========================
  const [lightOn, setLightOn] = useState(null); // null = chưa sync
  const [lightSyncing, setLightSyncing] = useState(false);
  const [lightMsg, setLightMsg] = useState("Loading...");

  const lightPollTimer = useRef(null);

  // =========================
  // DASHBOARD LOAD
  // =========================
  async function loadAll({ silent = false } = {}) {
    try {
      if (!silent) setLoading(true);

      // Feed
      const last = await fetch(`${BASE_URL}/dashboard/last`).then(r => r.json());
      if (last?.item?.feed_amount != null) {
        const fa = last.item.feed_amount;
        setFeedPercent(fa);
        if (fa < 10) setFeedHint("Feed almost empty");
        else if (fa < 30) setFeedHint("Low feed level");
        else setFeedHint("Plenty of feed available");
      } else {
        setFeedPercent("--");
        setFeedHint("No data.");
      }

      // Announce
      const ann = await fetch(`${BASE_URL}/dashboard/announce-count`).then(r => r.json());
      setAnnounceCount(ann?.count ?? 0);

      // Latest
      const latest = await fetch(`${BASE_URL}/dashboard/latest?n=60`).then(r => r.json());
      const items = latest?.items || [];
      const reversed = items.slice().reverse();

      setTurbLabels(
        reversed.map(r => {
          const dt = new Date(r.ts);
          return isNaN(dt) ? "" : dt.toLocaleTimeString("vi-VN", { hour12: false });
        })
      );

      setTurbData(reversed.map(r => Number(r.turbidity)));
      setTableItems(items.slice(0, 10));
    } catch (err) {
      console.error("LOAD ERROR:", err);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  // =========================
  // LIGHT: POLLING CONTROL
  // =========================
  function startLightPolling() {
    if (!lightPollTimer.current) {
      lightPollTimer.current = setInterval(fetchLightState, 3000);
    }
  }

  function stopLightPolling() {
    if (lightPollTimer.current) {
      clearInterval(lightPollTimer.current);
      lightPollTimer.current = null;
    }
  }


  async function fetchLightState() {
    try {
      const res = await fetch(`${BASE_URL}/control/light`);
      const data = await res.json();

      if (!res.ok || typeof data.light !== "number") {
        throw new Error("Invalid light response");
      }

      const isOn = data.light === 1;
      setLightOn(isOn);
      setLightMsg(isOn ? "Light is ON" : "Light is OFF");
      return isOn;
    } catch (err) {
      console.error("FETCH LIGHT ERROR:", err);
      setLightMsg("Cannot get light state");
      return null;
    }
  }

  // =========================
  // LIGHT: SEND COMMAND + ACK
  // =========================
  async function requestLight(nextOn) {
    if (lightSyncing) return;

    stopLightPolling();
    setLightSyncing(true);

    // OPTIMISTIC UPDATE
    setLightOn(nextOn);
    setLightMsg("Sending command...");

    try {
      const res = await fetch(`${BASE_URL}/control/light`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ light: nextOn ? 1 : 0 }),
      });

      const data = await res.json();
      if (!res.ok || !data.ok) {
        throw new Error("Command rejected");
      }

      setLightMsg("Waiting for device confirmation...");

      const deadline = Date.now() + 10000;
      while (Date.now() < deadline) {
        const current = await fetchLightState();
        if (current === nextOn) {
          setLightMsg(nextOn ? "Light is ON" : "Light is OFF");
          startLightPolling();
          return;
        }
        await new Promise(r => setTimeout(r, 1000));
      }

      // Timeout → rollback
      setLightOn(!nextOn);
      setLightMsg("No ACK from device");

    } catch (err) {
      console.error("REQUEST LIGHT ERROR:", err);
      setLightOn(!nextOn);
      setLightMsg("Error controlling light");
    } finally {
      setLightSyncing(false);
      startLightPolling();
    }
  }

  // =========================
  // FEED NOW
  // =========================
  async function feedNow() {
    try {
      await fetch(`${BASE_URL}/control/feed-now`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: 20 }),
      });
    } catch (err) {
      console.error("FEED ERROR:", err);
    }
  }

  // =========================
  // EFFECTS
  // =========================
  useEffect(() => {
    (async () => {
      await Promise.all([loadAll(), fetchLightState()]);
      startLightPolling();
    })();

    return () => stopLightPolling();
  }, []);

  useEffect(() => {
    const t = setInterval(() => loadAll({ silent: true }), 600000);
    return () => clearInterval(t);
  }, []);

  async function onRefresh() {
    try {
      setRefreshing(true);
      await Promise.all([loadAll({ silent: true }), fetchLightState()]);
    } finally {
      setRefreshing(false);
    }
  }

  // =========================
  // LOADING
  // =========================
  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0ea5e9" />
      </View>
    );
  }

  // =========================
  // UI
  // =========================
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AquaNova Dashboard</Text>
      </View>

      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.cards}>
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Light in Tank</Text>
            <View style={styles.lightRow}>
              <Text>{lightOn === null ? "Loading..." : lightOn ? "ON" : "OFF"}</Text>
              <Switch
                value={!!lightOn}
                onValueChange={requestLight}
                disabled={lightOn === null || lightSyncing}
              />
            </View>
            <Text style={styles.muted}>{lightMsg}</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Feed Amount</Text>
            <Text style={styles.big}>{feedPercent}%</Text>
            <Text style={styles.muted}>{feedHint}</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Feed Now</Text>
            <Button title="Feed 20g" onPress={feedNow} />
          </View>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>Announce</Text>
            <Text style={styles.big}>{announceCount}</Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Turbidity</Text>
          <LineChart
            data={{ labels: turbLabels, datasets: [{ data: turbData }] }}
            width={SCREEN_WIDTH - 40}
            height={240}
            chartConfig={{
              backgroundColor: "#fff",
              backgroundGradientFrom: "#eef7ff",
              backgroundGradientTo: "#dceeff",
              color: (o = 1) => `rgba(14,165,233,${o})`,
            }}
            bezier
          />
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Temperature</Text>
          {tableItems.map((r, i) => {
            const t = Number(r.temperature);
            const safe = !isNaN(t) && t >= SAFE_MIN && t <= SAFE_MAX;
            return (
              <View key={i} style={styles.row}>
                <Text>{new Date(r.ts).toLocaleString()}</Text>
                <Text>{isNaN(t) ? "--" : `${t.toFixed(2)} °C`}</Text>
                <Text style={[styles.badge, safe ? styles.safe : styles.alert]}>
                  {safe ? "Safe" : "Alert"}
                </Text>
              </View>
            );
          })}
        </View>

        <Footer />
      </ScrollView>
    </View>
  );
}

// =========================
// STYLES
// =========================
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f6f7fb" },
  header: { backgroundColor: "#0ea5e9", padding: 18 },
  headerTitle: { color: "#fff", fontSize: 22, fontWeight: "700" },

  cards: { padding: 16 },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    elevation: 2,
  },

  cardTitle: { fontSize: 18, fontWeight: "600", marginBottom: 6 },
  big: { fontSize: 28, fontWeight: "700" },
  muted: { color: "#6b7280", marginTop: 4 },

  lightRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },

  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
    color: "#fff",
  },

  safe: { backgroundColor: "#16a34a" },
  alert: { backgroundColor: "#dc2626" },

  center: { flex: 1, justifyContent: "center", alignItems: "center" },
});
