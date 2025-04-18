
import {View, StyleSheet, Text, StatusBar, TouchableOpacity,Platform, ActivityIndicator, Alert, Linking, ScrollView, Pressable} from 'react-native';
import {SafeAreaView, SafeAreaProvider} from 'react-native-safe-area-context';
import React, {useState} from 'react';
import { AntDesign, Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from "expo-image-picker";
import * as FileSystem from 'expo-file-system';
import { getAuthToken } from '../../services/authService'
import mammoth from "mammoth";
import { useRouter } from 'expo-router';

const upload = () => {
  
  const [selectFile, setSelectFile] = useState<DocumentPicker.DocumentPickerAsset| null>(null)
  const [photo, setPhoto] = useState<ImagePicker.ImagePickerAsset| null>(null)
  const [errorMessage, setErrorMessage] = useState(""); 
  const [isLoading, setIsLoading] = useState(false);
  const [extractedText, setExtractedText] = useState("")
  const router = useRouter ()

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
        const fileSize = successResult.assets[0].size || 0
        if (fileSize > 5 * 1024 * 1024){
          setErrorMessage("File too large (max 5MB)")
        }
        else{
          setSelectFile(successResult.assets[0])
          setPhoto(null)
        }
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
      const fileSize = result.assets[0].fileSize || 0
      if (fileSize > 5 * 1024 * 1024){
        setErrorMessage("File too large (max 5MB)")
      }
      else{
        setPhoto(result.assets[0]);
        setSelectFile(null);
      }
      
    }
  }
  
  const handleUpload = async() => {
    setErrorMessage("")
    setIsLoading(true)
    try{
      
      const token = await getAuthToken();
        if (!token) {
          throw new Error('Not authenticated');
        }
         
      const formData = new FormData()
      
      if (photo || selectFile){
        // Case: Photo taken to upload -> call OCR
        if(photo){
            formData.append('file', {
              uri: photo.uri,
              type: 'image/jpeg',
              name: 'image.jpg'
            } as any);
          
          const data = await handleOCR(formData,token)
          setExtractedText(data.text)
          const text = encodeURIComponent(data.text)
          setPhoto(null)
          router.navigate(`../translate/${text}`)
        }
        // Case: File selected to upload
        if(selectFile){
          const fileType = selectFile.mimeType?.toLowerCase() || '';
          // Case: File is not image
          if (!fileType.includes('image/jpeg') && !fileType.includes('image/png')) {
            const fileName = selectFile.name.split("/").pop();
            const newPath = `${FileSystem.documentDirectory}${fileName}`
            await FileSystem.copyAsync({
              from: selectFile.uri,
              to: newPath,
            })
            
            if(fileType.includes('application/pdf')){
                formData.append('file', {
                  uri: selectFile.uri,
                  type: selectFile.mimeType,
                  name: selectFile.name
                } as any);
                const data = await handleOCR(formData,token)
                setExtractedText(data.text)
                const text = encodeURIComponent(data.text)
                setSelectFile(null)
                router.navigate(`../translate/${text}`)
            }
            else if(fileType.includes('application/msword') || fileType.includes('application/vnd.openxmlformats-officedocument.wordprocessingml.document')){
              const data = await FileSystem.readAsStringAsync(newPath,{
                encoding: FileSystem.EncodingType.Base64,
              })
              const { value } = await mammoth.extractRawText({
                arrayBuffer: base64ToArrayBuffer(data),
              })

              setExtractedText(value);
              const text = encodeURIComponent(value.replace(/%/g,'~~~pct~~~'))
              setSelectFile(null)
              router.navigate(`../translate/${text}`)
            }
            else if(fileType.includes('text/plain')){
              const data = await FileSystem.readAsStringAsync(newPath)
              setExtractedText(data)
              const text = encodeURIComponent(data)
              setSelectFile(null)
              router.navigate(`../translate/${text}`)

            } 
          }
          // Case: File is image -> call OCR
          else{
              // For native platforms
              formData.append('file', {
                uri: selectFile.uri,
                type: selectFile.mimeType,
                name: selectFile.name
              } as any);
            }
            
            const data = await handleOCR(formData,token)
            setExtractedText(data.text)
            const text = encodeURIComponent(data.text)
            setSelectFile(null)
            router.navigate(`../translate/${text}`)

        }
          
      }
      else{
        setErrorMessage("No File Selected, Please select a file or take a photo")
      }
    }
    catch (err :any){
      console.error("Error uploading file:", err);
      setErrorMessage("Error: Something went wrong") 
    }
    finally{
      setIsLoading(false)
    }  
  }

  const handleOCR = async(formData: FormData, token: string) =>{
    const response = await fetch('http://192.168.0.118:8000/extract-text', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
      body: formData
    });

    if (!response.ok) {
      const errorText = await response.text();
      try {
        const errorData = JSON.parse(errorText);
        if (errorData.detail) {
          throw new Error(errorData.detail);
        } else {
          throw new Error(JSON.stringify(errorData));
        }
      } catch (e) {
        throw new Error(errorText || 'Failed to extract text');
      }
    }

    const data = await response.json()
    if (data){
      return data
    }  
  }

  const base64ToArrayBuffer = (base64: any) => {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  const base64ToUint8Array = (base64 : any) => {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
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
  resultContainer: {
    marginTop: 30,
    padding: 20,
    backgroundColor: "#fff",
    borderRadius: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 5,
    elevation: 3,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  resultText: {
    fontSize: 16,
    color: "#333",
  },
})