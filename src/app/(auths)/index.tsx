import { StyleSheet, Text, View, Dimensions,Image, TextInput, TouchableOpacity, ActivityIndicator, 
        KeyboardAvoidingView, Platform,ScrollView, Alert } from 'react-native'
import React, {useState} from 'react'
import { Link, useRouter } from 'expo-router'
import {AntDesign,Ionicons} from '@expo/vector-icons'

const Login = () => {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false); 
    const [error, setError] = useState("");
    const router = useRouter();
    
    const handleLogin = async () => {
      // Validate inputs
      if (!username || !password) {
        setError("Please enter both username and password");
        return;
      }
      
      setIsLoading(true);
      setError("");
      
      try {
        // Call the login API
        const response = await fetch('http://127.0.0.1:8000/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log("Login successful:", data);
          
          // Store the token (in a real app, you'd save this to secure storage)
          // For now, just navigate to the main app
          router.push('../(tabs)');
        } else {
          setError("Invalid username or password");
        }
      } catch (err) {
        console.error("Login error:", err);
        setError("Connection error. Please try again.");
      } finally {
        setIsLoading(false);
      }
    }
    
  return (
    <KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS === 'ios' ? "padding" : "height"}>
    <View style={styles.container}>
        <View style={styles.topIllustration}>
            <Image
                source={require("../../../assets/image/logo.png")}
                style={styles.illustrationImage}
                resizeMode='contain'
            />
        </View>
        <View style={{alignItems:'center', marginBottom:24}}>
            <Text style={styles.title}>Welcome Back !</Text>
        </View>
        <View style={styles.inputGroup}>
            <View style={styles.inputContainer}>
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
                    onChangeText={setUsername}
                    autoCapitalize='none'
                />
            </View>
        </View>
        <View style={styles.inputGroup}>
            <View style={styles.inputContainer}>
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
                    onChangeText={setPassword}
                    autoCapitalize='none'
                    secureTextEntry={!showPassword}
                />
                <TouchableOpacity
                    onPress ={()=>setShowPassword(!showPassword)}
                    style={styles.eyeIcon}
                >
                    <Ionicons
                        name={showPassword? "eye-outline" : "eye-off-outline"}
                        size={20}
                        color="#703682"
                    />
                </TouchableOpacity>
            </View>
        </View>
        
        {/* Display error message */}
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        
        <TouchableOpacity style={styles.button} onPress={handleLogin} disabled={isLoading}>
            {isLoading ? (
                <ActivityIndicator color ="white"/>
            ): (
                <Text style={styles.buttonText}>Log in</Text>    
            )
            }
        </TouchableOpacity>
        <Text style={styles.orText}>------------------- Or sign in with -------------------</Text>
        <View style={styles.socialContainer}>
        <TouchableOpacity style={styles.socialButton}>
          <Image
            source={{
              uri: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1280px-Google_%22G%22_logo.svg.png",
            }}
            style={styles.socialIcon}
          />
        </TouchableOpacity>
        <TouchableOpacity style={styles.socialButton}>
          <Image
            source={{
              uri: "https://upload.wikimedia.org/wikipedia/commons/0/05/Facebook_Logo_%282019%29.png",
            }}
            style={styles.socialIcon}
          />
        </TouchableOpacity>
        <TouchableOpacity style={styles.socialButton}>
          <Image
            source={{
              uri: "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/X_logo_2023.svg/1920px-X_logo_2023.svg.png",
            }}
            style={styles.socialIcon}
          />
        </TouchableOpacity>
      </View>

      <View style={{justifyContent:'center',flexDirection:"row"}}>     
        <Text style={styles.footerText}>Don't have an account?</Text>
        <Link href='/signup' asChild>
            <TouchableOpacity>
                <Text style={styles.signUpText}>Sign Up</Text>
            </TouchableOpacity>
        </Link>
      </View> 
    </View>
    </KeyboardAvoidingView>
    )
}

export default Login
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
  },
  topIllustration: {
    alignItems: "center",
    width: "100%",
  },
  illustrationImage: {
    width: Platform.OS === 'web' ? 200 : width * 0.75,
    height: Platform.OS === 'web' ? 200 : width * 0.75,
    maxWidth: '100%',
  },
  title: {
    fontSize: 32,
    fontWeight: "700",
    color: "white",
  },
  inputGroup: {
    marginBottom: 15,
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
  errorText: {
    color: 'red',
    backgroundColor: 'rgba(255,255,255,0.7)',
    padding: 10,
    borderRadius: 5,
    marginBottom: 15,
    textAlign: 'center',
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
    borderRadius: 35,
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
});