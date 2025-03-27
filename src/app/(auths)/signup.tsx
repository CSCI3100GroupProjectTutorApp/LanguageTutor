import { StyleSheet, Text, View, Dimensions, Image, TextInput, TouchableOpacity, ActivityIndicator, 
  KeyboardAvoidingView, Platform } from 'react-native'
import React, { useState } from 'react'
import { Link, router } from 'expo-router'
import { AntDesign, Ionicons } from '@expo/vector-icons'
import { register } from '../../api/auth'
import { APIError } from '../../api/client'

const Login = () => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [authPassword, setAuthPassword] = useState("");
  const [showAuthPassword, setShowAuthPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false); 
  const [errorMessage, setErrorMessage] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSignup = async () => {
    // Reset error message
    setErrorMessage("");
    
    // Validate inputs
    const missingFields = [];
    if (!username) missingFields.push("Username");
    if (!email) missingFields.push("Email");
    if (!password) missingFields.push("Password");
    if (!authPassword) missingFields.push("Password confirmation");

    if (missingFields.length > 0) {
      setErrorMessage(`Please fill in the following fields: ${missingFields.join(", ")}`);
      return;
    }

    if (!validateEmail(email)) {
      setErrorMessage("Please enter a valid email address");
      return;
    }
    
    if (password !== authPassword) {
      setErrorMessage("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long");
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await register({
        email,
        password,
        username,
        name: username // Using username as name since name field is required by the API
      });

      // If we get here, registration was successful
      setErrorMessage(response.message);
      setIsSuccess(true);
      
      // Wait a bit before redirecting to login
      setTimeout(() => {
        router.replace('/(auths)');
      }, 2000);
    } catch (err) {
      console.error('Registration error:', err);
      setIsSuccess(false);
      if (err instanceof APIError) {
        if (err.message?.includes('already exists')) {
          setErrorMessage('Username or email already exists. Please choose different ones.');
        } else if (err.status === 409) {
          setErrorMessage('This account already exists. Please try logging in instead.');
        } else {
          setErrorMessage(err.message || 'Registration failed. Please try again.');
        }
      } else {
        setErrorMessage('Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS === 'ios' ? "padding" : "height"}>
      <View style={styles.container}>
        <View style={{alignItems:'center', marginBottom:10}}>
          <Text style={styles.title}>Registration</Text>
        </View>
        <View style={{alignItems:'center', marginBottom:24}}>
          <Text style={styles.subtitle}>Sign up to learn smarter!</Text>
        </View>

        <View style={styles.inputGroup}>
          <View style={[styles.inputContainer, errorMessage && !username ? styles.inputError : null]}>
            <AntDesign
              name="user"
              size={20}
              color='gray'
              style={styles.inputIcon}
            />
            <TextInput
              style={styles.input}
              placeholder='Enter your Username'
              placeholderTextColor={"#808080"}
              value={username}
              onChangeText={(text) => {
                setUsername(text);
                setErrorMessage("");
              }}
              autoCapitalize='none'
            />
          </View>
        </View>
        
        <View style={styles.inputGroup}>
          <View style={[styles.inputContainer, errorMessage && (!email || !validateEmail(email)) ? styles.inputError : null]}>
            <AntDesign
              name="mail"
              size={20}
              color='gray'
              style={styles.inputIcon}
            />
            <TextInput
              style={styles.input}
              placeholder='Enter your Email'
              placeholderTextColor={"#808080"}
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                setErrorMessage("");
              }}
              autoCapitalize='none'
              keyboardType="email-address"
            />
          </View>
        </View>
        
        <View style={styles.inputGroup}>
          <View style={[styles.inputContainer, errorMessage && !password ? styles.inputError : null]}>
            <AntDesign
              name="lock"
              size={20}
              color='gray'
              style={styles.inputIcon}
            />
            <TextInput
              style={styles.input}
              placeholder='Enter your Password'
              placeholderTextColor={"#808080"}
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                setErrorMessage("");
              }}
              autoCapitalize='none'
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              style={styles.eyeIcon}
            >
              <Ionicons
                name={showPassword ? "eye-outline" : "eye-off-outline"}
                size={20}
                color="#703682"
              />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.inputGroup}>
          <View style={[styles.inputContainer, errorMessage && !authPassword ? styles.inputError : null]}>
            <AntDesign
              name="lock"
              size={20}
              color='gray'
              style={styles.inputIcon}
            />
            <TextInput
              style={styles.input}
              placeholder='Enter your Password Again'
              placeholderTextColor={"#808080"}
              value={authPassword}
              onChangeText={(text) => {
                setAuthPassword(text);
                setErrorMessage("");
              }}
              autoCapitalize='none'
              secureTextEntry={!showAuthPassword}
            />
            <TouchableOpacity
              onPress={() => setShowAuthPassword(!showAuthPassword)}
              style={styles.eyeIcon}
            >
              <Ionicons
                name={showAuthPassword ? "eye-outline" : "eye-off-outline"}
                size={20}
                color="#703682"
              />
            </TouchableOpacity>
          </View>
        </View>
        
        {errorMessage && (
          <Text style={[
            styles.errorText,
            isSuccess && styles.successText
          ]}>
            {errorMessage}
          </Text>
        )}
        
        <TouchableOpacity style={styles.button} onPress={handleSignup} disabled={isLoading}>
          {isLoading ? (
            <ActivityIndicator color="white"/>
          ) : (
            <Text style={styles.buttonText}>Sign up</Text>    
          )}
        </TouchableOpacity>

        <View style={{justifyContent:'center', flexDirection:"row"}}>     
          <Text style={styles.footerText}>Already have an account?</Text>
          <Link href='/(auths)' asChild>
            <TouchableOpacity>
              <Text style={styles.signUpText}>Login</Text>
            </TouchableOpacity>
          </Link>
        </View> 
      </View>
    </KeyboardAvoidingView>
  );
}

export default Login;
const { width } = Dimensions.get("window");


const styles = StyleSheet.create({
container: {
flexGrow: 1,
backgroundColor: "#703682",
padding: 20,
justifyContent: "center",
maxWidth: Platform.OS === 'web' ? 480 : '100%',
alignSelf: Platform.OS === 'web' ? 'center' : 'stretch',
minHeight: Platform.OS === 'web' ? '100%' : 'auto',
marginTop:-width*0.3,
},
topIllustration: {
alignItems: "center",
width: "100%",
},
illustrationImage: {
width: width * 0.75,
height: width * 0.75,
},
title: {
fontSize: 48,
fontWeight: "700",
color: "white",
},
subtitle: {
  fontSize: 16,
  fontWeight: "700",
  color: "white",
  },
inputGroup: {
marginBottom: 30,
},
inputContainer: {
paddingVertical:4,
flexDirection: "row",
alignItems: "center",
backgroundColor: "#f9f9f9",
borderRadius: 12,
borderWidth: 1,
borderColor: "#703682",
paddingHorizontal: 12,
},
inputIcon: {
marginRight: 10,
},
input: {
flex: 1,
height: 48,
color: "#1b361b",
},
eyeIcon: {
padding: 8,
},
button: {
backgroundColor: "#007bff",
borderRadius: 50,
paddingVertical: 15,
alignItems: "center",
justifyContent: "center",
width:"40%",
marginLeft:"30%",
marginBottom:30,
},
buttonText: {
color: 'white',
fontSize: 20,
fontWeight: "700",
},
errorContainer: {
marginBottom: 15,
padding: 10,
backgroundColor: 'rgba(255,0,0,0.1)',
borderRadius: 5,
borderWidth: 1,
borderColor: 'red',
},
errorText: {
color: 'red',
backgroundColor: 'rgba(255,255,255,0.7)',
padding: 10,
borderRadius: 5,
marginBottom: 15,
textAlign: 'center',
},
successText: {
color: '#4CAF50',
},
link: {
color: "#2e5a2e",
fontWeight: "600",
},
orText: {
fontSize: 16,
color: "white",
marginBottom: 20,
textAlign: "center",
},
socialContainer: {
flexDirection: "row",
justifyContent: "space-between",
width: "60%",
marginLeft:"20%",
marginBottom: 30,
alignItems:'center'
},
socialButton: {
width: 35,
height: 35,
borderRadius: 40,
backgroundColor:"#703682",
justifyContent: "center",
alignItems: "center",
},
socialIcon: {
width: 35,
height: 35,
resizeMode:'contain',
},
footer: {
flexDirection: "row",
justifyContent: "center",
marginTop: 24,
},
footerText: {
color: "white",
marginRight: 5,
fontSize: 16,
},
signUpText: {
color: "#007bff",
fontWeight: "bold",
fontSize: 16,
marginLeft:5
},
inputError: {
borderColor: 'red',
borderWidth: 1,
},
});