import {Tabs,Stack} from "expo-router"
import { SafeAreaView } from "react-native-safe-area-context"
import { StyleSheet, Platform} from "react-native";
import {Ionicons} from "@expo/vector-icons";

function TabBarIcon(props:{
    name: React.ComponentProps<typeof Ionicons>['name'];
    focused: boolean;
}){
    const {name, focused} = props;
    return <Ionicons name={name} size={24} color={focused? "#703682" : "gray"}/>;
}

const TabsLayout = () => {
    return (
        <SafeAreaView  style={styles.safeArea}>
            <Tabs screenOptions={{
                tabBarActiveTintColor:"#703682",
                tabBarInactiveTintColor: "gray",
                tabBarLabelStyle:{fontSize: 12},
                tabBarStyle:{
                    paddingTop: 0,
                    paddingBottom: 0,
                    height:50,
                },
                headerShown: false,
            }}>
                <Tabs.Screen 
                    name ="index"
                    options={{
                        title: "Home",
                        tabBarIcon: ({focused}) =>
                        <TabBarIcon name={focused ? "home" : "home-outline"} focused={focused}  
                        />,
                    }}
                />
                <Tabs.Screen 
                    name ="upload" 
                    options={{
                        title: "Upload",
                        tabBarIcon: ({focused}) =>
                        <TabBarIcon name={focused ? "open" : "open-outline"} focused={focused}  
                        />,
                    }}
                />
                <Tabs.Screen 
                    name ="myWordlist" 
                    options={{
                        title: "My Wordlist",
                        tabBarIcon: ({focused}) =>
                        <TabBarIcon name={focused ? "list" : "list-outline"}  focused={focused}  
                        />,
                    }}
                />
                <Tabs.Screen 
                    name ="settings" 
                    options={{
                        title: "Settings",
                        tabBarIcon: ({focused}) =>
                        <TabBarIcon name={focused ? "settings" : "settings-outline"} focused={focused}  
                        />,
                    }}
                />
                
            </Tabs>
        </SafeAreaView>
    );
};

export default TabsLayout;

const styles = StyleSheet.create({
    safeArea:{
        flex:1,
        justifyContent: "center",
        maxWidth: Platform.OS === 'web' ? 480 : '100%',
        alignSelf: Platform.OS === 'web' ? 'center' : 'stretch',
        minHeight: Platform.OS === 'web' ? '100%' : 'auto',
    },

});