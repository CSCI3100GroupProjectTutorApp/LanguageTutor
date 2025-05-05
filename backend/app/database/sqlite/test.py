import asyncio
from sqlite_storage import WordStorage

async def test_word_storage():
    # Initialize WordStorage
    storage = WordStorage(db_path="test_word_data.db")
    
    # Step 1: Initialize the database
    print("Initializing database...")
    await storage.initialize_db()
    print("Database initialized successfully.")
    
    # Step 2: Add a word
    print("Adding a word...")
    word = "test"
    en_meaning = "A procedure intended to establish the quality, performance, or reliability of something."
    ch_meaning = "測試"
    part_of_speech = ["noun"]
    user_id = "user123"
    
    word_id = await storage.add_word(word, en_meaning, ch_meaning, part_of_speech, user_id)
    print(f"Word added with ID: {word_id}")
    
    # Step 3: Find the word by exact match
    print("Finding the word by exact match...")
    found_word = await storage.find_word(word=word)
    print(f"Found word: {found_word}")
    
    # Step 4: Find the word by ID
    print("Finding the word by ID...")
    found_word_by_id = await storage.find_word(wordid=word_id)
    print(f"Found word by ID: {found_word_by_id}")
    
    # Step 5: Update the word
    print("Updating the word...")
    update_data = {
        "en_meaning": "An updated definition for the test word.",
        "part_of_speech": ["noun", "verb"]
    }
    update_success = await storage.update_word(word_id, update_data, user_id)
    print(f"Word updated successfully: {update_success}")
    
    # Step 6: Find the updated word
    print("Finding the updated word...")
    updated_word = await storage.find_word(wordid=word_id)
    print(f"Updated word: {updated_word}")
    
    # Step 7: Delete the word
    print("Deleting the word...")
    delete_success = await storage.delete_word(user_id, word=word)
    print(f"Word deleted successfully: {delete_success}")
    
    # Step 8: Verify the word is deleted
    print("Verifying the word is deleted...")
    deleted_word = await storage.find_word(word=word)
    print(f"Deleted word: {deleted_word}")
    
    # Clean up: Remove the test database file
    import os
    if os.path.exists("test_word_data.db"):
        os.remove("test_word_data.db")
        print("Test database file removed.")

# Run the test
asyncio.run(test_word_storage())