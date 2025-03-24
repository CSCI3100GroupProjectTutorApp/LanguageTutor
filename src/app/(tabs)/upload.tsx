
import {View, FlatList, StyleSheet, Text, StatusBar,Image} from 'react-native';
import {SafeAreaView, SafeAreaProvider} from 'react-native-safe-area-context';
import React from 'react'
import Methods from '../../components/Methods';
import {METHODS} from '../../../assets/constants/Methods'



const upload = () => {
  return (
  <SafeAreaProvider>
    <SafeAreaView style={styles.container}>
      <FlatList
        data={METHODS}
        renderItem={({item}) => <Methods method={item} />}
        numColumns={2}
        style={styles.flatList}
        contentContainerStyle={styles.flatListContent}
        columnWrapperStyle={styles.flatListColumn}
      />
    </SafeAreaView>
  </SafeAreaProvider>
  )
}


export default upload

const styles = StyleSheet.create({
  container: {
    flex: 1,
    marginTop: StatusBar.currentHeight || 0,
  },
  flatListContent: {
    paddingBottom: 20,
    paddingLeft: 20,
    paddingRight: 20,
  },
  flatListColumn: {
    justifyContent: 'space-between',
  },
  flatList:{
   
  }
})