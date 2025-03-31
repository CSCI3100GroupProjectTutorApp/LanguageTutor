# mongodb_utils/word.py
import datetime
import time

"""
Attributes in collection 'words':
    wordid: ID of the word
    word: Exact word
    ch_meaning: Chinese meaning/translation
    en_meaning: English meaning/definition
    part_of_speech: List of parts of speech (e.g., ["noun", "verb"])
    wordtime: Timestamp of when the word was added
"""

async def add_word(client, word, en_meaning, ch_meaning, part_of_speech) -> int:
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
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['words']
    
    try:
        # Check if word already exists
        existing_word = await collection.find_one({"word": word})
        if existing_word:
            print(f"Word '{word}' already exists with ID {existing_word['wordid']}")
            return existing_word["wordid"]
            
        # Find the maximum word ID
        max_word = await collection.find_one({}, sort=[("wordid", -1)])
        if max_word and "wordid" in max_word:
            wordid = max_word["wordid"] + 1
        else:
            wordid = 1  # Start with ID 1 if collection is empty

        # Get current timestamp
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add a new word to the collection
        document = {
            "wordid": wordid, 
            "word": word, 
            "ch_meaning": ch_meaning, 
            "en_meaning": en_meaning,
            "part_of_speech": part_of_speech, 
            "wordtime": current_time
        }
        
        result = await collection.insert_one(document)
        print(f"Word added. Inserted document ID: {result.inserted_id}")
        return wordid
    except Exception as e:
        print(f"Error adding word:", e)
        raise e

async def find_word(client, word=None, wordid=None, partial_match=False):
    """
    Find word(s) by exact match, partial match, or ID
    
    Args:
        client: MongoDBClient instance
        word: (Optional) Word to search for
        wordid: (Optional) Word ID to search for
        partial_match: Whether to use partial matching for the word
        
    Returns:
        A word document, list of word documents, or None if not found
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['words']
    
    try:
        # Search by wordid if provided
        if wordid is not None:
            return await collection.find_one({"wordid": wordid})
        
        # Search by word if provided
        if word is not None:
            if partial_match:
                # Use regex for partial matching
                regex_pattern = {"$regex": f".*{word}.*", "$options": "i"}
                cursor = collection.find({"word": regex_pattern})
                return [doc async for doc in cursor]
            else:
                # Exact match
                return await collection.find_one({"word": word})
    
        # If no search criteria provided, return all words
        cursor = collection.find()
        return [doc async for doc in cursor]
    except Exception as e:
        print(f"Error finding word:", e)
        raise e

async def update_word(client, wordid, update_data):
    """
    Update word information
    
    Args:
        client: MongoDBClient instance
        wordid: Word ID to update
        update_data: Dictionary of fields to update
        
    Returns:
        Boolean indicating success
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['words']
    
    try:
        result = await collection.update_one(
            {"wordid": wordid},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            print(f"Word {wordid} successfully updated")
            return True
        else:
            print(f"No changes made to word {wordid}")
            return False
    except Exception as e:
        print(f"Error updating word:", e)
        raise e

async def delete_word(client, word=None, wordid=None) -> bool:
    """
    Delete a word by word or wordid
    
    Args:
        client: MongoDBClient instance
        word: (Optional) Word to delete
        wordid: (Optional) Word ID to delete
        
    Returns:
        Boolean indicating if the word was deleted
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['words']
    
    try:
        query = {}
        
        # Delete by wordid if provided
        if wordid is not None:
            query["wordid"] = wordid
        # Delete by word if provided
        elif word is not None:
            query["word"] = word
        else:
            print("Either word or wordid must be provided")
            return False
            
        result = await collection.delete_one(query)
        
        if result.deleted_count > 0:
            print(f"Word successfully deleted")
            return True
        else:
            print(f"No word found to delete")
            return False
    except Exception as e:
        print(f"Error deleting word:", e)
        raise e