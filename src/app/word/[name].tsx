import { StyleSheet, Text, View, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native'
import { useLocalSearchParams, Stack, useRouter, useFocusEffect } from 'expo-router'
import React, { useState, useEffect, useCallback } from "react";
import { FontAwesome5, AntDesign, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { Word, WordUpdate } from '../../../assets/types/Word'
import * as wordService from '../../services/wordService';
import * as translateService from '../../services/translateService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const WordDetail = () => {
  const { name } = useLocalSearchParams<{ name: string }>()
  const router = useRouter();
  const [word, setWord] = useState<Word | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [meaningsByPos, setMeaningsByPos] = useState<Record<string, string[]>>({});
  const [isEditMode, setIsEditMode] = useState(false);
  const [editDefinitions, setEditDefinitions] = useState<{[key: string]: string[]}>({});
  const [newDefinitions, setNewDefinitions] = useState<{[key: string]: string}>({});
  const [editChMeanings, setEditChMeanings] = useState<string[]>([]);
  const [newChMeaning, setNewChMeaning] = useState<string>("");
  const [userid, setUserid] = useState("");

  // Load word whenever the component gets focus or name changes
  useEffect(() => {
    const loadUserId = async () => {
      try {
        // Try to get from both possible keys
        const id = await AsyncStorage.getItem("userid")
        
        console.log("Loaded userId in WordDetail:", id);
        
        if (id) {
          setUserid(id);
          // Also ensure it's saved under both keys for consistency
          await AsyncStorage.setItem("userId", id);
        } else {
          console.error("No user ID found in storage");
          Alert.alert(
            "Error", 
            "User ID not found. Please log in again.",
            [{ text: "OK", onPress: () => router.replace("/login") }]
          );
        }
      } catch (error) {
        console.error("Failed to load user ID:", error);
        Alert.alert("Error", "Failed to access user data. Please restart the app.");
      }
    };
    
    loadUserId();
  }, []);

  // Load word when name changes or userid becomes available
  useFocusEffect(
    useCallback(() => {
      // Only load word if we have both name and userid
      if (name && userid) {
        console.log(`Loading word '${name}' for user ${userid}`);
        loadWord();
      }
    }, [name, userid]) // Add userid as dependency so it reloads when userid changes
  );
  
  // Load word from the database
  const loadWord = async () => {
    setIsLoading(true);
    try {
      if (!name) return;
      const foundWord = await wordService.searchExactWords(name, userid)
      setWord(foundWord)
      if (foundWord) {
        // Process Chinese meanings
        if (Array.isArray(foundWord.ch_meaning)) {
          setEditChMeanings([...foundWord.ch_meaning]);
        } else if (typeof foundWord.ch_meaning === 'string') {
          // If it's a string, split by commas and trim
          setEditChMeanings(
            foundWord.ch_meaning
              .split(/[，]/)
              .map(m => m.trim())
              .filter(m => m.length > 0)
          );
        } else {
          setEditChMeanings([]);
        }
      }
      
      // Process and organize meanings
      processMeanings(foundWord);
      
    } catch (error) {
      console.error("Failed to load word:", error);
    } finally {
      setIsLoading(false);
    }
  };

  
  // Process and organize meanings by part of speech
  const processMeanings = (wordData: Word) => {
    if (!wordData) return;
    
    const organizedMeanings: Record<string, string[]> = {};
    
    // Handle case where en_meaning is an object with part of speech keys
    if (typeof wordData.en_meaning === 'object' && wordData.en_meaning !== null && !Array.isArray(wordData.en_meaning)) {
      // Process each part of speech
      Object.entries(wordData.en_meaning).forEach(([pos, meaning]) => {
        if (typeof meaning === 'string') {
          // Split meanings by commas
          const splitMeanings = meaning
            .split(/[,]/)
            .map(m => m.trim())
            .filter(m => m.length > 0);
          
          organizedMeanings[pos] = splitMeanings;
        } else if (Array.isArray(meaning)) {
          // If meaning is already an array, flatten it and split by commas
          const flattenedMeanings = meaning.flatMap(m => 
            typeof m === 'string' 
              ? m.split(/[,]/).map(part => part.trim()).filter(part => part.length > 0)
              : []
          );
          organizedMeanings[pos] = flattenedMeanings;
        }
      });
    }

    setMeaningsByPos(organizedMeanings);
    
    // Initialize edit definitions and new definitions
    setEditDefinitions({...organizedMeanings});
    
    // Initialize empty new definition fields
    const newDefs: {[key: string]: string} = {};
    if (wordData.part_of_speech) {
      wordData.part_of_speech.forEach(pos => {
        newDefs[pos] = "";
      });
    }
    setNewDefinitions(newDefs);
  };

  // Toggle edit mode
  const toggleEditMode = () => {
    if (isEditMode) {
      // We're exiting edit mode, so save changes
      saveChanges();
    } else {
      // We're entering edit mode
      if (word) {
        setEditDefinitions({...meaningsByPos});
        
        // Set Chinese meanings for editing
        if (Array.isArray(word.ch_meaning)) {
          setEditChMeanings([...word.ch_meaning]);
        } else if (typeof word.ch_meaning === 'string') {
          setEditChMeanings(
            word.ch_meaning
              .split(/[，]/)
              .map(m => m.trim())
              .filter(m => m.length > 0)
          );
        } else {
          setEditChMeanings([]);
        }
        
        setNewChMeaning("");
        
        // Initialize empty new definition fields
        const newDefs: {[key: string]: string} = {};
        if (word.part_of_speech) {
          word.part_of_speech.forEach(pos => {
            newDefs[pos] = "";
          });
        }
        setNewDefinitions(newDefs);
      }
    }
    
    setIsEditMode(!isEditMode);
  };

  // Handle changes to definition text
  const handleDefinitionChange = (pos: string, index: number, text: string) => {
    setEditDefinitions(prev => {
      const updated = {...prev};
      if (!updated[pos]) updated[pos] = [];
      updated[pos][index] = text;
      return updated;
    });
  };

  // Handle changes to Chinese meaning
  const handleChMeaningChange = (index: number, text: string) => {
    setEditChMeanings(prev => {
      const updated = [...prev];
      updated[index] = text;
      return updated;
    });
  };

  // Handle changes to new definition text
  const handleNewDefinitionChange = (pos: string, text: string) => {
    setNewDefinitions(prev => ({...prev, [pos]: text}));
  };

  // Add a new definition
  const addDefinition = (pos: string) => {
    if (!newDefinitions[pos] || !newDefinitions[pos].trim()) {
      Alert.alert("Error", "Please enter a definition first");
      return;
    }
    
    setEditDefinitions(prev => {
      const updated = {...prev};
      if (!updated[pos]) updated[pos] = [];
      updated[pos] = [...updated[pos], newDefinitions[pos].trim()];
      return updated;
    });
    
    // Clear the input
    setNewDefinitions(prev => ({...prev, [pos]: ""}));
  };

  // Add a new Chinese meaning
  const addChMeaning = () => {
    if (!newChMeaning || !newChMeaning.trim()) {
      Alert.alert("Error", "Please enter a Chinese meaning first");
      return;
    }
    
    setEditChMeanings(prev => [...prev, newChMeaning.trim()]);
    
    // Clear the input
    setNewChMeaning("");
  };

  // Remove a definition
  const removeDefinition = (pos: string, index: number) => {
    setEditDefinitions(prev => {
      const updated = {...prev};
      
      // Remove the definition at the specified index
      if (updated[pos] && updated[pos].length > 0) {
        updated[pos] = updated[pos].filter((_, i) => i !== index);
        
        // If this was the last definition for this part of speech, remove the entry
        if (updated[pos].length === 0) {
          delete updated[pos];
        }
      }
      
      return updated;
    });
  };

  // Remove a Chinese meaning
  const removeChMeaning = (index: number) => {
    setEditChMeanings(prev => prev.filter((_, i) => i !== index));
  };

  // Convert edited definitions to en_meaning format for saving
  const formatDefinitionsForSave = () => {
    const result: {[key: string]: string} = {};
    
    Object.entries(editDefinitions).forEach(([pos, definitions]) => {
      // Join definitions with commas for storage
      result[pos] = definitions.join(', ');
    });
    
    return result;
  };

  // Save all changes
  const saveChanges = async () => {
    if (!word) return;

    // Check if at least one definition exists
    const hasDefinitions = Object.values(editDefinitions).some(defs => defs.length > 0);
    if (!hasDefinitions) {
      Alert.alert("Error", "Please add at least one definition");
      return;
    }

    try {
      // Format the parts of speech
      const partsOfSpeech = Object.keys(editDefinitions);
      
      // Create update data
      const wordUpdate: WordUpdate = {
        word: word.word, // Keeping the original word (not editable)
        en_meaning: formatDefinitionsForSave(),
        part_of_speech: partsOfSpeech,
        ch_meaning: editChMeanings // Using the array of Chinese meanings
      };
      
      const success = await wordService.updateWord(word.wordid, userid, wordUpdate);
      if (success) {
        Alert.alert(
          "Success", 
          `Updated word "${word.word}" successfully!`,
          [
            { 
              text: "OK", 
              onPress: () => {
                // Reload the current word
                loadWord();
              } 
            }
          ]
        );
      } else {
        Alert.alert("Error", "Failed to update the word.");
        // Stay in edit mode if update failed
        setIsEditMode(true);
      }
    } catch (error) {
      console.error("Failed to update word:", error);
      Alert.alert("Error", "Failed to update the word in the database.");
      // Stay in edit mode if update failed
      setIsEditMode(true);
    }
  };

  // Delete word
  const deleteWord = () => {
    if (!word) return;
    
    Alert.alert(
      "Delete Word",
      `Are you sure you want to delete "${word.word}"?`,
      [
        {
          text: "Cancel",
          style: "cancel"
        },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              const success = await wordService.deleteWord(userid, word.wordid);
              if (success) {
                Alert.alert(
                  "Success", 
                  `Deleted word "${word.word}" successfully!`,
                  [
                    { 
                      text: "OK", 
                      onPress: () => {
                        // Use router.back() to go back to the previous screen
                        // Set a param that tells the wordlist page to refresh
                        router.replace({
                          pathname: "../(tabs)/myWordlist",
                          params: { refresh: Date.now().toString() }
                        });
                      }
                    }
                  ]
                );
              } else {
                Alert.alert("Error", "Failed to delete the word.");
              }
            } catch (error) {
              console.error("Failed to delete word:", error);
              Alert.alert("Error", "Failed to delete the word from the database.");
            }
          }
        }
      ]
    );
  };

  const cancelEdit = () => {
    setIsEditMode(false);
    // Reset to original values
    if (word) {
      // Reset Chinese meanings
      if (Array.isArray(word.ch_meaning)) {
        setEditChMeanings([...word.ch_meaning]);
      } else if (typeof word.ch_meaning === 'string') {
        setEditChMeanings(
          word.ch_meaning
            .split(/[，]/)
            .map(m => m.trim())
            .filter(m => m.length > 0)
        );
      } else {
        setEditChMeanings([]);
      }
      
      // Reset definitions
      setEditDefinitions({...meaningsByPos});
    }
  }

  return (
    <View style={styles.container}>
      <Stack.Screen 
        options= {{
          title: isEditMode ? "Edit Word" : "Definition", 
          headerTitleAlign: 'left',
          headerRight: () => (
            <View style={{ flexDirection: 'row' }}>
              <TouchableOpacity
                onPress={toggleEditMode}
                style={{
                  marginRight: 15,
                  padding: 10,
                  borderRadius: 5,
                }}
              >
                {isEditMode ? (
                  <MaterialCommunityIcons name='content-save-edit-outline' size={28} color='blue' />
                ) : (
                  <FontAwesome5 name='edit' size={22} color='blue' />
                )}
              </TouchableOpacity>
              {!isEditMode && (
                <TouchableOpacity
                  onPress={deleteWord}
                  style={{
                    marginRight: 10,
                    padding: 10,
                    borderRadius: 5,
                  }}
                >
                  <AntDesign name="minuscircleo" size={23} color="red" />
                </TouchableOpacity>
              )}
            </View>
          ),
        }}
      />
      
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <Text>Loading word...</Text>
        </View>
      ) : !word ? (
        <View style={styles.loadingContainer}>
          <Text>Word not found</Text>
        </View>
      ) : (
        <ScrollView 
          contentContainerStyle={styles.scrollContainer} 
          showsVerticalScrollIndicator={false}
        >
          {/* Word title and Chinese meaning */}
          <View style={styles.headerContainer}>
            {/* Word title - not editable */}
            <Text style={styles.title}>{word.word}</Text>
            
            {/* Chinese meaning - displayed in original layout when not in edit mode */}
            {!isEditMode && (
              <Text style={styles.chMeaning}>
                {Array.isArray(word.ch_meaning) && word.ch_meaning.length > 0
                  ? word.ch_meaning.join('，')
                  : typeof word.ch_meaning === 'string' ? word.ch_meaning : ''}
              </Text>
            )}
          </View>
          
          {/* Chinese Meanings Edit Section - only visible in edit mode */}
          {isEditMode && (
            <View style={styles.chMeaningEditSection}>
              <Text style={styles.sectionLabel}>Chinese Meanings:</Text>
              
              {/* Editable Chinese meanings */}
              {editChMeanings.map((meaning, index) => (
                <View key={`ch-${index}`} style={styles.editDefinitionContainer}>
                  <TextInput
                    style={styles.definitionInput}
                    value={meaning}
                    onChangeText={(text) => handleChMeaningChange(index, text)}
                  />
                  <TouchableOpacity
                    style={styles.removeButton}
                    onPress={() => removeChMeaning(index)}
                  >
                    <AntDesign name="minuscircle" size={20} color="red" />
                  </TouchableOpacity>
                </View>
              ))}
              
              {/* Add new Chinese meaning field */}
              <View style={styles.addDefinitionContainer}>
                <TextInput
                  style={styles.addDefinitionInput}
                  placeholder="Add new Chinese meaning..."
                  value={newChMeaning}
                  onChangeText={setNewChMeaning}
                />
                <TouchableOpacity
                  style={styles.addButton}
                  onPress={addChMeaning}
                >
                  <Ionicons name="add-circle" size={24} color="green" />
                </TouchableOpacity>
              </View>
            </View>
          )}
          
          {/* Horizontal divider */}
          <View style={styles.divider} />
          
          {/* Display meanings by part of speech */}
          {word.part_of_speech && word.part_of_speech.map((pos, posIndex) => (
            <View key={pos} style={styles.sectionContainer}>
              <Text style={styles.partOfSpeech}>{pos}</Text>
              
              {isEditMode ? (
                // Edit mode: show editable fields for existing definitions
                <>
                  {editDefinitions[pos] && editDefinitions[pos].map((def, index) => (
                    <View key={`edit-${pos}-${index}`} style={styles.editDefinitionContainer}>
                      <TextInput
                        style={styles.definitionInput}
                        value={def}
                        onChangeText={(text) => handleDefinitionChange(pos, index, text)}
                        multiline
                      />
                      <TouchableOpacity
                        style={styles.removeButton}
                        onPress={() => removeDefinition(pos, index)}
                      >
                        <AntDesign name="minuscircle" size={20} color="red" />
                      </TouchableOpacity>
                    </View>
                  ))}
                  
                  {/* Add new definition field */}
                  <View style={styles.addDefinitionContainer}>
                    <TextInput
                      style={styles.addDefinitionInput}
                      placeholder="Add new definition..."
                      value={newDefinitions[pos] || ""}
                      onChangeText={(text) => handleNewDefinitionChange(pos, text)}
                      multiline
                    />
                    <TouchableOpacity
                      style={styles.addButton}
                      onPress={() => addDefinition(pos)}
                    >
                      <Ionicons name="add-circle" size={24} color="green" />
                    </TouchableOpacity>
                  </View>
                </>
              ) : (
                // View mode: display bullet-pointed meanings
                <>
                  {meaningsByPos[pos] && meaningsByPos[pos].length > 0 ? (
                    meaningsByPos[pos].map((meaning, mIndex) => (
                      <View key={`${pos}-${mIndex}`} style={styles.meaningContainer}>
                        <Text style={styles.bullet}>•</Text>
                        <Text style={styles.enMeaning}>{meaning}</Text>
                      </View>
                    ))
                  ) : (
                    // Fallback if no meanings found for this part of speech
                    <View style={styles.meaningContainer}>
                      <Text style={styles.bullet}>•</Text>
                      <Text style={styles.enMeaning}>No definition available</Text>
                    </View>
                  )}
                </>
              )}
              
              {/* Add divider except after the last section */}
              {posIndex < word.part_of_speech.length - 1 && (
                <View style={[styles.divider, {marginTop: 16}]} />
              )}
            </View>
          ))}
          
          {/* Cancel button in edit mode */}
          {isEditMode && (
            <TouchableOpacity 
              style={styles.cancelButton}
              onPress={cancelEdit}
            >
              <Text style={styles.cancelButtonText}>Cancel</Text>
            </TouchableOpacity>
          )}
        </ScrollView>
      )}
    </View>
  )
}

export default WordDetail

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  headerContainer: {
    padding: 16,
    marginBottom: 8,
  },
  title: {
    fontSize: 40,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  chMeaning: {
    fontSize: 28,
    marginTop: 4,
    color: "#333",
  },
  chMeaningEditSection: {
    padding: 16,
    paddingTop: 0,
  },
  sectionLabel: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
    color: '#555',
  },
  sectionContainer: {
    padding: 16,
  },
  partOfSpeech: {
    fontSize: 24,
    marginBottom: 16,
    fontStyle: 'italic',
    color: "#555",
  },
  meaningContainer: {
    flexDirection: 'row',
    marginBottom: 12,
    paddingLeft: 8,
    alignItems: 'flex-start',
  },
  bullet: {
    fontSize: 20,
    marginRight: 10,
    lineHeight: 24,
  },
  enMeaning: {
    fontSize: 18,
    flex: 1,
    lineHeight: 24,
  },
  divider: {
    height: 1,
    backgroundColor: '#EAEAEA',
    marginHorizontal: 16,
  },
  scrollContainer: {
    paddingVertical: 10,
    backgroundColor: "white",
  },
  loadingContainer: {
    flex: 1,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Edit mode styles
  editDefinitionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    paddingHorizontal: 8,
  },
  definitionInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 5,
    padding: 10,
    fontSize: 16,
    minHeight: 40,
  },
  removeButton: {
    marginLeft: 10,
    padding: 5,
  },
  addDefinitionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 16,
    paddingHorizontal: 8,
  },
  addDefinitionInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#28a745',
    borderRadius: 5,
    padding: 10,
    fontSize: 16,
    minHeight: 40,
  },
  addButton: {
    marginLeft: 10,
    padding: 5,
  },
  cancelButton: {
    backgroundColor: '#f8f9fa',
    margin: 16,
    padding: 12,
    borderRadius: 5,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#dc3545',
  },
  cancelButtonText: {
    color: '#dc3545',
    fontSize: 16,
    fontWeight: 'bold',
  },
})