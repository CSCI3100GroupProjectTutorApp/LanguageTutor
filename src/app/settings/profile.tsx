import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TextInput, 
  TouchableOpacity, 
  ActivityIndicator,
  Alert,
  Platform,
  KeyboardAvoidingView,
  ScrollView
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import {getUserInfo} from '../../services/authService'
import { wordCount } from '../../services/wordService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const profile = () => {

    const [username, setUsername] = useState<string | null>(null);
    const [email, setEmail] =  useState<string | null>(null);
    const [count, setCount] = useState<number | null>(null);
    // State for loading status during API calls
    const [created, setCreated] = useState<string | null>(null);
    const [lastlogin, setLastlogin] =useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    
    function formatTimestamp(isoString) {
        const date = new Date(isoString);
        
        // Get components
        const year = date.getUTCFullYear();
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const day = String(date.getUTCDate()).padStart(2, '0');
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');
        
        // Format as YYYY-MM-DD HH:MM UTC
        return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
      }

    useEffect(() => {
        fetchInfo();
        loadWordCount();
    }, []);

      // Fetch the current user's license status
    const fetchInfo = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    
    try {
        const info = await getUserInfo();
        setUsername(info.username)
        setEmail(info.email)
        setCreated(info.created)
        setLastlogin(info.lastLogin)
    } catch (error: any) {
        setErrorMessage(error.message || 'Failed to get license status');
    } finally {
        setIsLoading(false);
    }
    };

    const loadWordCount = async () => {
        setIsLoading(true);
        setErrorMessage(null);
        
        try {
        const id = await AsyncStorage.getItem("userid")
        if (id){
            const result = await wordCount(id)
            setCount(result)
        }
        } catch (error: any) {
            setErrorMessage(error.message || 'Failed to get license status');
        } finally {
            setIsLoading(false);
        }
        };

    return (
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardAvoid}
        >
          <SafeAreaView style={styles.container}>
            <ScrollView>
              <Text style={styles.header}>My Profile</Text>
              
              {/* Request License Section */}
              <View style={styles.Card}>
                <Text style={styles.Title}>Username</Text>
                <Text style={styles.descriptionText}>
                  {username}
                </Text>
              </View>
              <View style={styles.Card}>
                <Text style={styles.Title}>Email</Text>
                <Text style={styles.descriptionText}>
                  {email}
                </Text>
              </View>
              <View style={styles.Card}>
                <Text style={styles.Title}>Account Log</Text>
                <View style={styles.logRow}><Text style={styles.descriptionText}>Last Login Time:</Text><Text style={styles.TimeText}>{formatTimestamp(lastlogin)}</Text></View>
                <View style={styles.logRow}><Text style={styles.descriptionText}>Created At:</Text><Text style={styles.TimeText}>{formatTimestamp(created)}</Text></View>
                </View>
                  
              <View style={styles.Card}>
                <Text style={styles.Title}>Added Word</Text>
                <Text style={styles.descriptionText}>
                  {count}
                </Text>
              </View>
              
              {/* Error Message */}
              {errorMessage && (
                <View style={styles.errorContainer}>
                  <Text style={styles.errorText}>{errorMessage}</Text>
                </View>
              )}
            </ScrollView>
          </SafeAreaView>
        </KeyboardAvoidingView>
      );
    };
    
    export default profile;
    
    const styles = StyleSheet.create({
      keyboardAvoid: {
        flex: 1,
      },
      container: {
        flex: 1,
        backgroundColor: '#F5F5F7',
        padding: 16,
      },
      header: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#6713ba',
        marginBottom: 30,
        marginTop: 20,
        textAlign: 'center'
      },
      Card: {
        backgroundColor: 'white',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 2,
      },
      Title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 16,
        color: '#333',
      },
      
      descriptionText: {
        fontSize: 18,
        color: '#555',
        marginBottom: 8,
      },
      TimeText: {
        fontSize: 18,
        color: '#555',
        marginBottom: 16,
        textAlign:'right',
      },
      errorContainer: {
        backgroundColor: '#FFEBEE',
        padding: 12,
        borderRadius: 8,
        marginBottom: 16,
      },
      logRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 8,
      },
    }); 