"""
SQLite-based word storage for offline and online synchronization.
With minimal global sync of word operations.
"""
import os
import json
import asyncio
import threading
import time
import datetime
from typing import List, Dict, Any, Optional, Union
import aiosqlite

class WordStorage:
    def __init__(self, db_path="word_data.db", auto_sync_interval=60):
        """Initialize the SQLite storage for words.
        
        Args:
            db_path (str): Path to the SQLite database file
            auto_sync_interval (int): Time between auto-sync attempts in seconds
        """
        self.db_path = db_path
        self.auto_sync_interval = auto_sync_interval
        self.is_syncing = False
        self.sync_status = {
            "last_sync_attempt": None,
            "last_successful_sync": None,
            "pending_operations": 0,
            "is_online": False,
            "sync_in_progress": False
        }
        self._sync_thread = None
        self._stop_sync = False
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        
    
    async def initialize_db(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as conn:
            # Create words table (local vocabulary)
            await conn.execute('''
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
            
            # Create sync_queue table for tracking operations to sync to global MongoDB
            await conn.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,  -- 'add', 'update', 'delete', 'view', 'quiz', etc.
                user_id TEXT NOT NULL,  -- User ID for the operation
                wordid INTEGER,
                word TEXT,
                result TEXT,  -- For quiz operations: 'correct', 'incorrect', etc.
                context TEXT,  -- Optional context/sentence
                data TEXT,  -- JSON string of additional operation data
                timestamp TEXT NOT NULL
            )
            ''')
            
            await conn.commit()
    
    async def add_word(self, word, en_meaning, ch_meaning, part_of_speech, user_id) -> int:
        """
        Add a new word to the local database
        
        Args:
            word: The word to add
            en_meaning: English meaning/definition
            ch_meaning: Chinese meaning/translation
            part_of_speech: List of parts of speech (e.g., ["noun", "verb"])
            user_id: User ID adding the word
            
        Returns:
            wordid: The ID of the newly created word
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Start a transaction
                await conn.execute("BEGIN TRANSACTION")
                
                # Check if word already exists
                cursor = await conn.execute("SELECT wordid FROM words WHERE word = ?", (word,))
                existing_word = await cursor.fetchone()
                if existing_word:
                    print(f"Word '{word}' already exists with ID {existing_word[0]}")
                    
                    # Record this as a "view" operation for syncing in the same transaction
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    await conn.execute(
                        """
                        INSERT INTO sync_queue 
                        (operation, user_id, wordid, word, result, context, data, timestamp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        ("view", user_id, existing_word[0], word, None, None, None, timestamp)
                    )
                    
                    await conn.commit()
                    return existing_word[0]
                    
                # Find the maximum word ID
                cursor = await conn.execute("SELECT MAX(wordid) FROM words")
                result = await cursor.fetchone()
                if result[0] is not None:
                    wordid = result[0] + 1
                else:
                    wordid = 1  # Start with ID 1 if table is empty

                # Get current timestamp
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Convert part_of_speech list to JSON string
                pos_json = json.dumps(part_of_speech)
                
                # Add a new word to the table
                await conn.execute(
                    "INSERT INTO words (wordid, word, en_meaning, ch_meaning, part_of_speech, wordtime, synced) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (wordid, word, en_meaning, ch_meaning, pos_json, current_time, 0)
                )
                
                # Add to sync queue in the same transaction
                data = {
                    "wordid": wordid,
                    "word": word,
                    "en_meaning": en_meaning,
                    "ch_meaning": ch_meaning,
                    "part_of_speech": part_of_speech,
                    "wordtime": current_time
                }
                
                # Add to sync queue directly instead of calling the separate method
                await conn.execute(
                    """
                    INSERT INTO sync_queue 
                    (operation, user_id, wordid, word, result, context, data, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    ("add", user_id, wordid, word, None, None, json.dumps(data), current_time)
                )
                
                # Commit the entire transaction
                await conn.commit()
                print(f"Word added locally with ID: {wordid}")
                return wordid
            except Exception as e:
                # Roll back the entire transaction if there's an error
                await conn.rollback()
                print(f"Error adding word:", e)
                raise e

    async def find_word(self, word=None, wordid=None, partial_match=False, user_id=None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Find word(s) by exact match, partial match, or ID
        
        Args:
            word: (Optional) Word to search for
            wordid: (Optional) Word ID to search for
            partial_match: Whether to use partial matching for the word
            user_id: (Optional) User ID performing the search
            
        Returns:
            A word dictionary, list of word dictionaries, or None if not found
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row  # This enables column access by name
            
            try:
                result = None
                
                # Search by wordid if provided
                if wordid is not None:
                    cursor = await conn.execute("SELECT * FROM words WHERE wordid = ?", (wordid,))
                    row = await cursor.fetchone()
                    if row:
                        result = dict(row)
                        # Convert part_of_speech JSON string back to list
                        result['part_of_speech'] = json.loads(result['part_of_speech'])
                        
                        # Record view operation if user_id is provided
                        if user_id and result:
                            await self._add_to_sync_queue(
                                "view", 
                                user_id, 
                                wordid, 
                                result['word'], 
                                None, 
                                None, 
                                None
                            )
                            
                        return result
                    return None
                
                # Search by word if provided
                if word is not None:
                    if partial_match:
                        # Use LIKE for partial matching
                        cursor = await conn.execute("SELECT * FROM words WHERE word LIKE ?", (f"%{word}%",))
                        rows = await cursor.fetchall()
                        results = []
                        for row in rows:
                            word_data = dict(row)
                            # Convert part_of_speech JSON string back to list
                            word_data['part_of_speech'] = json.loads(word_data['part_of_speech'])
                            results.append(word_data)
                            
                        # Record search operation if user_id is provided and results found
                        if user_id and results:
                            # Record only for the first match
                            await self._add_to_sync_queue(
                                "search", 
                                user_id, 
                                results[0]['wordid'], 
                                results[0]['word'], 
                                None, 
                                f"Partial search: {word}", 
                                None
                            )
                            
                        return results
                    else:
                        # Exact match
                        cursor = await conn.execute("SELECT * FROM words WHERE word = ?", (word,))
                        row = await cursor.fetchone()
                        if row:
                            result = dict(row)
                            # Convert part_of_speech JSON string back to list
                            result['part_of_speech'] = json.loads(result['part_of_speech'])
                            
                            # Record view operation if user_id is provided
                            if user_id:
                                await self._add_to_sync_queue(
                                    "view", 
                                    user_id, 
                                    result['wordid'], 
                                    result['word'], 
                                    None, 
                                    None, 
                                    None
                                )
                                
                            return result
                        return None
            
                # If no search criteria provided, return all words
                cursor = await conn.execute("SELECT * FROM words")
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    word_data = dict(row)
                    # Convert part_of_speech JSON string back to list
                    word_data['part_of_speech'] = json.loads(word_data['part_of_speech'])
                    results.append(word_data)
                
                # Record list operation if user_id is provided
                if user_id and results:
                    await self._add_to_sync_queue(
                        "list_all", 
                        user_id, 
                        0,  # 0 means "all words" 
                        "all_words", 
                        None, 
                        None, 
                        None
                    )
                    
                return results
            except Exception as e:
                print(f"Error finding word:", e)
                raise e
            
    async def update_word(self, wordid, update_data, user_id) -> bool:
        """
        Update word information locally
        
        Args:
            wordid: Word ID to update
            update_data: Dictionary of fields to update
            user_id: User ID performing the update
            
        Returns:
            Boolean indicating success
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Start a transaction
                await conn.execute("BEGIN TRANSACTION")
                
                # Check if word exists
                cursor = await conn.execute("SELECT word FROM words WHERE wordid = ?", (wordid,))
                row = await cursor.fetchone()
                if not row:
                    print(f"Word with ID {wordid} not found")
                    await conn.rollback()
                    return False
                
                word = row[0]
                    
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
                    
                    await conn.execute(sql, params)
                    
                    # Add to sync queue in the same transaction
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    await conn.execute(
                        """
                        INSERT INTO sync_queue 
                        (operation, user_id, wordid, word, result, context, data, timestamp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        ("update", user_id, wordid, word, None, None, json.dumps(update_data), timestamp)
                    )
                    
                    # Commit the entire transaction
                    await conn.commit()
                    print(f"Word {wordid} successfully updated locally")
                    return True
                else:
                    print("No valid fields to update")
                    await conn.rollback()
                    return False
                    
            except Exception as e:
                await conn.rollback()
                print(f"Error updating word:", e)
                raise e
        
    async def delete_word(self, word=None, wordid=None, user_id=None) -> bool:
        """
        Delete a word by word or wordid
        
        Args:
            word: (Optional) Word to delete
            wordid: (Optional) Word ID to delete
            user_id: User ID performing the deletion
            
        Returns:
            Boolean indicating if the word was deleted
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Start a transaction
                await conn.execute("BEGIN TRANSACTION")
                
                cursor = None
                word_info = None
                
                # Find the word info before deleting
                if wordid is not None:
                    cursor = await conn.execute("SELECT word FROM words WHERE wordid = ?", (wordid,))
                    word_info = await cursor.fetchone()
                    query = "DELETE FROM words WHERE wordid = ?"
                    params = (wordid,)
                elif word is not None:
                    cursor = await conn.execute("SELECT wordid FROM words WHERE word = ?", (word,))
                    word_row = await cursor.fetchone()
                    if word_row:
                        wordid = word_row[0]
                    word_info = word
                    query = "DELETE FROM words WHERE word = ?"
                    params = (word,)
                else:
                    print("Either word or wordid must be provided")
                    await conn.rollback()
                    return False
                
                if not word_info:
                    print(f"No word found to delete")
                    await conn.rollback()
                    return False
                    
                # Delete the word
                cursor = await conn.execute(query, params)
                
                # Check if any row was affected
                if cursor.rowcount > 0:
                    # Add to sync queue in the same transaction
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    actual_word = word if word else word_info[0]
                    
                    await conn.execute(
                        """
                        INSERT INTO sync_queue 
                        (operation, user_id, wordid, word, result, context, data, timestamp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        ("delete", user_id, wordid, actual_word, None, None, None, timestamp)
                    )
                    
                    # Commit the entire transaction
                    await conn.commit()
                    print(f"Word successfully deleted locally")
                    return True
                else:
                    print(f"No word found to delete")
                    await conn.rollback()
                    return False
            except Exception as e:
                await conn.rollback()
                print(f"Error deleting word:", e)
                raise e
    
    async def record_quiz_attempt(self, user_id, wordid, is_correct, context=None):
        """
        Record a quiz attempt
        
        Args:
            user_id: User identifier
            wordid: Word ID
            is_correct: Whether the answer was correct
            context: Optional context/sentence
            
        Returns:
            Boolean indicating success
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Get word text
                cursor = await conn.execute("SELECT word FROM words WHERE wordid = ?", (wordid,))
                row = await cursor.fetchone()
                if not row:
                    print(f"Word with ID {wordid} not found")
                    return False
                
                word = row[0]
                result = "correct" if is_correct else "incorrect"
                
                # Add to sync queue
                await self._add_to_sync_queue(
                    "quiz", 
                    user_id, 
                    wordid, 
                    word, 
                    result, 
                    context, 
                    None
                )
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                print(f"Error recording quiz attempt:", e)
                return False
    
    async def mark_word(self, user_id, wordid, context=None):
        """
        Mark a word as important/favorite
        
        Args:
            user_id: User identifier
            wordid: Word ID
            context: Optional context/note
            
        Returns:
            Boolean indicating success
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                # Get word text
                cursor = await conn.execute("SELECT word FROM words WHERE wordid = ?", (wordid,))
                row = await cursor.fetchone()
                if not row:
                    print(f"Word with ID {wordid} not found")
                    return False
                
                word = row[0]
                
                # Add to sync queue
                await self._add_to_sync_queue(
                    "mark", 
                    user_id, 
                    wordid, 
                    word, 
                    None, 
                    context, 
                    None
                )
                
                await conn.commit()
                return True
            except Exception as e:
                await conn.rollback()
                print(f"Error marking word:", e)
                return False
    
    async def _add_to_sync_queue(self, operation, user_id, wordid, word, result, context, data, conn=None):
        """
        Add an operation to the sync queue
        
        Args:
            operation: Type of operation (add, update, delete, view, quiz, etc.)
            user_id: User ID performing the operation
            wordid: Word ID
            word: Word text
            result: Optional result (correct, incorrect, etc.)
            context: Optional context/sentence
            data: Optional JSON string of additional data
            conn: Optional database connection (if None, creates a new one)
            
        Returns:
            Boolean indicating success
        """
        # If connection is provided, use it (caller is responsible for transaction)
        if conn:
            try:
                # Record timestamp
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert into sync queue
                await conn.execute(
                    """
                    INSERT INTO sync_queue 
                    (operation, user_id, wordid, word, result, context, data, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (operation, user_id, wordid, word, result, context, data, timestamp)
                )
                
                return True
            except Exception as e:
                print(f"Error adding to sync queue:", e)
                return False
        else:
            # Create a new connection if one wasn't provided
            async with aiosqlite.connect(self.db_path) as new_conn:
                try:
                    # Record timestamp
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Insert into sync queue
                    await new_conn.execute(
                        """
                        INSERT INTO sync_queue 
                        (operation, user_id, wordid, word, result, context, data, timestamp) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (operation, user_id, wordid, word, result, context, data, timestamp)
                    )
                    
                    await new_conn.commit()
                    return True
                except Exception as e:
                    await new_conn.rollback()
                    print(f"Error adding to sync queue:", e)
                    return False
                
    async def get_pending_syncs(self) -> List[Dict[str, Any]]:
        """
        Get all pending synchronization operations
        
        Returns:
            List of sync operations
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            try:
                cursor = await conn.execute("SELECT * FROM sync_queue ORDER BY id")
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    # Parse the data JSON string if it's not None
                    if result['data']:
                        try:
                            result['data'] = json.loads(result['data'])
                        except:
                            # Keep as is if not valid JSON
                            pass
                    results.append(result)
                    
                return results
            except Exception as e:
                print(f"Error getting pending syncs:", e)
                raise e
                
    async def remove_from_sync_queue(self, sync_id):
        """
        Remove an operation from the sync queue
        
        Args:
            sync_id: ID of the sync operation
        """
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute(
                    "DELETE FROM sync_queue WHERE id = ?",
                    (sync_id,)
                )
                await conn.commit()
            except Exception as e:
                print(f"Error removing operation from sync queue:", e)
                await conn.rollback()
                raise e

    async def sync_with_mongodb(self, mongo_client):
        """
        Synchronize local database with MongoDB
        
        Args:
            mongo_client: MongoDB client instance
        """
        # Check for internet connection
        try:
            # Get pending sync operations
            pending_syncs = await self.get_pending_syncs()
            
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
                user_id = sync_op['user_id']
                wordid = sync_op['wordid']
                word = sync_op['word']
                result = sync_op['result']
                context = sync_op['context']
                data = sync_op['data']
                
                try:
                    # Import the log_word_operation function
                    from ..mongodb_utils.word_operations import log_word_operation
                    
                    # All operations are just logged to the global database
                    await log_word_operation(
                        mongo_client,
                        user_id=user_id,
                        wordid=wordid,
                        word=word,
                        operation_type=operation,
                        result=result,
                        context=context,
                        data=data
                    )
                    
                    # Remove from sync queue once logged
                    await self.remove_from_sync_queue(sync_op['id'])
                    print(f"Successfully synced {operation} operation for word '{word}'")
                except Exception as e:
                    print(f"Error syncing {operation} operation for word '{word}': {e}")
                    # Continue with the next operation
                    
            print("Sync completed")
        except Exception as e:
            print(f"Sync error: {e}")
            
    # -- Auto-Sync Methods --
    
    def start_auto_sync(self, mongo_client):
        """Start the auto-sync background thread.
        
        Args:
            mongo_client: MongoDB client instance to use for syncing
        """
        if self._sync_thread and self._sync_thread.is_alive():
            print("Auto-sync is already running")
            return
            
        self._stop_sync = False
        self._sync_thread = threading.Thread(
            target=self._auto_sync_loop,
            args=(mongo_client,),
            daemon=True  # Make thread daemon so it exits when main program exits
        )
        self._sync_thread.start()
        print("Auto-sync thread started")
        
    def stop_auto_sync(self):
        """Stop the auto-sync background thread."""
        if not self._sync_thread or not self._sync_thread.is_alive():
            print("Auto-sync is not running")
            return
            
        print("Stopping auto-sync thread...")
        self._stop_sync = True
        self._sync_thread.join(timeout=10)  # Wait up to 10 seconds for thread to stop
        self._sync_thread = None
        print("Auto-sync thread stopped")
        
    def _auto_sync_loop(self, mongo_client):
        """Background loop that periodically checks for and performs sync.
        
        Args:
            mongo_client: MongoDB client instance
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while not self._stop_sync:
            try:
                # Check for pending sync operations
                pending_syncs = loop.run_until_complete(self.get_pending_syncs())
                self.sync_status["pending_operations"] = len(pending_syncs)
                
                if pending_syncs:
                    # Check internet connectivity by trying to connect to MongoDB
                    is_online = loop.run_until_complete(self._check_connectivity(mongo_client))
                    self.sync_status["is_online"] = is_online
                    
                    if is_online:
                        print(f"Auto-sync: Found {len(pending_syncs)} operations to sync")
                        self.sync_status["sync_in_progress"] = True
                        loop.run_until_complete(self.sync_with_mongodb(mongo_client))
                        self.sync_status["last_successful_sync"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.sync_status["sync_in_progress"] = False
                
                self.sync_status["last_sync_attempt"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            except Exception as e:
                print(f"Error in auto-sync loop: {e}")
                self.sync_status["sync_in_progress"] = False
            
            # Sleep between sync attempts
            for _ in range(self.auto_sync_interval):
                if self._stop_sync:
                    break
                time.sleep(1)  # Check for stop signal every second
                
        loop.close()
    
    async def _check_connectivity(self, mongo_client):
        """Check if we can connect to MongoDB.
        
        Args:
            mongo_client: MongoDB client instance
            
        Returns:
            bool: True if connection is available, False otherwise
        """
        try:
            if mongo_client.async_db is None:
                await mongo_client.connect_async()
            
            # Try a simple operation to check connectivity
            # This is a lightweight operation that won't affect performance
            await mongo_client.async_db.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB connection check failed: {e}")
            return False
    
    def get_sync_status(self):
        """Get the current sync status information.
        
        Returns:
            dict: The current sync status
        """
        # Update pending operations count in a separate thread to avoid blocking
        asyncio.run(self._update_pending_count())
        return self.sync_status
    
    async def _update_pending_count(self):
        """Update the pending operations count in the status."""
        try:
            pending_syncs = await self.get_pending_syncs()
            self.sync_status["pending_operations"] = len(pending_syncs)
        except Exception as e:
            print(f"Error updating pending count: {e}")
    
    async def force_sync(self, mongo_client):
        """Force an immediate synchronization attempt.
        
        Args:
            mongo_client: MongoDB client instance
            
        Returns:
            dict: Result of the sync operation
        """
        result = {
            "success": False,
            "message": "",
            "operations_processed": 0
        }
        
        if self.sync_status["sync_in_progress"]:
            result["message"] = "Sync already in progress"
            return result
        
        try:
            self.sync_status["sync_in_progress"] = True
            
            # Check connectivity
            is_online = await self._check_connectivity(mongo_client)
            self.sync_status["is_online"] = is_online
            
            if not is_online:
                result["message"] = "No internet connection available"
                return result
            
            # Get pending operations
            pending_syncs = await self.get_pending_syncs()
            
            if not pending_syncs:
                result["message"] = "No pending operations to sync"
                result["success"] = True
                return result
            
            # Perform the sync
            await self.sync_with_mongodb(mongo_client)
            
            # Update result
            result["success"] = True
            result["message"] = f"Successfully synced {len(pending_syncs)} operations"
            result["operations_processed"] = len(pending_syncs)
            
            # Update status
            self.sync_status["last_successful_sync"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.sync_status["pending_operations"] = 0
            
            return result
        except Exception as e:
            result["message"] = f"Sync error: {str(e)}"
            return result
        finally:
            self.sync_status["sync_in_progress"] = False
            self.sync_status["last_sync_attempt"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')