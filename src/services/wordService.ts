// app/services/wordService.ts

import { Word, WordCreate, WordUpdate } from '../../assets/types/Word';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SQLite from 'expo-sqlite';
import * as translateService from '../services/translateService';
import {getAuthToken} from '../services/authService';
import * as FileSystem from 'expo-file-system';

// Get the database directory

// Database connection - using the new async API
let db: SQLite.SQLiteDatabase | null = null;

// Initialize the database
export const initDatabase = async (userId: string): Promise<SQLite.SQLiteDatabase> => {
  try {
    // Open or create database
    const dbName = `wordbook_${userId}` 
    db = await SQLite.openDatabaseAsync(dbName);
    console.log(`Opening database: ${dbName}`);
    const dbDirectory = `${FileSystem.documentDirectory}SQLite/`;
    console.log("Database directory:", dbDirectory);  
    // Create words table
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS words (
        wordid INTEGER PRIMARY KEY,
        word TEXT UNIQUE NOT NULL,
        en_meaning TEXT,  -- Stored as JSON string
        ch_meaning TEXT,  -- Stored as JSON string
        part_of_speech TEXT,  -- Stored as JSON string
        wordtime TEXT NOT NULL,
        synced INTEGER DEFAULT 0,
        translated INTEGER DEFAULT 0
      );
    `);
    
    // Create sync_queue table
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT NOT NULL,  -- 'add', 'update', 'delete', 'view', 'quiz', etc.
        user_id TEXT NOT NULL,  -- User ID for the operation
        wordid INTEGER,
        word TEXT,
        context TEXT,  -- Optional context/sentence
        data TEXT,  -- JSON string of additional operation data
        timestamp TEXT NOT NULL
      );
    `);

    return db
  } catch (error) {
    console.error('Error initializing database:', error);
    throw error;
  }
};

// Safe JSON parse function that won't throw errors
const safeJsonParse = (jsonString: string | null, defaultValue: any = {}) => {
  if (!jsonString) return defaultValue;
  try {
    return JSON.parse(jsonString);
  } catch (error) {
    console.warn('Error parsing JSON:', error, 'Original string:', jsonString);
    return defaultValue;
  }
};

// Ensure object is properly serialized for storage
const safeJsonStringify = (obj: any, defaultValue: string = '{}') => {
  if (obj === undefined || obj === null) return defaultValue;
  try {
    return JSON.stringify(obj);
  } catch (error) {
    console.warn('Error stringifying object:', error);
    return defaultValue;
  }
};

// Check if network is available
export const isNetworkAvailable = async (): Promise<boolean> => {
  const state = await NetInfo.fetch();
  return !!state.isConnected && !!state.isInternetReachable;
};

// Get all words from local database
export const getAllWords = async (userId: string): Promise<Word[]> => {
  try {
    db = await initDatabase(userId);
    
    const result = await db.getAllAsync<any>('SELECT * FROM words ORDER BY word');
    
    return result.map(row => ({
      wordid: row.wordid,
      word: row.word,
      en_meaning: safeJsonParse(row.en_meaning, {}),
      ch_meaning: safeJsonParse(row.ch_meaning, []),
      part_of_speech: safeJsonParse(row.part_of_speech, []),
      wordtime: row.wordtime,
    }));
  } catch (error) {
    console.error('Error getting all words:', error);
    return []; // Return empty array instead of throwing
  }
};

export const getRecentWords = async (userId: string): Promise<Word[]> => {
  try {
    db = await initDatabase(userId);
    
    const result = await db.getAllAsync<any>('SELECT * FROM words ORDER BY wordtime DESC LIMIT 10');
    
    return result.map(row => ({
      wordid: row.wordid,
      word: row.word,
      en_meaning: safeJsonParse(row.en_meaning),
      ch_meaning: safeJsonParse(row.ch_meaning),
      part_of_speech: safeJsonParse(row.part_of_speech),
      wordtime: row.wordtime,
    }));
  } catch (error) {
    console.error('Error getting recent words:', error);
    return []; // Return empty array instead of throwing
  }
};

// Get a word by ID
export const getWordById = async (wordid: number, userId: string): Promise<Word | null> => {
  try {
    db = await initDatabase(userId);
    
    const result = await db.getAllAsync<any>(
      'SELECT * FROM words WHERE wordid = ?',
      [wordid]
    );
    
    if (result.length === 0) {
      return null;
    }
    
    const row = result[0];
    return {
      wordid: row.wordid,
      word: row.word,
      en_meaning: safeJsonParse(row.en_meaning, {}),
      ch_meaning: safeJsonParse(row.ch_meaning, []),
      part_of_speech: safeJsonParse(row.part_of_speech, []),
      wordtime: row.wordtime,
      synced: row.synced
    };
  } catch (error) {
    console.error('Error getting word by ID:', error);
    return null; // Return null instead of throwing
  }
};

// Search words
export const searchWords = async (query: string,userId: string): Promise<Word[]> => {
  try {
    db = await initDatabase(userId);
    
    
    const result = await db.getAllAsync<any>(
      'SELECT * FROM words WHERE word LIKE ? ORDER BY word',
      [`%${query}%`]
    );
    
    return result.map(row => ({
      wordid: row.wordid,
      word: row.word,
      en_meaning: safeJsonParse(row.en_meaning, {}),
      ch_meaning: safeJsonParse(row.ch_meaning, []),
      part_of_speech: safeJsonParse(row.part_of_speech, []),
      wordtime: row.wordtime,
      synced: row.synced
    }));
  } catch (error) {
    console.error('Error searching words:', error);
    return []; // Return empty array instead of throwing
  }
};

export const searchExactWords = async (query: string,userId: string): Promise<Word | null> => {
  try {
    db = await initDatabase(userId);
    
    const result = await db.getAllAsync<any>(
      'SELECT * FROM words WHERE word = ?',
      [query]
    );
    
    if (result.length === 0) {
      return null;
    }

    const row = result[0];
    return {
      wordid: row.wordid,
      word: row.word,
      en_meaning: safeJsonParse(row.en_meaning, {}),
      ch_meaning: safeJsonParse(row.ch_meaning, []),
      part_of_speech: safeJsonParse(row.part_of_speech, []),
      wordtime: row.wordtime,
    }
  } catch (error) {
    console.error('Error searching exact word:', error);
    return null; // Return null instead of throwing
  }
};

export const wordCount = async (userId: string): Promise<number | null> => {
  try {
    db = await initDatabase(userId);
    
    const result = await db.getFirstAsync<{count: number}>(
      'SELECT COUNT (*) as count FROM words'
    );
    
    return result? result.count : 0
    
  } catch (error) {
    console.error('Error searching exact word:', error);
    return null; // Return null instead of throwing
  }
};

// Add a word to local database
export const addWord = async (wordData: WordCreate, userId: string) => {
  try {
    db = await initDatabase(userId);

    const isOnline = await isNetworkAvailable();
  
    const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
    
    const cursor = await db.getAllAsync<any>('SELECT wordid FROM words WHERE word = ?', [wordData.word])
    if (cursor.length !== 0){   
        throw "already exist"
      }
    const maxID = await db.getAllAsync<any>('SELECT MAX(wordid) as max_id FROM words')
    let wordid = 1
    if (maxID.length !== 0 && maxID[0].max_id !== null){
      wordid = maxID[0].max_id + 1
    }
  // Insert word into words table
    await db.runAsync(
      'INSERT INTO words (wordid, word, en_meaning, ch_meaning, part_of_speech, wordtime, synced, translated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      [
        wordid,
        wordData.word,
        safeJsonStringify(wordData.en_meaning || {}) ,
        safeJsonStringify(wordData.ch_meaning || []),
        safeJsonStringify(wordData.part_of_speech || []),
        currentTime,
        0,
        wordData.translated || 0,
      ]
    );  
    let data = {
        "wordid": wordid,
        "word": wordData.word,
        "en_meaning": wordData.en_meaning,
        "ch_meaning": wordData.ch_meaning,
        "part_of_speech": wordData.part_of_speech,
        "wordtime": currentTime
    }
    
    await db.runAsync(
      'INSERT INTO sync_queue (operation, user_id, wordid, word, context, data, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)',
      ["add", userId, wordid, wordData.word, null, safeJsonStringify(data), currentTime]
    )
    
  } catch (error) {
    console.error('Error adding word:', error);
    throw error;
  }
};

// Update a word
export const updateWord = async (wordid: number, userID: string, updateData: WordUpdate): Promise<boolean> => {
  try {
    db = await initDatabase(userID);
    
    const cursor = await db.getAllAsync<any>("SELECT word FROM words WHERE wordid = ?", [wordid])
    if (cursor.length === 0){
        return false
    }
        
    let word = cursor[0].word
    const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');
    // Build update query
    let updateFields = [];
    let params = [];
    
    if (updateData.part_of_speech !== undefined) {
      updateFields.push('part_of_speech = ?');
      params.push(safeJsonStringify(updateData.part_of_speech, '[]'));
    }

    if (updateData.word !== undefined) {
      updateFields.push('word = ?');
      params.push(updateData.word);
    }

    if (updateData.en_meaning !== undefined) {
      updateFields.push('en_meaning = ?');
      params.push(safeJsonStringify(updateData.en_meaning, '{}'));
    }
    
    if (updateData.ch_meaning !== undefined) {
      updateFields.push('ch_meaning = ?');
      params.push(safeJsonStringify(updateData.ch_meaning, '[]'));
    }
    
    if (updateData.translated !== undefined) {
      updateFields.push('translated = ?');
      params.push(updateData.translated);
    }

    // Add synced status
    updateFields.push('synced = ?');
    params.push(0);

    updateFields.push('wordtime = ?');
    params.push(currentTime);
    
    const updateQuery = `UPDATE words SET ${updateFields.join(', ')} WHERE wordid = ?`;
     
    // Add wordid to params
     params.push(wordid);
    
     // Update the word
    const result = await db.runAsync(updateQuery, params);
    
    if (result.changes === 0) {
      return false;
    }
    
    // Add to sync queue
    await db.runAsync(
      'INSERT INTO sync_queue (operation, user_id, wordid, word,context, data, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [
        'update',
        userID,
        wordid,
        word,
        null,
        safeJsonStringify(updateData),
        currentTime
      ]
    );
    
    return true;
  } catch (error) {
    console.error('Error updating word:', error);
    return false; // Return false instead of throwing
  }
};

// Delete a word
export const deleteWord = async (userId: string, wordid: number): Promise<boolean> => {
  try {
    db = await initDatabase(userId);
    
    // First get the word data for sync queue
    const wordResult = await db.getAllAsync<any>(
      'SELECT word FROM words WHERE wordid = ?',
      [wordid]
    );
    
    if (wordResult.length === 0) {
      return false;
    }
    
    const word = wordResult[0].word;
    
    // Delete the word
    const deleteResult = await db.runAsync(
      'DELETE FROM words WHERE wordid = ?',
      [wordid]
    );
    
    if (deleteResult.changes === 0) {
      return false;
    }
    const currentTime = new Date().toISOString().slice(0, 19).replace('T', ' ');

    const data = {
      "wordid": wordid,
      "word": word,
      "operation": "delete",
      "timestamp": currentTime
  }
    // Add to sync queue
    await db.runAsync(
      'INSERT INTO sync_queue (operation, user_id, wordid, word, context, data, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [
        'delete',
        userId,
        wordid,
        word,
        null,
        safeJsonStringify(data),
        currentTime
      ]
    );
    
    return true;
  } catch (error) {
    console.error('Error deleting word:', error);
    return false; // Return false instead of throwing
  }
};

export const deleteAll = async(userId: string) : Promise<boolean> => {
  try{
    db = await initDatabase(userId);
    await db.execAsync(
      'DROP TABLE IF EXISTS words',
    );
    await db.execAsync(
      'DROP TABLE IF EXISTS sync_queue',
    );
    return true
  }
  catch (error) {
    console.error('Error Deleting database:', error);
    return false;
  }
}

// Sync with server
export const syncWithServer = async (userId: string): Promise<boolean> => {
  try {
    db = await initDatabase(userId);
    
    const isOnline = await isNetworkAvailable();
    
    if (!isOnline) {
      throw new Error('Not Online');
    }

    const token = await getAuthToken();
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    // Get user info from AsyncStorage
    const lastSyncTimestamp = await AsyncStorage.getItem('lastSyncTimestamp') || '';
    
    
    // Get all operations from sync queue
    const operations = await db.getAllAsync<any>(
      'SELECT * FROM sync_queue ORDER BY timestamp'
    );

    if (operations.length === 0){
      console.log('No pending sync');
      return false
    }

    const userid = await AsyncStorage.getItem('userId')
    
    const ops = operations.map(op => ({
      operation: op.operation,
      wordid: String(op.wordid),
      word: op.word || "",
      translation: "",
      context: "",  // Add empty context field
      data: safeJsonParse(op.data,{}),  // Default to empty object
      timestamp: op.timestamp
    }))
    console.log(ops)
    // Prepare payload
    const payload = {
      user_id: userid,
      operations: ops,
      device_id: "",
      last_sync_timestamp: lastSyncTimestamp,
    };
    console.log("Ready to sync to server...")
    
    // Send to server
    const response = await fetch(`${API_BASE_URL}/sync/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      throw new Error('Failed to sync with server');
    }
    
    const syncResponse = await response.json();
    
    
    // Clear sync queue
    await db.runAsync('DELETE FROM sync_queue');
    
    // Mark all words as synced
    await db.runAsync('UPDATE words SET synced = 1');
    
    // Update last sync timestamp
    await AsyncStorage.setItem('lastSyncTimestamp', syncResponse.sync_timestamp);
    
    return true;
  } catch (error) {
    console.error('Error syncing with server:', error);
    return false;
  }
};
export const handleAppCameOnline = async (userID: string): Promise<boolean> => {
  try {
    console.log('App came online, processing pending operations and translations');
    
    // Process translation queue first
    await processTranslationQueue(userID);
    
    // Then process offline operations
    await syncWithServer(userID);
    
    return true
  } catch (error) {
    console.error('Error handling app coming online:', error);
    return false
  }
};

export const processTranslationQueue = async (userID: string): Promise<boolean> => {
  try {
    const isOnline = await isNetworkAvailable();
    
    if (!isOnline) {
      console.log('Cannot process translation queue: offline');
      return false;
    }
    
    db = await initDatabase(userID);
    
    // Find words needing translation
    const pendingWords = await db.getAllAsync<any>(
      'SELECT wordid, word FROM words WHERE translated= 0'
    );
    
    if (pendingWords.length === 0) {
      console.log('No pending translations');
      return true;
    }
    
    console.log(`Processing translations for ${pendingWords.length} words`);
    
    // Process each word
    for (const wordRow of pendingWords) {
      try {
        // Call translation API

        const existingChMeaning = safeJsonParse(wordRow.ch_meaning, []);
        
        const wordCreate: WordCreate = await translateService.translateWordCreate(wordRow.word)
        
        if (existingChMeaning && existingChMeaning.length > 0) {
          // Create a set of existing meanings to avoid duplicates
          const existingMeaningsSet = new Set(existingChMeaning.map(item => 
            typeof item === 'string' ? item : JSON.stringify(item)
          ));
          
          // Add new meanings that don't already exist
          if (wordCreate.ch_meaning && Array.isArray(wordCreate.ch_meaning)) {
            wordCreate.ch_meaning.forEach(newMeaning => {
              const newMeaningStr = typeof newMeaning === 'string' ? newMeaning : JSON.stringify(newMeaning);
              if (!existingMeaningsSet.has(newMeaningStr)) {
                existingChMeaning.push(newMeaning);
              }
            });
          }
          
          // Use the merged meanings
          wordCreate.ch_meaning = existingChMeaning;
        }

        const updateData: WordUpdate = {
          ...wordCreate,
        };

        // Update the word with translation data
        await updateWord(wordRow.wordid, userID, updateData)

        console.log(`Updated translation for word: ${wordRow.word}`);
        
      } catch (error) {
        console.error(`Error processing translation for word ${wordRow.word}:`, error);
      }
    }
    
    return true;
  } catch (error) {
    console.error('Error processing translation queue:', error);
    return false;
  }
};


// Constants
const API_BASE_URL = 'http://192.168.0.118:8000';