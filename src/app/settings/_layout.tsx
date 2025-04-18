import { Stack } from "expo-router"
import { StyleSheet } from "react-native"

const settingsLayout = () => {
  return (
        <Stack >
            <Stack.Screen name='profile' 
            options={{headerShown:false}}/>
            <Stack.Screen name='license' 
            options={{headerShown:false}}/>
            <Stack.Screen name='FQA' 
            options={{headerShown:false}}/>
            <Stack.Screen name='about' 
            options={{headerShown:false}}/>
        </Stack>
  )
}

export default settingsLayout

const styles = StyleSheet.create({
    AreaView:{
        flex:1,
    },
})