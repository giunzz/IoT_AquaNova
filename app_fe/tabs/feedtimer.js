import React, { useState, useEffect } from "react";
import {BASE_URL} from "../../api";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from "react-native";
import { Dimensions } from "react-native";
import { PieChart } from "react-native-chart-kit";
import Footer from "../components/Footer";

const SCREEN_WIDTH = Dimensions.get("window").width;

export default function FeedTimer() {
  // ---------------- STATE ----------------
  const [feedAmount, setFeedAmount] = useState("20");
  const [feedMsg, setFeedMsg] = useState("");

  const [scDate, setScDate] = useState("");
  const [scTime, setScTime] = useState("08:30");
  const [scRepeat, setScRepeat] = useState("none");
  const [scAmount, setScAmount] = useState("20");
  const [scMsg, setScMsg] = useState("");

  const [scheduleList, setScheduleList] = useState([]);
  const [loadingSchedules, setLoadingSchedules] = useState(true);

  const [feedPercent, setFeedPercent] = useState(null);
  const [feedTime, setFeedTime] = useState("—");

  // ---------------- FEED NOW ----------------
  async function feedNow() {
    try {
      setFeedMsg("Sending...");
      const res = await fetch(`${BASE_URL}/control/feed-now`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: Number(feedAmount) }),
      });
      const data = await res.json();

      setFeedMsg(data.ok ? "Feed sent!" : "Error sending feed");
    } catch (err) {
      setFeedMsg("Error: " + err.message);
    } finally {
      setTimeout(() => setFeedMsg(""), 2500);
    }
  }

  // ---------------- LOAD FEED STATUS ----------------
  async function loadFeedStatus() {
    try {
      const res = await fetch(`${BASE_URL}/dashboard/last`);
      const data = await res.json();

      if (!data.item) return;

      const amount = Number(data.item.feed_amount ?? data.item.feed ?? 0);
      setFeedPercent(amount);
      setFeedTime(data.item.ts ?? "—");
    } catch (err) {
      console.log("Feed status error:", err);
    }
  }

  // ---------------- LOAD SCHEDULE ----------------
  async function loadSchedules() {
    try {
      setLoadingSchedules(true);
      const res = await fetch(`${BASE_URL}/control/schedules`);
      const data = await res.json();

      setScheduleList(data.items ?? []);
    } catch (err) {
      console.log("Load schedule error:", err);
    } finally {
      setLoadingSchedules(false);
    }
  }

  async function addSchedule() {
    if (!scDate || !scTime || !scAmount) {
      setScMsg("Please fill all fields.");
      return;
    }

    try {
      setScMsg("Creating...");
      const res = await fetch(`${BASE_URL}/control/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: scDate,
          time: scTime,
          repeat: scRepeat,
          amount: Number(scAmount),
        }),
      });

      const data = await res.json();

      if (!data.error) {
        setScMsg("Added.");
        loadSchedules();
      } else {
        setScMsg("Failed: " + data.error);
      }
    } catch (err) {
      setScMsg("Error: " + err.message);
    } finally {
      setTimeout(() => setScMsg(""), 2500);
    }
  }

  async function deleteSchedule(id) {
    Alert.alert("Confirm", "Delete this schedule?", [
      { text: "Cancel" },
      {
        text: "OK",
        onPress: async () => {
          try {
            await fetch(`${BASE_URL}/control/schedules/${id}`, {
              method: "DELETE",
            });
            loadSchedules();
          } catch (err) {
            Alert.alert("Error", err.message);
          }
        },
      },
    ]);
  }

  // ---------------- EFFECT ----------------
  useEffect(() => {
    loadFeedStatus();
    loadSchedules();
  }, []);

  useEffect(() => {
    const timer = setInterval(loadFeedStatus, 600000);
    return () => clearInterval(timer);
  }, []);

  // ---------------- UI ----------------
  return (
    <View style={styles.wrapper}>
      
      {/* FIXED HEADER */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Feed Timer</Text>
      </View>

      {/* SCROLLABLE CONTENT */}
      <ScrollView style={styles.scrollArea}>
        
        {/* ==== FEED NOW ==== */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Feed Now</Text>

          <Text>Amount (g)</Text>
          <TextInput
            value={feedAmount}
            onChangeText={setFeedAmount}
            keyboardType="numeric"
            style={styles.input}
          />

          <TouchableOpacity style={styles.btn} onPress={feedNow}>
            <Text style={styles.btnText}>Feed Now</Text>
          </TouchableOpacity>

          {!!feedMsg && <Text style={styles.msg}>{feedMsg}</Text>}
        </View>

        {/* ==== ADD SCHEDULE ==== */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Add Schedule</Text>

          <Text>Date (YYYY-MM-DD)</Text>
          <TextInput style={styles.input} value={scDate} onChangeText={setScDate} />

          <Text>Time (HH:MM)</Text>
          <TextInput style={styles.input} value={scTime} onChangeText={setScTime} />

          <Text>Repeat</Text>
          <TextInput
            style={styles.input}
            value={scRepeat}
            onChangeText={setScRepeat}
            placeholder="none | daily | weekly"
          />

          <Text>Amount (g)</Text>
          <TextInput
            style={styles.input}
            value={scAmount}
            onChangeText={setScAmount}
            keyboardType="numeric"
          />

          <TouchableOpacity style={styles.btnSecondary} onPress={addSchedule}>
            <Text style={styles.btnText}>Add Schedule</Text>
          </TouchableOpacity>

          {!!scMsg && <Text style={styles.msg}>{scMsg}</Text>}
        </View>

        {/* ==== PIE CHART ==== */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Feed Status</Text>

          {feedPercent === null ? (
            <ActivityIndicator size="large" color="#0ea5e9" />
          ) : (
            <>
              <PieChart
                data={[
                  {
                    name: "Remaining",
                    population: feedPercent,
                    color: "#0ea5e9",
                    legendFontColor: "#777",
                    legendFontSize: 12,
                  },
                  {
                    name: "Used",
                    population: 100 - feedPercent,
                    color: "#e5e7eb",
                    legendFontColor: "#777",
                    legendFontSize: 12,
                  },
                ]}
                width={SCREEN_WIDTH - 40}
                height={180}
                accessor="population"
                backgroundColor="transparent"
                hasLegend={false}
                chartConfig={{
                  backgroundColor: "#ffffff",
                  backgroundGradientFrom: "#ffffff",
                  backgroundGradientTo: "#ffffff",
                  color: (opacity = 1) => `rgba(0,0,0,${opacity})`,
                }}
                paddingLeft="20"
              />

              <Text style={styles.centerText}>
                {feedPercent}% — {feedTime}
              </Text>

              {feedPercent < 10 && (
                <Text style={[styles.centerText, { color: "red" }]}>
                  WARNING: Low Feed!
                </Text>
              )}
            </>
          )}
        </View>

        {/* ==== SCHEDULE LIST ==== */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Current Schedules</Text>

          {loadingSchedules ? (
            <ActivityIndicator size="large" color="#0ea5e9" />
          ) : scheduleList.length === 0 ? (
            <Text>No schedules.</Text>
          ) : (
            scheduleList.map((item, index) => (
              <View key={item.id ?? index} style={styles.row}>
                <Text>{item.date} {item.time}</Text>

                <TouchableOpacity
                  onPress={() => deleteSchedule(item.id)}
                  style={styles.deleteBtn}
                >
                  <Text style={{ color: "white" }}>Delete</Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>
      </ScrollView>

      {/* FIXED FOOTER */}
      <Footer />
    </View>
  );
}

// ---------------- STYLES ----------------
const styles = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: "#f6f7fb" },

  header: { backgroundColor: "#0ea5e9", padding: 18 },
  headerTitle: { color: "#fff", fontSize: 22, fontWeight: "700" },

  scrollArea: { flex: 1 },

  card: {
    backgroundColor: "#fff",
    padding: 16,
    marginHorizontal: 14,
    marginVertical: 10,
    borderRadius: 12,
    elevation: 2,
  },

  cardTitle: { fontSize: 18, fontWeight: "700", marginBottom: 10 },

  input: {
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#fff",
    padding: 10,
    borderRadius: 10,
    marginBottom: 12,
  },

  btn: {
    backgroundColor: "#2563eb",
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 6,
  },
  btnSecondary: {
    backgroundColor: "#0ea5e9",
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 6,
  },
  btnText: { color: "#fff", fontWeight: "700" },

  msg: { marginTop: 8, color: "#6b7280" },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
  },

  deleteBtn: {
    backgroundColor: "red",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },

  centerText: {
    textAlign: "center",
    marginTop: 10,
    color: "#6b7280",
  },
});
