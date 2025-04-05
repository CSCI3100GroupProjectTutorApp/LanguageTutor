
import {View, StyleSheet, Text, StatusBar, TouchableOpacity,Platform, ActivityIndicator, Alert, Linking} from 'react-native';
import {SafeAreaView, SafeAreaProvider} from 'react-native-safe-area-context';
import React, {useState} from 'react';
import { AntDesign, Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from "expo-image-picker";

const upload = () => {
  
  const [selectFile, setSelectFile] = useState<DocumentPicker.DocumentPickerAsset| null>(null)
  const [photo, setPhoto] = useState<ImagePicker.ImagePickerAsset| null>(null)
  const [errorMessage, setErrorMessage] = useState(""); 
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectFile = async () => {
    setErrorMessage("")
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword",
                "application/pdf",
                "image/*",
                "text/plain"
        ],
        copyToCacheDirectory: true,
        multiple:false
      })

      if (!result.canceled) {
        const successResult = result as DocumentPicker.DocumentPickerSuccessResult
        setSelectFile(successResult.assets[0])
        setPhoto(null)
      } else {
        Alert.alert("No file selected","Select a File to Upload");
      }
    } catch (err:any) {
      setErrorMessage("Error: Something went wrong");
    }
  }

  
  // Function to upload the selected file
  const handleOpenCamera = async() => {
    setErrorMessage("")
    try{
      const { status } = await ImagePicker.getCameraPermissionsAsync()
      
      if (status === 'granted') {
        launchCamera();
      } else {
        const { status: newStatus } = await ImagePicker.requestCameraPermissionsAsync();
        if (newStatus === 'granted') {
          launchCamera();
        } else {
          Alert.alert(
            "Permission Denied",
            "Change the Camera Permission in the setting for this function",
            [{ text: "Cancel", style: "cancel" },
            { 
              text: "Go to Settings",
              onPress: () => Linking.openSettings() // Open the app's settings page
            }]
          );
        }
      }
    }
    catch (err: any){
      setErrorMessage("Error: Something went wrong")  
    }
      
  }
  const launchCamera = async () => {
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: false,
      cameraType:ImagePicker.CameraType.back,
      mediaTypes: "images",
      quality: 1,
    });

    if (!result.canceled) {
      setPhoto(result.assets[0]);
      setSelectFile(null);
    }
  }
  
  const handleUpload = () => {
    setErrorMessage("")
    try{
      if (selectFile || photo){
        const uploadFile = (selectFile ? selectFile : photo)
        // handle upload to server
      }
      else{
        setErrorMessage("No File Selected, Please select a file or take a photo")
      }
    }
    catch (err:any){
      setErrorMessage("Error: Something went wrong") 
    }
  }
  return (
  <SafeAreaProvider>
    <SafeAreaView style={styles.container}>
    <View style={{alignItems:'center', marginBottom:24}}>
      <Text style={styles.header}> Upload for Instant Translation</Text>
      <Text style={styles.descriptor}>Support file: pdf, doc, docx, images</Text>  
    </View>
    <TouchableOpacity style={styles.uploadBox} onPress={handleSelectFile}>
        <AntDesign name="addfile" size={40} color="black" />
        <Text style={styles.fileText}>Select file</Text>
        {!selectFile ? (!photo ? null : <Text>Upload File: {photo.uri}</Text>) : <Text>Upload File: {selectFile.name}</Text>}
    </TouchableOpacity>
    <View style={styles.seperatorContainer}>
        <View style={styles.seperator}/>
        <Text style={styles.orText}>or</Text>
        <View style={styles.seperator}/>
    </View>
    <TouchableOpacity style={styles.cameraButton} onPress={handleOpenCamera}>
        <Ionicons name="camera-outline" size={20} color="#FFFFFF" />
        <Text style={styles.cameraButtonText}> Open Camera</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.uploadButton} onPress={handleUpload} disabled={isLoading}>
        {isLoading ? (<ActivityIndicator color="black"/>) :
        (<Text style={styles.uploadButtonText}>Upload</Text>)}
      </TouchableOpacity>
      {errorMessage ? (
                  <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>{errorMessage}</Text>
                  </View>
                ) : null}
    </SafeAreaView>
  </SafeAreaProvider>
  )
}


export default upload

const styles = StyleSheet.create({
  container: {
    flex: 1,
    marginTop: StatusBar.currentHeight || 0,
    padding: 20,
    justifyContent: "center",
    maxWidth: Platform.OS === 'web' ? 480 : '100%',
    alignSelf: Platform.OS === 'web' ? 'center' : 'stretch',
    minHeight: Platform.OS === 'web' ? '100%' : 'auto',
  },
  header:{
    fontSize:24,
    fontWeight:'bold',
    marginBottom:10,
  },
  descriptor:{
    fontSize:14,
  },
  uploadBox: {
    width: "100%",
    height: "25%",
    borderRadius: 12,
    borderWidth: 2,
    borderColor: "black",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: "15%",
    backgroundColor:'white',
  },
  fileText: {
    fontSize: 16,
    color: "black",
    marginTop: 8,
  },
  seperatorContainer:{
    flexDirection:"row",
    alignItems: "center",
    marginBottom: 50,  
  },
  seperator:{
    height: 1,
    backgroundColor: "black",
    flex:1,
  },
  orText:{
    fontSize: 18,
    marginHorizontal:10,
    fontWeight:"600",
  },
  cameraButton: {
    flexDirection: "row",
    backgroundColor: "#333333",
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 8,
    justifyContent: "center",
    marginBottom: 50,
  },
  cameraButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    marginLeft: 8,
  },
  uploadButton: {
    backgroundColor: "#00FF85",
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 8,
    alignSelf: "stretch",
    alignItems: "center",
    marginBottom:24,
  },
  uploadButtonText: {
    color: "#1A1A1A",
    fontSize: 16,
    fontWeight: "bold",
  },
  errorText: {
    color: 'red',
    padding: 10,
    marginBottom: 15,
    textAlign: 'center',
    fontWeight: "600",
    fontSize:16,
    borderWidth: 2, 
    borderColor: 'red',
    borderRadius: 5,
  },
  errorContainer: {
    marginBottom: 15,
    padding: 10,
  },
})