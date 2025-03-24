import { StyleSheet, Text, View, Pressable, TouchableOpacity } from 'react-native'
import { Setting } from '../../assets/types/Setting'
import { Ionicons } from "@expo/vector-icons"; 


export const SettingLayout = ({ settings }:{settings : Setting}) => {
    return (
        <View style={styles.section}>
        <Text style={styles.sectionTitle}>{settings.section}</Text>
            {settings.items.map((menuItem, index) => (
                <TouchableOpacity key={index} style={styles.item}>
                <View style={styles.iconWrapper}>
                    <Ionicons
                    name={menuItem.icon as keyof typeof Ionicons.glyphMap}
                    size={35}
                    color="black" // Icon color
                    />
                </View>
                <View style={styles.textWrapper}>
                    <Text style={styles.itemTitle}>{menuItem.title}</Text>
                    {menuItem.description ? (
                    <Text style={styles.itemDescription}>{menuItem.description}</Text>
                    ) : null}
                </View>
                <Ionicons
                    name="chevron-forward"
                    size={20}
                    color="black" // Chevron color
                />
                </TouchableOpacity>
            ))}
        </View>
    );
};

export default SettingLayout

const styles = StyleSheet.create({
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        fontSize: 30,
        fontWeight: "bold",
        color: "black", // Section title color
        marginBottom: 8,
    },
    item: {
        flexDirection: "row",
        alignItems: "center",
        backgroundColor: "white", // Item background
        padding: 12,
        borderRadius: 8,
        marginBottom: 8,
        borderColor:"black",
        borderWidth:1,
    },
    iconWrapper: {
        marginRight: 12,
    },
    textWrapper: {
        flex: 1,
    },
    itemTitle: {
        fontSize: 20,
        fontWeight: "bold",
        color: "black",
    },
    itemDescription: {
        fontSize: 12,
        color: "black", // Description text color
    },
})