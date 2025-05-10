import React from "react";
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ScrollView } from "react-native";
import {Link} from "expo-router"
import { Ionicons, MaterialIcons } from "@expo/vector-icons"; // You can use any icon library
import { SETTINGDATA } from "../../../assets/constants/settings";
import {SettingLayout} from "../../components/SettingLayout"

const settings = () => {
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.header}>Settings</Text>
      <FlatList
        data={SETTINGDATA}
        renderItem={({ item }) => 
                <SettingLayout settings={item}/>}
        scrollEnabled={false}
      />
    </ScrollView>
    
  );
}

export default settings

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "white", // Background color
    paddingHorizontal: 16,
  },
  header: {
    fontSize: 40,
    fontWeight: "bold",
    color: "#6713ba",
    marginVertical: 20,
  },
});