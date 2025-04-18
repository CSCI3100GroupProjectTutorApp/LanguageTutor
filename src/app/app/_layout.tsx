import {Stack, Slot, useRouter, useSegments,useLocalSearchParams} from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView  } from "react-native-safe-area-context";
import { StyleSheet, Platform} from "react-native";
import { useEffect, useState,createContext, useCallback  } from 'react';
import { ActivityIndicator, View, Text } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NetworkSyncProvider  } from '../../assets/context/NetworkSyncProvider';

export default function RootLayout(){
    const [isLoading, setIsLoading] = useState(true);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const router = useRouter();
    const segments = useSegments();
    
    const checkLoginStatus = async () => {
        try {
          const userLoggedIn = await AsyncStorage.getItem('userLoggedIn');
          //console.log(`checkLoginStatus: ${userLoggedIn}`)
          setIsLoggedIn(userLoggedIn === 'true');
        } catch (error) {
          console.error('Failed to get login status:', error);
          setIsLoggedIn(false);
        } finally {
          setIsLoading(false);
        }
    }

    useEffect(() => {
        checkLoginStatus();
    }, [checkLoginStatus]);

    
    useEffect(() => {
      if (isLoading) return;

      const inAuthGroup = segments[0] === '(auths)';
      //console.log(`checkLogin: ${isLoggedIn}`)
      if (!isLoggedIn && !inAuthGroup) {
        // Redirect to login if not logged in and not already in auth group
        router.replace('/(auths)');
      } else if (isLoggedIn && inAuthGroup) {
        // Redirect to home if logged in but still in auth group
        router.replace('/(tabs)');
      }
    }, [isLoggedIn, isLoading]);
    
    if (isLoading) {
      return (<View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text>Loading...</Text>
      </View>)
    }
    return (
        <NetworkSyncProvider>
        <SafeAreaView style={{flex:1}}>
            <SafeAreaProvider>
            <Stack>
                <Stack.Screen name ='(auths)' options={{headerShown: false}}/>
                <Stack.Screen name ='(tabs)' options={{headerShown: false}}/>
                <Stack.Screen name ='translate' options={{headerShown: false}}/>
                <Stack.Screen name ='word' options={{headerShown: false}}/> 
                <Stack.Screen name ='settings' options={{headerShown: false}}/>         
            </Stack>
            <StatusBar style="dark" backgroundColor="transparent"/>
            </SafeAreaProvider>
        </SafeAreaView>
        </NetworkSyncProvider>
    )
}
const styles = StyleSheet.create({

})