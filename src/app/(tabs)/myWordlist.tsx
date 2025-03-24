import { ScrollView, FlatList, StyleSheet, Text, View, TextInput, TouchableOpacity, Modal } from 'react-native'
import React, { useState } from "react";
import {WORDS} from '../../../assets/constants/Words'
import PreviewWordlist from '../../components/Preview-Wordlist'
import { Word } from '../../../assets/types/Word'


const Home = () => {
  const [words, setWords] = useState(WORDS);
  const [searchQuery, setSearchQuery] = useState("");
  const [newWordName, setNewWordName] = useState("");
  const [isSortedAsc, setIsSortedAsc] = useState(true); 
  const [visible, setVisble] = useState(false)

  const show = () => setVisble(true)
  const hide = () => setVisble(false)
  
  const filteredWords = words.filter((word) =>
    word.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const addNewWord = () => {
    hide()
  };
  
  const sortWords = () => {
    const sorted = [...words].sort((a, b) => {
      if (isSortedAsc) return a.name.localeCompare(b.name)
      else return b.name.localeCompare(a.name)
    });
    setWords(sorted);
    setIsSortedAsc(!isSortedAsc);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Search..."
        value={searchQuery}
        onChangeText={(text) => setSearchQuery(text)}
      />
      <View style={styles.button}>
        <TouchableOpacity onPress={sortWords} style={styles.sortButton}>
          <Text style={styles.sortButtonText}>
            Sort ({isSortedAsc ? "Ascending" : "Descending"})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={show} style={styles.addButton}>
          <Text style={styles.addButtonText}>Add New Word</Text>
            <Modal
              visible={visible}
              onRequestClose={() => {setNewWordName(''); addNewWord()}}
              animationType='fade'
              transparent
            >
              <View style={styles.modalOverlay}>
                <View style={styles.modalContent}>
                  <Text style={styles.modalTitle}>Add New Word</Text>
                    <TextInput
                      style={styles.modalInput}
                      placeholder="Enter a new word"
                      value={newWordName}
                      onChangeText={(text) => setNewWordName(text)}
                    />
                  <View style={styles.modalButtons}>
                    <TouchableOpacity onPress={() => {setNewWordName(''); hide()}} style={styles.cancelButton}>
                      <Text style={styles.cancelButtonText}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => {setNewWordName(''); addNewWord()}} style={styles.confirmButton}>
                      <Text style={styles.confirmButtonText}>Confirm</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            </Modal>
        </TouchableOpacity>
      </View>
      <FlatList 
        data={filteredWords} 
        renderItem={({ item }) => 
          <PreviewWordlist word={item}/>}
        keyExtractor={item => item.name}
        numColumns={1}
        contentContainerStyle={styles.flatListContent}
        style={{ paddingHorizontal:10, }}
        scrollEnabled={false}
      />
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
    paddingBottom: 10,
  },
  container: {
    padding: 10,
    backgroundColor: "#f9f9f9",
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
    backgroundColor: "#fff",
    height:60,
  },
  addButton: {
    width:'42%',
    marginLeft: 8,
    backgroundColor: "#007bff",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  addButtonText: {
    color: "#fff",
    fontWeight: "bold",
    alignItems: "center",
    textAlign: 'center',
  },
  sortButton: {
    width:'42%',
    marginRight: 8,
    backgroundColor: "#28a745",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginBottom: 12,

  },
  sortButtonText: {
    color: "#fff",
    fontWeight: "bold",
    textAlign: 'center',
  },
  button:{
      backgroundColor: '#f9f9f9',
      marginVertical: 4,
      borderRadius: 10,
      overflow: 'hidden',
      flexDirection:"row",
      marginHorizontal: 20,
      justifyContent: 'space-between'
  },
  hideButton:{
    height:100, 
    backgroundColor:'#DDD',
    opacity: .5,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  modalInput: {
    width: '100%',
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
    padding: 10,
    marginBottom: 20,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
  },
  cancelButton: {
    flex: 1,
    backgroundColor: '#f44336',
    padding: 10,
    borderRadius: 5,
    alignItems: 'center',
    marginRight: 5,
  },
  cancelButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  confirmButtonText: {
    color: 'white',
    fontWeight: 'bold',
  },
  confirmButton: {
    flex: 1,
    backgroundColor: '#4caf50',
    padding: 10,
    borderRadius: 5,
    alignItems: 'center',
    marginLeft: 5,
  },
})