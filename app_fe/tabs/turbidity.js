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
import Footer from "../components/Footer"; // FOOTER CỐ ĐỊNH
import { LineChart } from "react-native-chart-kit";
import { Dimensions } from "react-native";

const SCREEN_WIDTH = Dimensions.get("window").width;

export default function TurbidityScreen() {
  // -------------------- STATE --------------------
  const [currentTurb, setCurrentTurb] = useState("--");
  const [turbHint, setTurbHint] = useState("No data.");
  const [highCount, setHighCount] = useState(0);

  const [turbLabels, setTurbLabels] = useState([]);
  const [turbData, setTurbData] = useState([]);

  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);

  const PAGE_SIZE = 20;

  const SAFE_MIN = 0;
  const SAFE_MAX = 200;
  const TURBIDITY_WARN = 200;

  // -------------------- FETCH DATA --------------------
  async function loadAll() {
    try {
      setLoading(true);

      const res = await fetch(`${BASE_URL}/dashboard/latest?n=600`);
      const data = await res.json();
      const list = data.items || [];

      // newest first
      const sorted = list.slice().sort((a, b) => new Date(b.ts) - new Date(a.ts));
      setItems(sorted);

      // Update cards
      if (sorted.length > 0) {
        const latest = sorted[0];
        const v = Number(latest.turbidity ?? NaN);

        if (!isNaN(v)) {
          setCurrentTurb(v.toFixed(2));

          if (v > TURBIDITY_WARN) {
            setTurbHint("Warning: turbidity is high!");
          } else {
            setTurbHint("Water turbidity is in safe range.");
          }
        }

        const highs = sorted.filter((r) => Number(r.turbidity) > TURBIDITY_WARN).length;
        setHighCount(highs);
      }

      // Prepare chart data
      const recent = sorted.slice(0, 200).reverse();
      setTurbLabels(
        recent.map((r) =>
          new Date(r.ts).toLocaleTimeString("vi-VN", { hour12: false })
        )
      );
      setTurbData(recent.map((r) => Number(r.turbidity ?? NaN)));

    } catch (err) {
      console.log("LOAD ERROR:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  useEffect(() => {
    const timer = setInterval(loadAll, 600000);
    return () => clearInterval(timer);
  }, []);

  // -------------------- PAGINATION --------------------
  const totalPages = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageData = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // -------------------- UI --------------------
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
        <Text style={styles.headerTitle}>Turbidity</Text>
      </View>

      {/* MAIN SCROLL CONTENT */}
      <ScrollView style={styles.scrollArea}>

        {/* CARDS */}
        <View style={styles.cards}>
          {/* Current turbidity */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Current turbidity</Text>
            <Text style={styles.bigText}>{currentTurb} NTU</Text>
            <Text style={styles.muted}>{turbHint}</Text>
          </View>

          {/* High turbidity alerts */}
          <View style={styles.card}>
            <Text style={styles.cardTitle}>High turbidity alerts</Text>
            <Text style={styles.bigText}>{highCount}</Text>
            <Text style={styles.muted}>Records above safe threshold</Text>
          </View>
        </View>

        {/* CHART */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Turbidity Chart</Text>

          <LineChart
            data={{
              labels: turbLabels,
              datasets: [{ data: turbData }],
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
            bezier
          />
        </View>

        {/* TABLE */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Turbidity Readings</Text>

          {pageData.map((r, idx) => {
            const turb = Number(r.turbidity ?? NaN);
            const safe = turb >= SAFE_MIN && turb <= SAFE_MAX;
            return (
              <View key={idx} style={styles.row}>
                <Text style={styles.rowText}>
                  {(page - 1) * PAGE_SIZE + idx + 1}.
                </Text>

                <Text style={styles.rowText}>
                  {new Date(r.ts).toLocaleString()}
                </Text>

                <Text style={styles.rowText}>{turb.toFixed(2)} NTU</Text>

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

      {/* FOOTER CỐ ĐỊNH */}
      <Footer />
    </View>
  );
}

// -------------------- STYLES --------------------
const styles = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: "#f6f7fb" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },

  header: { backgroundColor: "#0ea5e9", padding: 18 },
  headerTitle: { color: "white", fontSize: 22, fontWeight: "700" },

  scrollArea: { flex: 1 },

  cards: {
    padding: 16,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },

  card: {
    backgroundColor: "white",
    padding: 16,
    borderRadius: 12,
    marginHorizontal: 14,
    marginVertical: 8,
    elevation: 2,
  },

  cardTitle: { fontSize: 18, fontWeight: "700", marginBottom: 10 },
  bigText: { fontSize: 28, fontWeight: "700", marginBottom: 6 },
  muted: { color: "#6b7280" },

  row: {
    flexDirection: "row",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderColor: "#e5e7eb",
    justifyContent: "space-between",
  },
  rowText: { fontSize: 14 },

  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
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
