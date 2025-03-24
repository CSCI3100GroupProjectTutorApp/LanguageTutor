import { StyleSheet, Text, View, Dimensions,Image, TextInput, TouchableOpacity, ActivityIndicator, 
  KeyboardAvoidingView, Platform } from 'react-native'
import React, {useState} from 'react'
import { Link } from 'expo-router'
import {AntDesign,Ionicons} from '@expo/vector-icons'

const Login = () => {
const [username, setUsername] = useState("");
const [password, setPassword] = useState("");
const [showPassword, setShowPassword] = useState(false);
const [authPassword, setAuthPassword] = useState("");
const [showAuthPassword, setShowAuthPassword] = useState(false);
const [isLoading, setIsLoading] = useState(false); 

const handleSignup = () => {}
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
              placeholder='Enter your Password Again'
              placeholderTextColor={"#808080"}
              value={authPassword}
              onChangeText={setAuthPassword}
              autoCapitalize='none'
              secureTextEntry={!showAuthPassword}
          />
          <TouchableOpacity
              onPress ={()=>setShowAuthPassword(!showAuthPassword)}
              style={styles.eyeIcon}
          >
              <Ionicons
                  name={showAuthPassword? "eye-outline" : "eye-off-outline"}
                  size={20}
                  color="#703682"
              />
          </TouchableOpacity>
      </View>
  </View>
  <TouchableOpacity style={styles.button} onPress={handleSignup} disabled={isLoading}>
      {isLoading ? (
          <ActivityIndicator color ="white"/>
      ): (
          <Text style={styles.buttonText}>Sign up</Text>    
      )
      }
  </TouchableOpacity>

<View style={{justifyContent:'center',flexDirection:"row"}}>     
  <Text style={styles.footerText}>Already have an account?</Text>
  <Link href='/(auths)' asChild>
      <TouchableOpacity>
          <Text style={styles.signUpText}>Login</Text>
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
});