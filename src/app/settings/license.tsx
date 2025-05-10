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
import { getLicenseStatus, activateLicense, requestLicense, LicenseStatus } from '../../services/licenseService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const LicencePage = () => {
  // State for license key input
  const [licenseKey, setLicenseKey] = useState('');
  const [isKeyValid, setIsKeyValid] = useState(true);
  
  // State for loading status during API calls
  const [isLoading, setIsLoading] = useState(false);
  const [isActivating, setIsActivating] = useState(false);
  const [isRequesting, setIsRequesting] = useState(false);
  
  // State for license status
  const [licenseStatus, setLicenseStatus] = useState<LicenseStatus | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch the license status on component mount
  useEffect(() => {
    fetchLicenseStatus();
  }, []);

  // Fetch the current user's license status
  const fetchLicenseStatus = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    
    try {
      const status = await getLicenseStatus();
      setLicenseStatus(status);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to get license status');
    } finally {
      setIsLoading(false);
    }
  };

  // Validate license key format
  const validateLicenseKey = (key: string) => {
    // License key format: XXXX-XXXX-XXXX-XXXX (alphanumeric)
    const pattern = /^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;
    return pattern.test(key.toUpperCase());
  };

  // Handle activation of a license key
  const handleActivateLicense = async () => {
    // Format license key to uppercase
    const formattedKey = licenseKey.toUpperCase();
    
    // Validate license key format
    if (!validateLicenseKey(formattedKey)) {
      setIsKeyValid(false);
      return;
    }
    
    setIsKeyValid(true);
    setIsActivating(true);
    setErrorMessage(null);
    
    try {
      const result = await activateLicense(formattedKey);
      Alert.alert('Success', result.message || 'License activated successfully');
      
      // Refresh license status
      await fetchLicenseStatus();
      await AsyncStorage.setItem('license','true')
      // Clear input field
      setLicenseKey('');
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to activate license');
    } finally {
      setIsActivating(false);
    }
  };

  // Handle requesting a new license
  const handleRequestLicense = async () => {
    setIsRequesting(true);
    setErrorMessage(null);
    
    try {
      const result = await requestLicense();
      
      if (result.success) {
        Alert.alert('Success', result.message || 'License key has been sent to your email.');
        // Refresh license status
        await fetchLicenseStatus();
      } else {
        setErrorMessage(result.message || 'Failed to request license');
      }
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to request license');
    } finally {
      setIsRequesting(false);
    }
  };

  // Format the activation date
  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.keyboardAvoid}
    >
      <SafeAreaView style={styles.container}>
        <ScrollView>
          <Text style={styles.header}>License Management</Text>
          
          {/* License Status Section */}
          <View style={styles.statusCard}>
            <Text style={styles.cardTitle}>License Status</Text>
            
            {isLoading ? (
              <ActivityIndicator size="large" color="#6713ba" />
            ) : licenseStatus ? (
              <>
                <View style={styles.statusRow}>
                  <Text style={styles.statusLabel}>Status:</Text>
                  <View style={[
                    styles.statusBadge, 
                    licenseStatus.has_valid_license ? styles.statusActive : styles.statusInactive
                  ]}>
                    <Text style={styles.statusText}>
                      {licenseStatus.has_valid_license ? 'Active' : 'Inactive'}
                    </Text>
                  </View>
                </View>
                
                {licenseStatus.has_valid_license && (
                  <>
                    <View style={styles.statusRow}>
                      <Text style={styles.statusLabel}>License Key:</Text>
                      <Text style={styles.statusValue}>{licenseStatus.license_key}</Text>
                    </View>
                    
                    <View style={styles.statusRow}>
                      <Text style={styles.statusLabel}>Activated On:</Text>
                      <Text style={styles.statusValue}>
                        {formatDate(licenseStatus.activated_at)}
                      </Text>
                    </View>
                  </>
                )}
                
                {licenseStatus.message && (
                  <Text style={styles.statusMessage}>{licenseStatus.message}</Text>
                )}
                
                <TouchableOpacity 
                  style={styles.refreshButton}
                  onPress={fetchLicenseStatus}
                >
                  <Ionicons name="refresh" size={20} color="white" />
                  <Text style={styles.refreshButtonText}>Refresh Status</Text>
                </TouchableOpacity>
              </>
            ) : (
              <Text style={styles.noDataText}>No license data available</Text>
            )}
          </View>
          
          {/* License Activation Section */}
          <View style={styles.activationCard}>
            <Text style={styles.cardTitle}>Activate License</Text>
            
            <Text style={styles.inputLabel}>Enter License Key</Text>
            <TextInput
              style={[styles.input, !isKeyValid && styles.inputError]}
              value={licenseKey}
              onChangeText={(text) => {
                setLicenseKey(text);
                setIsKeyValid(true);
              }}
              placeholder="XXXX-XXXX-XXXX-XXXX"
              autoCapitalize="characters"
              autoCorrect={false}
            />
            
            {!isKeyValid && (
              <Text style={styles.errorText}>
                Invalid license key format. Please use the format XXXX-XXXX-XXXX-XXXX.
              </Text>
            )}
            
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={handleActivateLicense}
              disabled={isActivating || licenseKey.trim() === ''}
            >
              {isActivating ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <>
                  <Ionicons name="key" size={20} color="white" />
                  <Text style={styles.buttonText}>Activate License</Text>
                </>
              )}
            </TouchableOpacity>
          </View>
          
          {/* Request License Section */}
          <View style={styles.requestCard}>
            <Text style={styles.cardTitle}>Need a License?</Text>
            <Text style={styles.descriptionText}>
              Request a license key to unlock all features of the application.
            </Text>
            
            <TouchableOpacity 
              style={styles.secondaryButton}
              onPress={handleRequestLicense}
              disabled={isRequesting}
            >
              {isRequesting ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <>
                  <Ionicons name="mail" size={20} color="white" />
                  <Text style={styles.buttonText}>Request License</Text>
                </>
              )}
            </TouchableOpacity>
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

export default LicencePage;

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
  statusCard: {
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
  activationCard: {
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
  requestCard: {
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
  cardTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#333',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  statusLabel: {
    fontSize: 16,
    fontWeight: '600',
    width: 110,
    color: '#555',
  },
  statusValue: {
    fontSize: 16,
    color: '#333',
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusActive: {
    backgroundColor: '#4CAF50',
  },
  statusInactive: {
    backgroundColor: '#F44336',
  },
  statusText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 14,
  },
  statusMessage: {
    fontSize: 14,
    color: '#555',
    fontStyle: 'italic',
    marginTop: 8,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    color: '#555',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    backgroundColor: '#F9F9F9',
    marginBottom: 16,
  },
  inputError: {
    borderColor: '#F44336',
  },
  primaryButton: {
    backgroundColor: '#6713ba',
    borderRadius: 8,
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  secondaryButton: {
    backgroundColor: '#2196F3',
    borderRadius: 8,
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    marginTop: 8,
  },
  refreshButton: {
    backgroundColor: '#333',
    borderRadius: 8,
    height: 40,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
    marginTop: 16,
    alignSelf: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  refreshButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 8,
  },
  descriptionText: {
    fontSize: 15,
    color: '#555',
    marginBottom: 16,
  },
  errorContainer: {
    backgroundColor: '#FFEBEE',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#D32F2F',
    fontSize: 14,
  },
  noDataText: {
    fontSize: 16,
    color: '#888',
    fontStyle: 'italic',
    textAlign: 'center',
    marginVertical: 16,
  },
}); 