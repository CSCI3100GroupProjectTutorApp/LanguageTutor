import { ScrollView, FlatList, FlatListComponent, StyleSheet, Text, View } from 'react-native'
import React from 'react'
import {WORDS} from '../../../assets/constants/Words'
import PreviewWordlist from '../../components/Preview-Wordlist'
import { Link } from "expo-router";
import {HomeHeader} from '../../components/Home-header'

const Home = () => {
  const recentWords = WORDS.filter((item) => item.recent<10);
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <FlatList 
        data={recentWords} 
        renderItem={({ item }) => 
        <PreviewWordlist word={item}/>}
        keyExtractor={item => item.name}
        numColumns={1}
        ListHeaderComponent={HomeHeader}
        contentContainerStyle={styles.flatListContent}
        style={{ paddingHorizontal:10, paddingVertical:5 }}
        scrollEnabled={false}
      />
      <Link href="/myWordlist" style={styles.link}>Look For More</Link>
    </ScrollView>         
  )
}

export default Home

const styles = StyleSheet.create({
  flatListContent:{
    paddingBottom: 10,
  },
  title:{
    fontSize: 24,
    color: 'blue', 
    textAlign: 'left',
    fontWeight: "bold", 
    paddingBottom: 10,
  },
  link: {
    fontSize: 20,
    color: "blue",
    textAlign: "center",
    paddingBottom: 20,
  },
  container: {
    padding: 10,
    backgroundColor: "#f9f9f9",
  },
})