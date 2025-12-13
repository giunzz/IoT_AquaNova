import React, { useEffect, useRef, useState } from "react";
import { BASE_URL } from "../../api";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  Platform,
  ActivityIndicator,
  KeyboardAvoidingView,
} from "react-native";

import { Ionicons } from "@expo/vector-icons";
import * as Speech from "expo-speech";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system/legacy";
import Footer from "../components/Footer";

export default function ChatbotScreen() {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]); // {from:"user"|"bot", text:string}
  const [listening, setListening] = useState(false);
  const [uploading, setUploading] = useState(false);

  const scrollRef = useRef(null);
  const recordingRef = useRef(null);
  const stopTimerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (stopTimerRef.current) clearTimeout(stopTimerRef.current);
      stopTimerRef.current = null;

      (async () => {
        try {
          if (recordingRef.current) await recordingRef.current.stopAndUnloadAsync();
        } catch {}
        recordingRef.current = null;

        try {
          await Audio.setAudioModeAsync({
            allowsRecordingIOS: false,
            playsInSilentModeIOS: true,
          });
        } catch {}
      })();
    };
  }, []);

  function formatBotReply(reply) {
    try {
      const obj = JSON.parse(reply);
      if ("light" in obj) return obj.light === 1 ? "Đã bật đèn" : "Đã tắt đèn";
      if ("feeding" in obj) return "Đang cho cá ăn ngay!";
      return JSON.stringify(obj, null, 2);
    } catch {
      return reply;
    }
  }

  function scrollToEnd() {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 80);
  }

  async function sendMessage(msgText) {
    const finalText = (msgText ?? text).trim();
    if (!finalText) return;

    setMessages((prev) => [...prev, { from: "user", text: finalText }]);
    setText("");
    scrollToEnd();

    try {
      const res = await fetch(`${BASE_URL}/chatbot/api`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: finalText }),
      });

      const raw = await res.text();
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${raw.slice(0, 200)}`);

      const data = JSON.parse(raw);
      const botText = formatBotReply(data.reply ?? "");

      setMessages((prev) => [...prev, { from: "bot", text: botText }]);
      scrollToEnd();

      Speech.speak(botText, { language: "vi-VN", pitch: 1.0, rate: 1.0 });
    } catch (err) {
      setMessages((prev) => [...prev, { from: "bot", text: "Lỗi kết nối server." }]);
      scrollToEnd();
    }
  }

  async function ensureMicPermissionAndMode() {
    const perm = await Audio.requestPermissionsAsync();
    if (!perm.granted) throw new Error("Microphone permission not granted");

    await Audio.setAudioModeAsync({
      allowsRecordingIOS: true,
      playsInSilentModeIOS: true,
      shouldDuckAndroid: true,
    });
  }

  async function uploadToSTT(uri) {
    const info = await FileSystem.getInfoAsync(uri);
    if (!info.exists) throw new Error("Recorded file not found");

    const form = new FormData();
    form.append("audio", {
      uri,
      name: "voice.m4a",
      type: Platform.OS === "ios" ? "audio/m4a" : "audio/mp4",
    });

    const res = await fetch(`${BASE_URL}/chatbot/stt`, {
      method: "POST",
      body: form,
    });

    const raw = await res.text();
    if (!res.ok) throw new Error(`STT HTTP ${res.status}: ${raw.slice(0, 200)}`);

    // nếu server lỡ trả html => sẽ throw ở đây, log sẽ rõ
    const data = JSON.parse(raw);
    return (data?.text ?? "").toString().trim();
  }

  async function stopListeningAndSend() {
    try {
      if (stopTimerRef.current) clearTimeout(stopTimerRef.current);
      stopTimerRef.current = null;

      const recording = recordingRef.current;
      if (!recording) return;

      try {
        await recording.stopAndUnloadAsync();
      } catch {}

      setListening(false);

      const uri = recording.getURI();
      recordingRef.current = null;
      if (!uri) throw new Error("No recording URI");

      setUploading(true);
      const sttText = await uploadToSTT(uri);
      setUploading(false);

      if (sttText) {
        await sendMessage(sttText);
      } else {
        setMessages((prev) => [...prev, { from: "bot", text: "Không nhận được giọng nói." }]);
        scrollToEnd();
      }
    } catch (err) {
      setUploading(false);
      setListening(false);
      recordingRef.current = null;
      setMessages((prev) => [...prev, { from: "bot", text: "Lỗi thu âm hoặc nhận dạng giọng nói." }]);
      scrollToEnd();
      console.log("STT error:", err?.message || err);
    } finally {
      try {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: false,
          playsInSilentModeIOS: true,
        });
      } catch {}
    }
  }

  async function startListening() {
    try {
      if (listening) {
        await stopListeningAndSend();
        return;
      }

      setListening(true);
      await ensureMicPermissionAndMode();

      const recording = new Audio.Recording();
      recordingRef.current = recording;

      await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      await recording.startAsync();

      // auto stop sau 3s
      stopTimerRef.current = setTimeout(() => {
        stopListeningAndSend();
      }, 3000);
    } catch (err) {
      setListening(false);
      recordingRef.current = null;
      setMessages((prev) => [...prev, { from: "bot", text: "Không thể mở micro. Hãy kiểm tra quyền mic." }]);
      scrollToEnd();
      console.log("Start record error:", err?.message || err);

      try {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: false,
          playsInSilentModeIOS: true,
        });
      } catch {}
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.wrapper}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 64 : 0}
    >
      {/* HEADER */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AquaNova</Text>
        <Text style={styles.headerSub}>Assistant</Text>
      </View>

      {/* MAIN CARD */}
      <View style={styles.main}>
        <View style={styles.card}>
          <Text style={styles.cardTitle}>AquaNova Assistant</Text>

          <ScrollView style={styles.chatBox} ref={scrollRef}>
            {messages.map((m, i) => (
              <View
                key={i}
                style={[
                  styles.msg,
                  m.from === "user" ? styles.msgUser : styles.msgBot,
                ]}
              >
                <Text style={[styles.msgText, m.from === "user" ? styles.msgUserText : styles.msgBotText]}>
                  {m.text}
                </Text>
              </View>
            ))}
          </ScrollView>

          {/* RECORD INDICATOR */}
          {(listening || uploading) && (
            <Text style={styles.recording}>
              {uploading ? "Đang xử lý..." : "Đang nghe..."}
            </Text>
          )}

          {/* INPUT AREA */}
          <View style={styles.inputArea}>
            <TextInput
              style={styles.input}
              placeholder="Nói hoặc nhập lệnh..."
              value={text}
              onChangeText={setText}
              onSubmitEditing={() => sendMessage()}
              returnKeyType="send"
            />

            <TouchableOpacity style={styles.sendBtn} onPress={() => sendMessage()}>
              <Text style={styles.sendText}>Send</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.micBtn, listening && styles.micActive]}
              onPress={startListening}
              disabled={uploading}
            >
              {uploading ? (
                <ActivityIndicator />
              ) : (
                <Ionicons
                  name={listening ? "stop-circle-outline" : "mic-outline"}
                  size={22}
                />
              )}
            </TouchableOpacity>
          </View>
        </View>
      </View>

      <Footer />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  wrapper: { flex: 1, backgroundColor: "#f6f7fb" },

  header: {
    backgroundColor: "#0ea5e9",
    paddingHorizontal: 18,
    paddingVertical: 14,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerTitle: { color: "#fff", fontSize: 20, fontWeight: "700" },
  headerSub: { color: "#fff", opacity: 0.95, fontSize: 14 },

  main: { flex: 1, padding: 16 },
  card: {
    flex: 1,
    backgroundColor: "#fff",
    borderRadius: 14,
    padding: 16,
    shadowColor: "#000",
    elevation: 2,
  },
  cardTitle: { fontSize: 18, fontWeight: "700", marginBottom: 10 },

  chatBox: { flex: 1, marginBottom: 10 },
  msg: {
    padding: 12,
    borderRadius: 12,
    marginVertical: 6,
    maxWidth: "86%",
  },
  msgUser: { backgroundColor: "#2563eb", alignSelf: "flex-end" },
  msgBot: { backgroundColor: "#e5e7eb", alignSelf: "flex-start" },
  msgText: { fontSize: 15 },
  msgUserText: { color: "#fff" },
  msgBotText: { color: "#111" },

  recording: {
    textAlign: "center",
    paddingVertical: 6,
    color: "#dc2626",
    fontWeight: "700",
  },

  inputArea: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: "#eee",
    paddingTop: 10,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 42,
    backgroundColor: "#fff",
  },
  sendBtn: {
    backgroundColor: "#0ea5e9",
    height: 42,
    paddingHorizontal: 14,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  sendText: { color: "#fff", fontWeight: "700" },

  micBtn: {
    height: 42,
    width: 42,
    backgroundColor: "#e5e7eb",
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  micActive: { backgroundColor: "#fca5a5" },
});
