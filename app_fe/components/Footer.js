import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function Footer() {
  return (
    <View style={styles.footer}>
      <Text style={styles.title}>Thành viên thực hiện</Text>
      <Text style={styles.text}>
        Hoàng Ngọc Dung – 23139006 | Đoàn Minh Duy Bình – 23139005 | 
        Trần Hữu Dương – 23130009
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  footer: {
    paddingVertical: 12,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    marginTop: 10,
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0ea5e9",
    textAlign: "center",
  },
  text: {
    textAlign: "center",
    color: "#6b7280",
    marginTop: 4,
  },
});
