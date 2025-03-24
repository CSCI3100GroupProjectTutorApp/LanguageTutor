import { StyleSheet, Text, View, Image,Pressable, } from 'react-native'
import React from 'react'
import { Link } from 'expo-router';

export const HomeHeader = () => {
  return (
    <View style={[styles.headerContainer]}>
        <Link asChild href='/upload'>
            <Pressable>
                <View style={styles.heroContainer}>
                    <Image
                    source={require('../../assets/image/heroImage.png')}
                    style={styles.heroImage}
                    />
                </View>
            </Pressable>
         </Link>
        <View>
            <Text style={styles.Title}>Recent</Text>
        </View>
    </View>
  )
}


const styles = StyleSheet.create({
    headerContainer: {
        gap: 20,
    },
    heroContainer: {
        width: '100%',
        height: 200, 
    },
    heroImage: {
        width: '100%',
        height: '100%',
        resizeMode: 'stretch',
        borderRadius: 20,
    },
    Title: {
        fontSize: 24,
        fontWeight: 'bold',
        marginBottom: 10,
        color:"blue"
    },
})