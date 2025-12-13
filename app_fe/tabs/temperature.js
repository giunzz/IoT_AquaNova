import React, { useState, useEffect } from "react";
import {BASE_URL} from "../../api";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import Footer from "../components/Footer";
import { LineChart } from "react-native-chart-kit";
import { Dimensions } from "react-native";

const SCREEN_WIDTH = Dimensions.get("window").width;

export default function TemperatureScreen() {
  // ---------------- STATE ----------------
  const [currentTemp, setCurrentTemp] = useState("--");
  const [tempHint, setTempHint] = useState("No data.");
  const [alertCount, setAlertCount] = useState(0);

  const [chartLabels, setChartLabels] = useState([]);
  const [chartData, setChartData] = useState([]);

  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);

  const SAFE_MIN_TEMP = 24;
  const SAFE_MAX_TEMP = 30;

  const PAGE_SIZE = 20;

  // ---------------- FETCH DATA ----------------
  async function loadAll() {
    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/dashboard/latest?n=600`);
      const data = await res.json();
      const list = data.items || [];

      // sort newest first
      const sorted = list
        .slice()
        .sort((a, b) => new Date(b.ts) - new Date(a.ts));

      setItems(sorted);

      // Update cards
      if (sorted.length > 0) {
        const latest = sorted[0];
        const v = Number(latest.temperature ?? latest.temp ?? NaN);

        if (!isNaN(v)) {
          setCurrentTemp(v.toFixed(2));

          if (v < SAFE_MIN_TEMP || v > SAFE_MAX_TEMP) {
            setTempHint("Warning: temperature out of safe range!");
          } else {
            setTempHint("Temperature is in safe range.");
          }
        }

        const alerts = sorted.filter((r) => {
          const t = Number(r.temperature ?? r.temp ?? NaN);
          return t < SAFE_MIN_TEMP || t > SAFE_MAX_TEMP;
        }).length;
        setAlertCount(alerts);
      }

      // CHART DATA
      const recent = sorted.slice(0, 200).reverse();
      setChartLabels(
        recent.map((r) =>
          new Date(r.ts).toLocaleTimeString("vi-VN", { hour12: false })
        )
      );
      setChartData(
        recent.map((r) => Number(r.temperature ?? r.temp ?? NaN))
      );
    } catch (err) {
      console.log("ERROR:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    const timer = setInterval(loadAll, 600000); // 10 minutes
    return () => clearInterval(timer);
  }, []);

  // ---------------- PAGINATION ----------------
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageData = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // ---------------- UI ----------------
  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#0ea5e9" />
      </View>
    );
  }

  return (
    <View style={styles.wrapper}>
      {/* HEADER FIXED */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Temperature</Text>
      </View>

      {/* MAIN CONTENT */}
      <ScrollView style={styles.scrollArea}>
        {/* -------- CARDS -------- */}
        <View style={styles.cards}>
          {/* Current temp */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Current temperature</Text>
            <Text style={styles.bigText}>{currentTemp} °C</Text>
            <Text style={styles.muted}>{tempHint}</Text>
          </View>

          {/* Alerts */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Out-of-range alerts</Text>
            <Text style={styles.bigText}>{alertCount}</Text>
            <Text style={styles.muted}>Records outside safe range.</Text>
          </View>
        </View>

        {/* -------- CHART -------- */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Temperature Chart</Text>

          <LineChart
            data={{
              labels: chartLabels,
              datasets: [{ data: chartData }],
            }}
            width={SCREEN_WIDTH - 40}
            height={250}
            chartConfig={{
              backgroundColor: "#ffffff",
              backgroundGradientFrom: "#eef7ff",
              backgroundGradientTo: "#dceeff",
              color: (opacity = 1) => `rgba(14,165,233, ${opacity})`,
              strokeWidth: 2,
            }}
          />
        </View>

        {/* -------- TABLE -------- */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Temperature Readings</Text>

          {pageData.map((r, idx) => {
            const t = Number(r.temperature ?? r.temp ?? NaN);
            const safe = t >= SAFE_MIN_TEMP && t <= SAFE_MAX_TEMP;
            return (
              <View key={idx} style={styles.row}>
                <Text style={styles.rowText}>
                  {(page - 1) * PAGE_SIZE + idx + 1}.
                </Text>
                <Text style={styles.rowText}>
                  {new Date(r.ts).toLocaleString()}
                </Text>
                <Text style={styles.rowText}>{t.toFixed(2)} °C</Text>

                <Text style={[styles.badge, safe ? styles.safe : styles.alert]}>
                  {safe ? "Safe" : "Alert"}
                </Text>
              </View>
            );
          })}

          {/* PAGINATION */}
          <View style={styles.pagination}>
            <TouchableOpacity
              style={[styles.pageBtn, page <= 1 && styles.disabledBtn]}
              disabled={page <= 1}
              onPress={() => setPage(page - 1)}
            >
              <Text style={styles.pageBtnText}>Prev</Text>
            </TouchableOpacity>

            <Text style={styles.muted}>
              Page {page} / {totalPages}
            </Text>

            <TouchableOpacity
              style={[styles.pageBtn, page >= totalPages && styles.disabledBtn]}
              disabled={page >= totalPages}
              onPress={() => setPage(page + 1)}
            >
              <Text style={styles.pageBtnText}>Next</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>

      {/* FOOTER FIXED */}
      <Footer />
    </View>
  );
}

// ---------------- STYLES ----------------
const styles = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: "#f6f7fb" },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },

  header: { padding: 16, backgroundColor: "#0ea5e9" },
  headerTitle: { color: "#fff", fontSize: 22, fontWeight: "700" },

  scrollArea: { flex: 1 },

  cards: { padding: 16, flexDirection: "row", flexWrap: "wrap", gap: 12 },

  card: {
    backgroundColor: "white",
    padding: 16,
    borderRadius: 12,
    marginHorizontal: 14,
    marginVertical: 8,
    elevation: 2,
  },
  cardTitle: { fontSize: 18, fontWeight: "700", marginBottom: 8 },
  bigText: { fontSize: 28, fontWeight: "700", marginBottom: 6 },
  muted: { color: "#6b7280" },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderColor: "#e5e7eb",
  },
  rowText: { fontSize: 14 },

  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    color: "white",
  },
  safe: { backgroundColor: "#16a34a" },
  alert: { backgroundColor: "#dc2626" },

  pagination: {
    marginTop: 10,
    flexDirection: "row",
    justifyContent: "flex-end",
    gap: 10,
  },

  pageBtn: {
    backgroundColor: "#0ea5e9",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
  },
  disabledBtn: { opacity: 0.4 },
  pageBtnText: { color: "white", fontWeight: "600" },
});
