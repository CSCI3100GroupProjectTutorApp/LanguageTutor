import { StyleSheet, Text, View, FlatList, TouchableOpacity, Platform, Pressable, TouchableWithoutFeedback, Dimensions, Alert } from 'react-native'
import { Redirect, useLocalSearchParams, Stack, useFocusEffect} from 'expo-router'
import React, { useState, useCallback, useMemo, useEffect, } from 'react'
import { FontAwesome5 } from '@expo/vector-icons'
import { SafeAreaView } from 'react-native-safe-area-context';
import { getAuthToken } from '../../services/authService'
import { Word, WordCreate } from '../../../assets/types/Word'
import * as wordService from '../../services/wordService';
import * as translateService from '../../services/translateService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const text = () => {
  const { text } = useLocalSearchParams<{ text: string }>()
  const decodedText = decodeURIComponent(text).replace('~~~pct~~~', '%')
  const [selectedWordId, setSelectedWordId] = useState<string | null>(null);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [isPopupVisible, setIsPopupVisible] = useState(false);
  const [selectedContent, setSelectedContent] = useState<string>('');
  const [translation, setTranslation] = useState<string>('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [successTranslate, setSuccessTranslate] = useState(false)
  const [userid, setUserid] = useState("")
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const wordsPerPage = 500;
  

  useFocusEffect(
    useCallback(() => {
      const initUserID = async () => {
        try {
          await getUserID()
        } catch (error) {
          console.error("Failed to initialize database:", error);
        }
      };
      initUserID();
      // Return a cleanup function
      return () => {
        // Any cleanup if needed
      };
    }, [text]) // Re-run effect when text changes
  );

  // Define what characters are considered punctuation
  const isPunctuation = useCallback((char: string) => {
    return /[.,;:!?/\"\(\)\[\]\{\}<>]/.test(char);
  }, []);
  
  const getUserID = async () => {
    try {
      const userID = await AsyncStorage.getItem("userid")

      setUserid(userID || "")
    } catch (error) {
      console.error("Failed to load words:", error);
    }
  };

  // Function to translate text
  const translateWord = useCallback(async (word: string) => {
    setIsTranslating(true);
    setSuccessTranslate(false)
    try {
      const accesstoken = await getAuthToken();
      if (!accesstoken) {
        throw new Error('Not authenticated');
      }
      const response = await fetch('http://192.168.0.118:8000/translate/word', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accesstoken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          word: word,
          target_language: "zh-tw",
        })
      })
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
      setSuccessTranslate(true)
      return data.translated_word
    } catch (error) {
      return 'Translation failed';
    }
    finally {
      setIsTranslating(false);
    } 
  }, []);
  
  // Handle word press with translation
  const handleWordPress = useCallback(async (wordId: string, wordContent: string, x: number, y: number) => {
    setSelectedWordId(wordId);
    setSelectedContent(wordContent);
    setPopupPosition({
      x: x - 100,
      y: y - 40,
    });
    setTranslation(''); // Clear previous translation
    setIsPopupVisible(true);
    
    // Get translation
    const translatedText = await translateWord(wordContent);
    setTranslation(translatedText);
  }, [translateWord]);
  
  // Process text into tokens
  const processText = useCallback((text: string) => {
    const paragraphs = text.split('\n');
    let globalWordIndex = 0;
    
    const processedParagraphs = paragraphs.map((paragraph, paragraphIndex) => {
      // Split paragraph content into individual characters
      const chars = paragraph.split('');
      const tokens = [];
      let currentWord = '';
      let inWord = false;
      
      // Process each character
      for (let i = 0; i < chars.length; i++) {
        const char = chars[i];
        
        // Handle spaces
        if (char === ' ') {
          // If we were building a word, add it to tokens
          if (inWord) {
            tokens.push({
              type: 'word',
              text: currentWord,
              wordIndex: globalWordIndex++
            });
            currentWord = '';
            inWord = false;
          }
          tokens.push({ type: 'space', text: ' ' });
        }
        // Handle punctuation
        else if (isPunctuation(char)) {
          // If we were building a word, add it to tokens
          if (inWord) {
            tokens.push({
              type: 'word',
              text: currentWord,
              wordIndex: globalWordIndex++
            });
            currentWord = '';
            inWord = false;
          }
          tokens.push({ type: 'punctuation', text: char });
        }
        // Handle regular characters (part of a word)
        else {
          currentWord += char;
          inWord = true;
        }
      }
      
      // Add any remaining word
      if (inWord) {
        tokens.push({
          type: 'word',
          text: currentWord,
          wordIndex: globalWordIndex++
        });
      }
      
      return {
        id: `p-${paragraphIndex}`,
        tokens: tokens
      };
    });
    
    return {
      paragraphs: processedParagraphs,
      totalWords: globalWordIndex
    };
  }, [isPunctuation]);
  
  // Process the text into tokens
  const processedText = useMemo(() => {
    return processText(decodedText);
  }, [decodedText, processText]);
  
  // Calculate total pages
  useEffect(() => {
    const totalPagesCount = Math.ceil(processedText.totalWords / wordsPerPage);
    setTotalPages(Math.max(1, totalPagesCount));
  }, [processedText, wordsPerPage]);
  
  // Get content for current page
  const currentPageContent = useMemo(() => {
    const startWordIndex = (currentPage - 1) * wordsPerPage;
    const endWordIndex = startWordIndex + wordsPerPage;
    
    // Mark which tokens should be visible
    const visibleParagraphs = processedText.paragraphs.map(paragraph => {
      const visibleTokens = [];
      let includeNextTokens = false;
      
      for (let i = 0; i < paragraph.tokens.length; i++) {
        const token = paragraph.tokens[i];
        
        if (token.type === 'word') {
          // Check if this word is within our page range
          if (token.wordIndex >= startWordIndex && token.wordIndex < endWordIndex) {
            visibleTokens.push({
              ...token,
              id: `${paragraph.id}-token-${i}`
            });
            includeNextTokens = true;
          } else {
            includeNextTokens = false;
          }
        } 
        // Include spaces and punctuation that follow a visible word
        else if (includeNextTokens) {
          visibleTokens.push({
            ...token,
            id: `${paragraph.id}-token-${i}`
          });
        }
      }
      
      return {
        id: paragraph.id,
        tokens: visibleTokens
      };
    }).filter(p => p.tokens.length > 0);
    
    return visibleParagraphs;
  }, [processedText, currentPage, wordsPerPage]);
  
  // Position adjustments for popup
  const x_axisCorrection = useCallback((Position: { x: number }) => {
    const screenWidth = Dimensions.get('window').width;
    if (Position.x > screenWidth - 210) {
      return screenWidth - 230;
    } else if (Position.x < 20) {
      return 20;
    }
    return Position.x;
  }, []);
  
  const y_axisCorrection = useCallback((Position: { y: number }) => {
    const screenHeight = Dimensions.get('window').height;
    if (Position.y > screenHeight - 150) {
      return Position.y - 100;
    }
    return Position.y;
  }, []);
  
  // Close popup
  const closePopup = useCallback(() => {
    setIsPopupVisible(false);
    setSelectedWordId(null);
    setTranslation('');
  }, []);
  
  // Render token based on its type
  const renderToken = useCallback((token, index) => {
    switch (token.type) {
      case 'word':
        return (
          <Pressable
            key={token.id}
            onPress={(event) => {
              const { pageX, pageY } = event.nativeEvent;
              handleWordPress(token.id, token.text, pageX, pageY);
            }}
          >
            <Text
              style={[
                styles.wordText,
                selectedWordId === token.id && styles.highlightedWord
              ]}
            >
              {token.text}
            </Text>
          </Pressable>
        );
      case 'space':
        return <Text key={`space-${index}`} style={styles.spaceText}>{token.text}</Text>;
      case 'punctuation':
        return <Text key={`punct-${index}`} style={styles.punctuationText}>{token.text}</Text>;
      default:
        return null;
    }
  }, [selectedWordId, handleWordPress]);
  
  // Render paragraph
  const renderParagraph = useCallback(({ item }) => {
    if (item.tokens.length === 0) return null;
    
    return (
      <View style={styles.paragraphContainer}>
        <View style={styles.lineContainer}>
          {item.tokens.map((token, index) => renderToken(token, index))}
        </View>
      </View>
    );
  }, [renderToken]);
  
  // Pagination handlers
  const goToNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
      setSelectedWordId(null);
      setIsPopupVisible(false);
    }
  }, [currentPage, totalPages]);
  
  const goToPrevPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
      setSelectedWordId(null);
      setIsPopupVisible(false);
    }
  }, [currentPage]);
  const addWord = async() => {
    
    console.log(selectedContent)
    let cleanedWord = selectedContent.replace(/(?!\B['’-]\B)[^\w'’-]+/g, '');

    // Check if the cleaned word contains any alphabetic characters
    const containsAlphabet = /[a-zA-Z]/.test(cleanedWord);
    
    if (!cleanedWord || !containsAlphabet) {
      Alert.alert("Cannot be added. Please select other");
      return;
    }
    else{
      try {
            const wordCreate: WordCreate = await translateService.translateWordCreate(cleanedWord)
            await wordService.addWord(
              wordCreate,
              userid
            ) 
            Alert.alert("Success", `Added word "${cleanedWord}" successfully!`);
          } catch (error) {
            console.error("Failed to add word:", error);
            Alert.alert("Error", "Failed to add the word to database.");
          }
    }
  }
  
  return (
    <SafeAreaView style={styles.container}>
      <Stack.Screen options={{
        title: "Translation",
        headerTitleAlign: 'center',
        
      }} />
      <FlatList
        data={currentPageContent}
        keyExtractor={(item) => item.id}
        renderItem={renderParagraph}
        ItemSeparatorComponent={() => <View style={styles.paragraphSeparator} />}
        initialNumToRender={10}
        removeClippedSubviews={true}
      />
      
      {/* Pagination controls */}
      {totalPages > 1 && (
        <View style={styles.paginationContainer}>
          <TouchableOpacity 
            style={[styles.pageButton, currentPage === 1 && styles.disabledButton]} 
            onPress={goToPrevPage}
            disabled={currentPage === 1}
          >
            <Text style={styles.pageButtonText}>Previous</Text>
          </TouchableOpacity>
          
          <View style={styles.pageIndicatorContainer}>
            <Text style={styles.pageIndicator}>
              {currentPage} / {totalPages}
            </Text>
          </View>
          
          <TouchableOpacity 
            style={[styles.pageButton, currentPage === totalPages && styles.disabledButton]} 
            onPress={goToNextPage}
            disabled={currentPage === totalPages}
          >
            <Text style={styles.pageButtonText}>Next</Text>
          </TouchableOpacity>
        </View>
      )}
      
      {/* Popup for selected word */}
      {isPopupVisible && (
        <View
          style={[
            styles.popup,
            {
              top: y_axisCorrection(popupPosition),
              left: x_axisCorrection(popupPosition),
            },
          ]}
        >
          <View style={styles.popupTextContainer}>
            {isTranslating ?  <Text style={styles.popupText}>Translating...</Text> : 
              successTranslate ? <Text style={styles.popupSuccessText}>{translation}</Text> : 
              <Text style={styles.popupText}>Translation Failed</Text> }
            <Text style={styles.selectedWordText}>{selectedContent}</Text>
          </View>
          <TouchableOpacity style={styles.addButton} onPress={addWord}>
            <Text style={styles.addButtonText}>Add</Text>
          </TouchableOpacity>
        </View>
      )}
      
      {/* Overlay to close popup */}
      {isPopupVisible && (
        <TouchableWithoutFeedback onPress={closePopup}>
          <View style={styles.overlay} />
        </TouchableWithoutFeedback>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f9f9f9',
  },
  paragraphContainer: {
    marginVertical: 4,
  },
  lineContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'baseline',
  },
  paragraphSeparator: {
    height: 10,
  },
  wordText: {
    fontSize: 22,
    color: '#333',
  },
  spaceText: {
    fontSize: 22,
    color: '#333',
  },
  punctuationText: {
    fontSize: 22,
    color: '#333',
  },
  highlightedWord: {
    backgroundColor: 'yellow',
    borderRadius: 4,
  },
  popup: {
    position: 'absolute',
    flexDirection: 'row',
    width: 225,
    height: 70,
    backgroundColor: 'black',
    borderRadius: 8,
    zIndex: 10,
    alignItems: 'center',
    padding: 8,
    ...(Platform.OS === 'android' ? { elevation: 5 } : { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, shadowRadius: 3 }),
  },
  popupText: {
    fontSize: 15,
    color: 'white',
    textAlign: 'center',
  },
  popupSuccessText: {
    fontSize: 20,
    color: 'white',
    textAlign: 'center',
  },
  selectedWordText: {
    fontSize: 14,
    color: '#cccccc',
    textAlign: 'center',
    marginTop: 4,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'transparent',
    zIndex: 5,
  },
  addButton: {
    backgroundColor: 'green',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    width: 60,
    height: 40,
    marginLeft: 10,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  popupTextContainer: {
    flex: 1,
    marginRight: 10,
  },
  paginationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
    marginTop: 10,
  },
  pageButton: {
    backgroundColor: '#0066cc',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 5,
    width: 100,
    alignItems: 'center',
  },
  pageButtonText: {
    color: 'white',
    fontWeight: '600',
  },
  pageIndicatorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pageIndicator: {
    fontSize: 16,
    color: '#333',
    fontWeight: '500',
  },
  disabledButton: {
    backgroundColor: '#cccccc',
  },
});

export default text;