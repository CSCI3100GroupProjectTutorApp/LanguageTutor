import { ScrollView, FlatList, StyleSheet, Text, View, BackHandler, Alert, DeviceEventEmitter } from 'react-native'
import React, {useEffect, useState, useCallback, useRef} from 'react'
import PreviewWordlist from '../../components/Preview-Wordlist'
import { Link, useFocusEffect } from "expo-router";
import {HomeHeader} from '../../components/Home-header'
import { Word } from '../../../assets/types/Word'
import * as wordService from '../../services/wordService';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TRANSLATION_COMPLETED_EVENT } from '../../../assets/context/NetworkSyncProvider';

const Home = () => {
  const [words, setWords] = useState<Word[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userid, setUserid] = useState("");
  const loadingSessionRef = useRef<string | null>(null);
  
  // Load user ID when component mounts
  useEffect(() => {
    const loadUserId = async () => {
      try {
        // Try to get from both possible keys
        const id = await AsyncStorage.getItem("userid")
        
        console.log("Loaded userId in Home Index:", id);
        
        if (id) {
          setUserid(id);
          // Also ensure it's saved under both keys for consistency
          await AsyncStorage.setItem("userId", id);
        } else {
          console.error("No user ID found in storage");
          Alert.alert(
            "Error", 
            "User ID not found. Please log in again.",
            [{ text: "OK" }]
          );
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
        console.log('TRANSLATION EVENT: Translation completed, reloading recent words...');
        if (userid) {
          // Create a session ID for this load
          const sessionId = `translation-event-${Date.now()}`;
          loadingSessionRef.current = sessionId;
          loadWordsWithSession(sessionId);
        }
      }
    );
    
    return () => {
      subscription.remove();
    };
  }, [userid]);

  // Load word when name changes or userid becomes available
  useFocusEffect(
    useCallback(() => {
      // Only load word if we have userid
      if (userid) {
        const sessionId = `focus-${Date.now()}`;
        loadingSessionRef.current = sessionId;
        loadWordsWithSession(sessionId);
      }
    }, [userid]) // Add userid as dependency so it reloads when userid changes
  );
  
  // Handle back button only on this screen
  useFocusEffect(
    useCallback(() => {
      // This function will be called when the back button is pressed
      const backAction = () => {
        Alert.alert('Exit App', 'Do you want to exit the app?', [
          {
            text: 'Cancel',
            onPress: () => null,
            style: 'cancel',
          },
          {
            text: 'Yes',
            onPress: () => BackHandler.exitApp(),
          },
        ]);
        return true; // Prevent default behavior (exiting the app)
      };

      // Add the event listener
      const backHandler = BackHandler.addEventListener(
        'hardwareBackPress',
        backAction
      );

      // Return a cleanup function
      return () => {
        // This will be called when the screen loses focus
        backHandler.remove();
      };
    }, [])
  );
  
  // Load words with session tracking
  const loadWordsWithSession = async (sessionId: string) => {
    setIsLoading(true);
    try {
      console.log(`Loading recent words for UserID: ${userid} (session ${sessionId})`);
      const wordList = await wordService.getRecentWords(userid);
      
      // Only update state if this is still the active session
      if (sessionId !== loadingSessionRef.current) {
        console.log(`Session ${sessionId} is no longer active, discarding results`);
        return;
      }
      
      console.log(`Loaded ${wordList.length} recent words from database (session ${sessionId})`);
      
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
      if (sessionId === loadingSessionRef.current) {
        setIsLoading(false);
      }
    }
  };

  // Legacy load words function - now calls the session-aware version
  const loadWords = () => {
    if (!userid) return;
    
    const sessionId = `manual-${Date.now()}`;
    loadingSessionRef.current = sessionId;
    loadWordsWithSession(sessionId);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <FlatList 
        data={words} 
        renderItem={({ item }) => (
          <PreviewWordlist 
            word={item.word}
            part_of_speech={item.part_of_speech}
            ch_meaning={item.ch_meaning}
            wordid={item.wordid}
            en_meaning={item.en_meaning}
            synced={item.synced}
            wordtime={item.wordtime}
          />
        )}
        keyExtractor={item => item.word}
        numColumns={1}
        ListHeaderComponent={HomeHeader}
        contentContainerStyle={styles.flatListContent}
        style={{ paddingHorizontal:10, paddingVertical:5 }}
        scrollEnabled={false}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.emptyContainer}>
              <Text>Loading words...</Text>
            </View>
          ) : (
            <View style={styles.emptyContainer}>
              <Text>No recent words found. Add some words to get started!</Text>
            </View>
          )
        }
      />
      <Link href="/myWordlist" style={styles.link}>More</Link>
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
    fontSize: 24,
    color: "blue",
    textAlign: "center",
    paddingBottom: 20,
  },
  container: {
    padding: 10,
    backgroundColor: "#f9f9f9",
  },
  emptyContainer: {
    padding: 20,
    alignItems: 'center',
  },
})