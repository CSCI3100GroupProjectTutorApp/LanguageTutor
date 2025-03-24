import {Stack} from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { SafeAreaView } from "react-native-safe-area-context";


export default function RootLayout(){
    return (
        <SafeAreaView style={{flex:1}}>
            <SafeAreaProvider>
            <Stack>
                <Stack.Screen name ='(auths)' options={{headerShown: false}}/>
                <Stack.Screen name ='(tabs)' options={{headerShown: false}}/>
                <Stack.Screen name ='word' options={{headerShown: false}}/>
            </Stack>
            <StatusBar style="dark" backgroundColor="transparent"/>
            </SafeAreaProvider>
        </SafeAreaView>
        
    );
}