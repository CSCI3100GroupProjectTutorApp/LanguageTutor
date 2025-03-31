import sqlite3
import datetime
import os
import asyncio
import json
from typing import List, Dict, Any, Optional, Union

class WordStorage:
    def __init__(self, db_path="word_data.db"):
        """Initialize the SQLite storage for words.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.sync_queue = []  # Queue for pending sync operations
        self.initialize_db()
        
    def initialize_db(self):
        """Create tables if they don't exist."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create words table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            wordid INTEGER PRIMARY KEY,
            word TEXT UNIQUE NOT NULL,
            en_meaning TEXT,
            ch_meaning TEXT,
            part_of_speech TEXT,  -- Stored as JSON string
            wordtime TEXT NOT NULL,
            synced INTEGER DEFAULT 0  -- 0: not synced, 1: synced
        )
        ''')
        
        # Create sync_queue table for tracking operations to sync
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,  -- 'add', 'update', 'delete'
            wordid INTEGER,
            word TEXT,
            data TEXT,  -- JSON string of the operation data
            timestamp TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_word(self, word, en_meaning, ch_meaning, part_of_speech) -> int:
        """
        Add a new word to the local database
        
        Args:
            word: The word to add
            en_meaning: English meaning/definition
            ch_meaning: Chinese meaning/translation
            part_of_speech: List of parts of speech (e.g., ["noun", "verb"])
            
        Returns:
            wordid: The ID of the newly created word
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if word already exists
            cursor.execute("SELECT wordid FROM words WHERE word = ?", (word,))
            existing_word = cursor.fetchone()
            if existing_word:
                print(f"Word '{word}' already exists with ID {existing_word[0]}")
                return existing_word[0]
                
            # Find the maximum word ID
            cursor.execute("SELECT MAX(wordid) FROM words")
            result = cursor.fetchone()
            if result[0] is not None:
                wordid = result[0] + 1
            else:
                wordid = 1  # Start with ID 1 if table is empty

            # Get current timestamp
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Convert part_of_speech list to JSON string
            pos_json = json.dumps(part_of_speech)
            
            # Add a new word to the table
            cursor.execute(
                "INSERT INTO words (wordid, word, en_meaning, ch_meaning, part_of_speech, wordtime, synced) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (wordid, word, en_meaning, ch_meaning, pos_json, current_time, 0)
            )
            
            # Add to sync queue
            data = {
                "wordid": wordid,
                "word": word,
                "en_meaning": en_meaning,
                "ch_meaning": ch_meaning,
                "part_of_speech": part_of_speech,
                "wordtime": current_time
            }
            
            cursor.execute(
                "INSERT INTO sync_queue (operation, wordid, word, data, timestamp) VALUES (?, ?, ?, ?, ?)",
                ('add', wordid, word, json.dumps(data), current_time)
            )
            
            conn.commit()
            print(f"Word added locally with ID: {wordid}")
            return wordid
        except Exception as e:
            conn.rollback()
            print(f"Error adding word:", e)
            raise e
        finally:
            conn.close()

    def find_word(self, word=None, wordid=None, partial_match=False) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Find word(s) by exact match, partial match, or ID
        
        Args:
            word: (Optional) Word to search for
            wordid: (Optional) Word ID to search for
            partial_match: Whether to use partial matching for the word
            
        Returns:
            A word dictionary, list of word dictionaries, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        try:
            # Search by wordid if provided
            if wordid is not None:
                cursor.execute("SELECT * FROM words WHERE wordid = ?", (wordid,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Convert part_of_speech JSON string back to list
                    result['part_of_speech'] = json.loads(result['part_of_speech'])
                    return result
                return None
            
            # Search by word if provided
            if word is not None:
                if partial_match:
                    # Use LIKE for partial matching
                    cursor.execute("SELECT * FROM words WHERE word LIKE ?", (f"%{word}%",))
                    rows = cursor.fetchall()
                    results = []
                    for row in rows:
                        result = dict(row)
                        # Convert part_of_speech JSON string back to list
                        result['part_of_speech'] = json.loads(result['part_of_speech'])
                        results.append(result)
                    return results
                else:
                    # Exact match
                    cursor.execute("SELECT * FROM words WHERE word = ?", (word,))
                    row = cursor.fetchone()
                    if row:
                        result = dict(row)
                        # Convert part_of_speech JSON string back to list
                        result['part_of_speech'] = json.loads(result['part_of_speech'])
                        return result
                    return None
        
            # If no search criteria provided, return all words
            cursor.execute("SELECT * FROM words")
            rows = cursor.fetchall()
            results = []
            for row in rows:
                result = dict(row)
                # Convert part_of_speech JSON string back to list
                result['part_of_speech'] = json.loads(result['part_of_speech'])
                results.append(result)
            return results
        except Exception as e:
            print(f"Error finding word:", e)
            raise e
        finally:
            conn.close()

    def update_word(self, wordid, update_data) -> bool:
        """
        Update word information locally
        
        Args:
            wordid: Word ID to update
            update_data: Dictionary of fields to update
            
        Returns:
            Boolean indicating success
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if word exists
            cursor.execute("SELECT wordid FROM words WHERE wordid = ?", (wordid,))
            if not cursor.fetchone():
                print(f"Word with ID {wordid} not found")
                return False
                
            # Build the SQL SET clause and parameters
            set_clause = []
            params = []
            
            # Handle special case for part_of_speech (convert list to JSON)
            if 'part_of_speech' in update_data:
                set_clause.append("part_of_speech = ?")
                params.append(json.dumps(update_data['part_of_speech']))
                
            # Handle other fields
            for key, value in update_data.items():
                if key != 'part_of_speech' and key in ['word', 'en_meaning', 'ch_meaning']:
                    set_clause.append(f"{key} = ?")
                    params.append(value)
            
            # Add synced status
            set_clause.append("synced = ?")
            params.append(0)  # Mark as not synced
            
            # Update the word
            if set_clause:
                sql = f"UPDATE words SET {', '.join(set_clause)} WHERE wordid = ?"
                params.append(wordid)
                
                cursor.execute(sql, params)
                
                # Add to sync queue
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT word FROM words WHERE wordid = ?", (wordid,))
                word = cursor.fetchone()[0]
                
                cursor.execute(
                    "INSERT INTO sync_queue (operation, wordid, word, data, timestamp) VALUES (?, ?, ?, ?, ?)",
                    ('update', wordid, word, json.dumps(update_data), current_time)
                )
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"Word {wordid} successfully updated locally")
                    return True
                else:
                    print(f"No changes made to word {wordid}")
                    return False
            else:
                print("No valid fields to update")
                return False
                
        except Exception as e:
            conn.rollback()
            print(f"Error updating word:", e)
            raise e
        finally:
            conn.close()

    def delete_word(self, word=None, wordid=None) -> bool:
        """
        Delete a word by word or wordid
        
        Args:
            word: (Optional) Word to delete
            wordid: (Optional) Word ID to delete
            
        Returns:
            Boolean indicating if the word was deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            params = ()
            
            # Find the word info before deleting
            if wordid is not None:
                cursor.execute("SELECT word FROM words WHERE wordid = ?", (wordid,))
                params = (wordid,)
                query = "DELETE FROM words WHERE wordid = ?"
            elif word is not None:
                cursor.execute("SELECT wordid FROM words WHERE word = ?", (word,))
                word_row = cursor.fetchone()
                if word_row:
                    wordid = word_row[0]
                params = (word,)
                query = "DELETE FROM words WHERE word = ?"
            else:
                print("Either word or wordid must be provided")
                return False
            
            word_info = cursor.fetchone()
            if not word_info:
                print(f"No word found to delete")
                return False
                
            # Delete the word
            cursor.execute(query, params)
            
            # Add to sync queue
            if cursor.rowcount > 0:
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO sync_queue (operation, wordid, word, data, timestamp) VALUES (?, ?, ?, ?, ?)",
                    ('delete', wordid, word if word else word_info[0], '{}', current_time)
                )
                
                conn.commit()
                print(f"Word successfully deleted locally")
                return True
            else:
                print(f"No word found to delete")
                return False
        except Exception as e:
            conn.rollback()
            print(f"Error deleting word:", e)
            raise e
        finally:
            conn.close()
            
    def get_pending_syncs(self) -> List[Dict[str, Any]]:
        """
        Get all pending synchronization operations
        
        Returns:
            List of sync operations
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM sync_queue ORDER BY id")
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                # Parse the data JSON string
                result['data'] = json.loads(result['data'])
                results.append(result)
                
            return results
        finally:
            conn.close()
            
    def mark_as_synced(self, wordid):
        """
        Mark a word as synced with MongoDB
        
        Args:
            wordid: Word ID to mark as synced
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE words SET synced = 1 WHERE wordid = ?",
                (wordid,)
            )
            conn.commit()
        finally:
            conn.close()
            
    def remove_from_sync_queue(self, sync_id):
        """
        Remove an operation from the sync queue
        
        Args:
            sync_id: ID of the sync operation
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM sync_queue WHERE id = ?",
                (sync_id,)
            )
            conn.commit()
        finally:
            conn.close()

    async def sync_with_mongodb(self, mongo_client):
        """
        Synchronize local database with MongoDB
        
        Args:
            mongo_client: MongoDB client instance
        """
        # Check for internet connection
        try:
            # Get pending sync operations
            pending_syncs = self.get_pending_syncs()
            
            if not pending_syncs:
                print("No pending syncs found")
                return
                
            print(f"Syncing {len(pending_syncs)} operations with MongoDB")
            
            # Ensure MongoDB client is connected
            if mongo_client.async_db is None:
                await mongo_client.connect_async()
                
            # Process each pending operation
            for sync_op in pending_syncs:
                operation = sync_op['operation']
                wordid = sync_op['wordid']
                word = sync_op['word']
                data = sync_op['data']
                
                try:
                    if operation == 'add':
                        # Convert part_of_speech from data if needed
                        if isinstance(data['part_of_speech'], str):
                            data['part_of_speech'] = json.loads(data['part_of_speech'])
                            
                        await add_word(
                            mongo_client,
                            word=data['word'],
                            en_meaning=data['en_meaning'],
                            ch_meaning=data['ch_meaning'],
                            part_of_speech=data['part_of_speech']
                        )
                    elif operation == 'update':
                        await update_word(mongo_client, wordid, data)
                    elif operation == 'delete':
                        await delete_word(mongo_client, wordid=wordid)
                        
                    # Mark as synced and remove from queue
                    self.mark_as_synced(wordid)
                    self.remove_from_sync_queue(sync_op['id'])
                    print(f"Successfully synced {operation} operation for word '{word}'")
                except Exception as e:
                    print(f"Error syncing {operation} operation for word '{word}': {e}")
                    # Continue with the next operation
                    
            print("Sync completed")
        except Exception as e:
            print(f"Sync error: {e}")