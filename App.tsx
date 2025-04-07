import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ActivityIndicator, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { initializeAuth, apiClient, API_ENDPOINTS } from './src/api';

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [dbStatus, setDbStatus] = useState<{ status?: string; error?: string }>({});

  useEffect(() => {
    // Initialize authentication from stored token
    initializeAuth();
    
    // Test backend connection
    const testBackendConnection = async () => {
      try {
        // Test the database connection
        const result = await apiClient.get(API_ENDPOINTS.TEST_DB);
        setDbStatus({ status: 'Connected to backend and database' });
      } catch (error) {
        console.error('Backend connection test failed:', error);
        setDbStatus({ error: 'Failed to connect to backend' });
      } finally {
        setIsLoading(false);
      }
    };
    
    testBackendConnection();
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar style="auto" />
      
      <Text style={styles.title}>Language Tutoring App</Text>
      
      {isLoading ? (
        <ActivityIndicator size="large" color="#0000ff" />
      ) : (
        <View style={styles.statusContainer}>
          <Text style={styles.subtitle}>Backend Connection Status:</Text>
          
          {dbStatus.status ? (
            <Text style={styles.successText}>{dbStatus.status}</Text>
          ) : dbStatus.error ? (
            <Text style={styles.errorText}>{dbStatus.error}</Text>
          ) : null}
          
          <Text style={styles.infoText}>
            {Platform.OS === 'web' 
              ? 'Running on web platform'
              : `Running on ${Platform.OS}`
            }
          </Text>
        </View>
      )}
      
      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Frontend and Backend Integration Demo
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    marginBottom: 10,
    textAlign: 'center',
  },
  statusContainer: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    width: '100%',
    maxWidth: 500,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 5,
  },
  successText: {
    color: 'green',
    fontSize: 16,
    marginVertical: 10,
    textAlign: 'center',
  },
  errorText: {
    color: 'red',
    fontSize: 16,
    marginVertical: 10,
    textAlign: 'center',
  },
  infoText: {
    fontSize: 14,
    marginTop: 20,
    color: '#666',
    textAlign: 'center',
  },
  footer: {
    position: 'absolute',
    bottom: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
  },
});
