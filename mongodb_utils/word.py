# mongodb_utils/word.py
import datetime
import time

"""
Attributes in collection 'word':
    wordid: ID of the word
    word: Exact word
    ch_meaning: Chinese meaning/translation
    en_meaning: English meaning/definition
    part_of_speech: List of parts of speech (e.g., ["noun", "verb"])
    wordtime: Timestamp of when the word was added
"""

def add_word(client, word, en_meaning, ch_meaning, part_of_speech) -> int:
    """
    Add a new word to the word collection
    
    Args:
        client: MongoDBClient instance
        word: The word to add
        en_meaning: English meaning/definition
        ch_meaning: Chinese meaning/translation
        part_of_speech: List of parts of speech (e.g., ["noun", "verb"])
        
    Returns:
        wordid: The ID of the newly created word
    """
    if client.db is None:
        client.connect()
        
    collection = client.db['word']
    try:
        # Check if word already exists
        existing_word = collection.find_one({"word": word})
        if existing_word:
            print(f"Word '{word}' already exists with ID {existing_word['wordid']}")
            return existing_word["wordid"]
            
        # Find the maximum word ID
        max_word = collection.find_one({}, sort=[("wordid", -1)])
        if max_word:
            wordid = max_word["wordid"] + 1
        else:
            wordid = 1  # Start with ID 1 if collection is empty

        # Get current timestamp
        ts = time.time()
        
        # Add a new word to the collection
        document = {
            "wordid": wordid, 
            "word": word, 
            "ch_meaning": ch_meaning, 
            "en_meaning": en_meaning,
            "part_of_speech": part_of_speech, 
            "wordtime": datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        }
        
        result = collection.insert_one(document)
        print(f"Word added. Inserted document ID: {result.inserted_id}")
        return wordid
    except Exception as e:
        print(f"Error adding word:", e)

def find_word(client, word=None, wordid=None):
    """
    Find word(s) by exact match or ID
    
    Args:
        client: MongoDBClient instance
        word: (Optional) Exact word to search for
        wordid: (Optional) Word ID to search for
        
    Returns:
        A word document, or None if not found
    """
    if client.db is None:
        client.connect()
        
    collection = client.db['word']
    try:
        # Search by wordid if provided
        if wordid is not None:
            return collection.find_one({"wordid": wordid})
        
        # Search by exact word if provided
        if word is not None:
            return collection.find_one({"word": word})
    
            
        # If no search criteria provided, return all words
        return list(collection.find())
    except Exception as e:
        print(f"Error finding word:", e)

def delete_word(client, word=None, wordid=None) -> bool:
    """
    Delete a word by word or wordid
    
    Args:
        client: MongoDBClient instance
        word: (Optional) Word to delete
        wordid: (Optional) Word ID to delete
        
    Returns:
        Boolean indicating if the word was deleted
    """
    if client.db is None:
        client.connect()
        
    collection = client.db['word']
    try:
        # Delete by wordid if provided
        if wordid is not None:
            result = collection.delete_one({"wordid": wordid})
            
        # Delete by word if provided
        elif word is not None:
            result = collection.delete_one({"word": word})
        else:
            print("Either word or wordid must be provided")
            return False
            
        if result.deleted_count > 0:
            print(f"Word successfully deleted")
            return True
        else:
            print(f"No word found to delete")
            return False
    except Exception as e:
        print(f"Error deleting word:", e)