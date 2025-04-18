import { ScrollView, FlatList, StyleSheet, Text, View, TextInput, TouchableOpacity, Modal, Alert, DeviceEventEmitter } from 'react-native'
import React, { useState, useEffect, useCallback, useRef } from "react";
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
import PreviewWordlist from '../../components/Preview-Wordlist'
import { Word, WordCreate } from '../../../assets/types/Word'
import * as wordService from '../../services/wordService';
import * as translateService from '../../services/translateService';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TRANSLATION_COMPLETED_EVENT } from '../../../assets/context/NetworkSyncProvider';

const Home = () => {
  const params = useLocalSearchParams<{ refresh: string }>();
  const [words, setWords] = useState<Word[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [newWord, setNewWord] = useState<string>("")
  const [isSortedAsc, setIsSortedAsc] = useState(true); 
  const [visible, setVisible] = useState(false);
  const [userid, setUserid] = useState<string | null>(null);
  
  // Track the current focus session to avoid duplicate loads
  const currentFocusSession = useRef<string | null>(null);
  
  // Load user ID only once when component mounts
  useEffect(() => {
    const loadUserId = async () => {
      try {
        // Try to get from both possible keys for maximum compatibility
        const id = await AsyncStorage.getItem("userid") || 
                  await AsyncStorage.getItem("userId");
                  
        console.log("Loaded userId in myWordlist:", id);
        
        if (id) {
          setUserid(id);
          // Also ensure it's saved under both keys for consistency
          await AsyncStorage.setItem("userId", id);
          await AsyncStorage.setItem("userid", id);
        } else {
          console.error("No user ID found in storage");
          Alert.alert("Error", "User ID not found. Please log in again.");
        }
      } catch (error) {
        console.error("Failed to load user ID:", error);
        Alert.alert("Error", "Failed to access user data. Please restart the app.");
      }
    };
    
    loadUserId();
  }, []);

  // Listen for translation completed events
  useEffect(() => {
    const subscription = DeviceEventEmitter.addListener(
      TRANSLATION_COMPLETED_EVENT,
      () => {
        console.log('TRANSLATION EVENT: Translation completed, reloading word list...');
        if (userid) {
          // Create a unique ID for event-triggered loading
          const loadId = `translation-event-${Date.now()}`;
          loadAllWords(loadId);
        }
      }
    );
    
    return () => {
      subscription.remove();
    };
  }, [userid]);

  // Handle focus events and refreshes
  useFocusEffect(
    useCallback(() => {
      // Create a unique session ID for this focus event
      // Combine refresh param with timestamp to ensure uniqueness
      const refreshParam = params.refresh || '';
      const focusSessionId = `focus-${refreshParam}-${Date.now()}`;
      
      // Store the current focus session ID
      currentFocusSession.current = focusSessionId;
      
      // Only proceed if we have a valid userid
      if (userid) {
        console.log(`Component focused with session ${focusSessionId}. Loading words...`);
        
        // Load words with the current session ID
        loadAllWords(focusSessionId);
        
        // Clear search query when component gains focus
        setSearchQuery("");
      }
      
      // Cleanup function (will run when component loses focus)
      return () => {
        console.log(`Component unfocused for session ${focusSessionId}`);
        // We don't clear the session ID on unfocus to allow manual loading to work
      };
    }, [params.refresh, userid])
  );

  // Load all words from the database (used for both focus events and manual loads)
  const loadAllWords = async (sessionId: string) => {
    // Safety check for userid
    if (!userid) {
      console.error("Cannot load words: userId is not available");
      return;
    }
    
    // If this is a manual load, update the current session
    if (sessionId.startsWith('manual-') || sessionId.startsWith('translation-event-')) {
      console.log(`Setting ${sessionId.startsWith('manual-') ? 'manual' : 'translation event'} load session: ${sessionId}`);
      currentFocusSession.current = sessionId;
    }
    
    setIsLoading(true);
    try {
      console.log(`Loading all words for UserID: ${userid} (session ${sessionId})`);
      const wordList = await wordService.getAllWords(userid);
      
      // For manual loads or translation events, we always accept the results
      const isManualLoad = sessionId.startsWith('manual-');
      const isTranslationEvent = sessionId.startsWith('translation-event-');
      const isCurrentSession = sessionId === currentFocusSession.current;
      
      if (!isManualLoad && !isTranslationEvent && !isCurrentSession) {
        console.log(`Session ${sessionId} is no longer active, discarding results`);
        return;
      }
      
      console.log(`Loaded ${wordList.length} words from database (session ${sessionId})`);
      
      // Convert the database format to your Word type
      const formattedWords: Word[] = wordList.map(item => ({
        wordid: item.wordid,
        word: item.word,
        en_meaning: item.en_meaning,
        ch_meaning: item.ch_meaning,
        part_of_speech: item.part_of_speech,
        wordtime: item.wordtime,
        synced: item.synced,
      }));
      setWords(formattedWords);
    } catch (error) {
      console.error(`Failed to load words (session ${sessionId}):`, error);
      Alert.alert("Error", "Failed to load word list.");
    } finally {
      // For manual loads, translation events, or if this is still the current session, update loading state
      if (sessionId.startsWith('manual-') || sessionId.startsWith('translation-event-') || sessionId === currentFocusSession.current) {
        setIsLoading(false);
      }
    }
  };

  // Regular loadWords for use outside of focus events (like after adding a word or clearing search)
  const loadWords = async () => {
    if (!userid) return;
    
    // Create a unique ID for manual loading
    const loadId = `manual-${Date.now()}`;
    console.log(`Manual load requested: ${loadId}`);
    loadAllWords(loadId);
  };

  // Function to handle search query changes
  const handleSearchQueryChange = (text: string) => {
    setSearchQuery(text);
    
    // If text is empty, immediately reload all words
    if (text.trim() === "" && userid) {
      console.log("Search query cleared, reloading all words");
      loadWords(); // This calls the manual load function
    }
  };

  // Search words - only trigger search when searchQuery changes and userid exists
  useEffect(() => {
    // Skip empty searches - they're handled by handleSearchQueryChange
    if (!userid || searchQuery.trim() === "") return;
    
    const searchWords = async () => {
      setIsLoading(true);
      try {
        console.log(`Searching for "${searchQuery}" with userId: ${userid}`);
        const wordList = await wordService.searchWords(searchQuery, userid);
        console.log(`Found ${wordList.length} words matching "${searchQuery}"`);
        
        const formattedWords: Word[] = wordList.map(item => ({
          wordid: item.wordid,
          word: item.word,
          en_meaning: item.en_meaning,
          ch_meaning: item.ch_meaning,
          part_of_speech: item.part_of_speech,
          wordtime: item.wordtime,
          synced: item.synced,
        }));
        setWords(formattedWords);
      } catch (error) {
        console.error("Failed to search words:", error);
      } finally {
        setIsLoading(false);
      }
    };

    // Add debounce to avoid too many searches
    const timer = setTimeout(() => {
      searchWords();
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery, userid]);

  // Show/hide modal
  const show = () => setVisible(true);
  const hide = () => {
    setVisible(false);
    // Reset the form when closing the modal
    setNewWord("")
  };
  
  const isNetworkAvailable = async (): Promise<boolean> => {
    const state = await NetInfo.fetch();
    return !!state.isConnected && !!state.isInternetReachable;
  };

  // Add new word
  const addNewWord = async () => {
    if (!userid) {
      Alert.alert("Error", "User ID not available. Please log in again.");
      return;
    }
    
    if (!newWord.trim()) {
      Alert.alert("Error", "Word name cannot be empty");
      return;
    }
    
    if (!(/^[A-Za-z]+$/.test(newWord.trim()))) {
      Alert.alert("Error", "Word can only be made up of alphabets");
      return;
    }
    
    try {
      let wordCreate: WordCreate = {
        word: newWord,
        en_meaning: {},
        ch_meaning: [],
        part_of_speech: [],
        translated: 0,
      }
      
      const isOnline = await isNetworkAvailable();
      
      if (isOnline) {
        console.log(`Translating word: ${newWord}`);
        wordCreate = await translateService.translateWordCreate(newWord);
      }
      
      console.log(`Adding word "${newWord}" for user ${userid}`);
      await wordService.addWord(wordCreate, userid);
      
      // Reset form and reload words
      hide();
      loadWords(); // Use manual load here
      
      Alert.alert("Success", `Added word "${newWord}" successfully!`);
    } catch (error) {
      console.error("Failed to add word:", error);
      Alert.alert("Error", "Failed to add the word to database.");
    }
  };
  
  // Sort words
  const sortWords = () => {
    const sorted = [...words].sort((a, b) => {
      if (isSortedAsc) return a.word.localeCompare(b.word)
      else return b.word.localeCompare(a.word)
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
        onChangeText={handleSearchQueryChange}
      />
      <View style={styles.button}>
        <TouchableOpacity onPress={sortWords} style={styles.sortButton}>
          <Text style={styles.sortButtonText}>
            Sort ({isSortedAsc ? "Ascending" : "Descending"})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={show} style={styles.addButton}>
          <Text style={styles.addButtonText}>Add New Word</Text>
        </TouchableOpacity>
      </View>
      
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <Text>Loading words...</Text>
        </View>
      ) : !userid ? (
        <View style={styles.loadingContainer}>
          <Text>User ID not available. Please restart the app.</Text>
        </View>
      ) : (
        <FlatList 
          data={words} 
          renderItem={({ item }) => <PreviewWordlist {...item}/>}
          keyExtractor={item => item.word}
          numColumns={1}
          contentContainerStyle={styles.flatListContent}
          style={{ paddingHorizontal:10 }}
          scrollEnabled={false}
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text>No words found. Add some words to get started!</Text>
            </View>
          }
        />
      )}
      
      <Modal
        visible={visible}
        onRequestClose={() => hide()}
        animationType='fade'
        transparent
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Add New Word</Text>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Input Word Here"
              value={newWord}
              onChangeText={(text) => setNewWord(text)}
            />    
            <View style={styles.modalButtons}>
              <TouchableOpacity onPress={hide} style={styles.cancelButton}>
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={addNewWord} style={styles.confirmButton}>
                <Text style={styles.confirmButtonText}>Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>         
  )
}

export default Home

// Styles remain the same
const styles = StyleSheet.create({
  // Your existing styles...
  // ... all the styles remain unchanged
  loadingContainer: {
    padding: 20,
    alignItems: 'center',
  },
  emptyContainer: {
    padding: 20,
    alignItems: 'center',
  },
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
    maxHeight: '80%',
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
    marginTop: 10,
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
  posTitle: {
    alignSelf: 'flex-start',
    fontWeight: 'bold',
    marginBottom: 10,
  },
  posContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    width: '100%',
    marginBottom: 15,
  },
  posButton: {
    backgroundColor: '#f0f0f0',
    borderRadius: 15,
    paddingHorizontal: 10,
    paddingVertical: 6,
    margin: 4,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  posButtonSelected: {
    backgroundColor: '#007bff',
    borderColor: '#0056b3',
  },
  posButtonText: {
    fontSize: 12,
    color: '#333',
  },
  posButtonTextSelected: {
    color: '#fff',
    fontWeight: 'bold',
  },
});