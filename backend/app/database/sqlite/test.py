import os
import asyncio
from sqlite_storage import WordStorage

# Test database path
TEST_DB_PATH = "data/test_word_storage.db"

# Remove the test database if it exists
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

def print_separator(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

async def test_word_storage():
    # Initialize storage
    print_separator("Initializing WordStorage")
    storage = WordStorage(TEST_DB_PATH)
    print(f"Database initialized at {TEST_DB_PATH}")
    
    # Test adding words
    print_separator("Testing add_word")
    word1_id = storage.add_word(
        word="test", 
        en_meaning="A process for checking functionality", 
        ch_meaning="測試", 
        part_of_speech=["noun", "verb"]
    )
    print(f"Added word 'test' with ID: {word1_id}")
    
    word2_id = storage.add_word(
        word="example", 
        en_meaning="A representative specimen", 
        ch_meaning="例子", 
        part_of_speech=["noun"]
    )
    print(f"Added word 'example' with ID: {word2_id}")
    
    word3_id = storage.add_word(
        word="implement", 
        en_meaning="To put into effect", 
        ch_meaning="實施", 
        part_of_speech=["verb", "noun"]
    )
    print(f"Added word 'implement' with ID: {word3_id}")
    
    # Test finding words
    print_separator("Testing find_word by ID")
    word = storage.find_word(wordid=word1_id)
    print(f"Found word by ID {word1_id}:")
    print(word)
    
    print_separator("Testing find_word by exact word")
    word = storage.find_word(word="example")
    print(f"Found word 'example':")
    print(word)
    
    print_separator("Testing find_word with partial match")
    words = storage.find_word(word="impl", partial_match=True)
    print(f"Found words containing 'impl':")
    for w in words:
        print(f" - {w['word']}: {w['en_meaning']}")
    
    print_separator("Testing get all words")
    all_words = storage.find_word()
    print(f"Found {len(all_words)} words in total:")
    for w in all_words:
        print(f" - {w['wordid']}: {w['word']} ({', '.join(w['part_of_speech'])})")
    
    # Test updating words
    print_separator("Testing update_word")
    update_result = storage.update_word(
        wordid=word1_id,
        update_data={
            "en_meaning": "An updated definition for testing",
            "part_of_speech": ["noun", "verb", "adjective"]
        }
    )
    print(f"Update result: {update_result}")
    
    updated_word = storage.find_word(wordid=word1_id)
    print(f"Updated word:")
    print(updated_word)
    
    # Test pending syncs
    print_separator("Testing get_pending_syncs")
    pending_syncs = storage.get_pending_syncs()
    print(f"Found {len(pending_syncs)} pending sync operations:")
    for op in pending_syncs:
        print(f" - {op['operation']} for word '{op['word']}' (ID: {op['wordid']})")
        print(f"   Data: {op['data']}")
    
    # Test delete word
    print_separator("Testing delete_word by ID")
    delete_result = storage.delete_word(wordid=word2_id)
    print(f"Delete result: {delete_result}")
    
    remaining_words = storage.find_word()
    print(f"Remaining words after deletion:")
    for w in remaining_words:
        print(f" - {w['wordid']}: {w['word']}")
    
    # Test delete word by name
    print_separator("Testing delete_word by name")
    delete_result = storage.delete_word(word="implement")
    print(f"Delete result: {delete_result}")
    
    remaining_words = storage.find_word()
    print(f"Remaining words after second deletion:")
    for w in remaining_words:
        print(f" - {w['wordid']}: {w['word']}")
    
    # Final sync queue check
    print_separator("Final sync queue check")
    final_syncs = storage.get_pending_syncs()
    print(f"Found {len(final_syncs)} pending sync operations at the end:")
    for op in final_syncs:
        print(f" - {op['operation']} for word '{op['word']}' (ID: {op['wordid']})")
    
    print("\nAll tests completed successfully!")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_word_storage())