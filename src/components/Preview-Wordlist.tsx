// components/Preview-Wordlist.tsx

import { StyleSheet, Text, TouchableOpacity, View } from 'react-native'
import React from 'react'
import { useRouter } from 'expo-router';
import { Word } from '../../assets/types/Word'

const PreviewWordlist = (wordText: Word) => {
  
  const name = wordText.word
  const router = useRouter()

  return (
    <TouchableOpacity 
      style={styles.container}
      onPress={() => router.push(`/word/${name}`)}
    >
      <View style={styles.wordContainer}>
        <Text style={styles.wordText}>{wordText.word}</Text>
      </View>
      
      {wordText.part_of_speech && wordText.part_of_speech.length > 0 && (
        <View style={styles.definitionContainer}>
         <Text style={styles.partOfSpeech}>{wordText.part_of_speech.join(" ")}</Text>
        </View>
      )} 
      
      {wordText.ch_meaning.length > 0 && (
        <View style={styles.chineseContainer}>
          <Text style={styles.chineseText}>{wordText.ch_meaning.join("，")}</Text>
        </View>
      )}
    
    </TouchableOpacity>
  )
}

export default PreviewWordlist

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    marginVertical: 6,
    borderRadius: 10,
    padding: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  wordContainer: {
    marginBottom: 8,
  },
  wordText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  definitionContainer: {
    marginBottom: 5
  },
  definitionText: {
    fontSize: 16,
    color: 'black',
    marginBottom: 4,
    fontWeight: '400',
  },
  partOfSpeech: {
    fontSize: 14,
    fontStyle: 'italic',
    fontWeight: '500',
    color: '#888',
  },
  chineseContainer: {
    marginTop: 2,
  },
  chineseText: {
    fontSize: 18,
    color: '#333',
    fontWeight: '500',
  },
})