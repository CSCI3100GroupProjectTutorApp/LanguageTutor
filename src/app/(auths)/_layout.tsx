import { Stack } from "expo-router"
import { StyleSheet } from "react-native"

const Authlayout = () => {
  return (
        <Stack >
            <Stack.Screen name='index' 
            options={{headerShown:false}}/>
            <Stack.Screen name='signup' 
            options={{headerShown:false}}/>
        </Stack>
  )
}

export default Authlayout

const styles = StyleSheet.create({
    AreaView:{
        flex:1,
    },
})