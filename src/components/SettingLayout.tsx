import { StyleSheet, Text, View, Pressable, TouchableOpacity, Alert, Platform } from 'react-native'
import { Setting } from '../../assets/types/Setting'
import { Ionicons } from "@expo/vector-icons"; 
import { Link, useRouter } from 'expo-router';
import { clearAuthToken } from '../services/authService';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const SettingLayout = ({ settings }:{settings : Setting}) => {
    const router = useRouter();

    const handleLogout = async() =>{
        try{ 
            await AsyncStorage.setItem('userLoggedIn', 'false');
            await AsyncStorage.setItem('userid', "")
        }
        catch(e){
            console.error("Logout Error: ",e)
        }   
    }

    const handleAction = async (action: string | undefined) => {
        console.log("Action triggered:", action);
        if (action === 'logout') {
            Alert.alert(
                "Log Out",
                "Are you sure you want to log out?",
                [
                    {
                        text: "Cancel",
                        style: "cancel"
                    },
                    {
                        text: "Log Out",
                        onPress: () => {
                            console.log("Logout confirmed, attempting to log out...");
                            // Clear the authentication token
                            clearAuthToken();
                            handleLogout()
                            
                            // Force navigation using different methods based on platform
                            if (Platform.OS === 'web') {
                                // For web, use direct location change
                                console.log("Using window.location for web logout...");
                                window.location.href = '/';
                            } else {
                                // For native, use router
                                console.log("Using router.replace for native logout...");
                                router.replace('../(auths)');
                            }
                        }
                    }
                ]
            );
        }
    };

    return (
        <View style={styles.section}>
        <Text style={styles.sectionTitle}>{settings.section}</Text>
            {settings.items.map((menuItem, index) => (
                menuItem.href ? (
                    <Link key={index} href={menuItem.href} asChild>
                        <TouchableOpacity style={styles.item}>
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
                    </Link>
                ) : (
                    <TouchableOpacity 
                        key={index} 
                        style={[
                            styles.item, 
                            menuItem.logoutStyle && styles.logoutItem
                        ]} 
                        onPress={() => handleAction(menuItem.action)}
                    >
                        <View style={styles.iconWrapper}>
                            <Ionicons
                            name={menuItem.icon as keyof typeof Ionicons.glyphMap}
                            size={35}
                            color={menuItem.logoutStyle ? "white" : "black"}
                            />
                        </View>
                        <View style={styles.textWrapper}>
                            <Text style={[
                                styles.itemTitle, 
                                menuItem.logoutStyle && styles.logoutText
                            ]}>
                                {menuItem.title}
                            </Text>
                            {menuItem.description ? (
                            <Text style={[
                                styles.itemDescription,
                                menuItem.logoutStyle && styles.logoutText
                            ]}>
                                {menuItem.description}
                            </Text>
                            ) : null}
                        </View>
                        {!menuItem.logoutStyle && (
                            <Ionicons
                                name="chevron-forward"
                                size={20}
                                color="black"
                            />
                        )}
                    </TouchableOpacity>
                )
            ))}
        </View>
    );
};

export default SettingLayout

const styles = StyleSheet.create({
    section: {
        marginBottom: 12,
    },
    sectionTitle: {
        fontSize: 30,
        fontWeight: "bold",
        color: "black", // Section title color
        marginBottom: 24,
    },
    item: {
        flexDirection: "row",
        alignItems: "center",
        backgroundColor: "white", // Item background
        padding: 12,
        borderRadius: 8,
        marginBottom: 20,
        borderColor:"black",
        borderWidth:1,
    },
    logoutItem: {
        backgroundColor: "red",
        borderColor: "red",
    },
    logoutText: {
        color: "white",
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