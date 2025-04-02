# mongodb_utils/word_operations.py
import datetime

async def log_word_operation(client, user_id, wordid, word, operation_type, 
                           result=None, context=None, data=None, timestamp=None):
    """
    Log a user's operation on a word in the global database
    
    Args:
        client: MongoDBClient instance
        user_id: User identifier
        wordid: Word ID (from local SQLite)
        word: The actual word text
        operation_type: Type of operation (add, update, delete, view, quiz, mark, etc.)
        result: Optional result (correct, incorrect, etc.)
        context: Optional context/sentence
        data: Optional additional data
        timestamp: Optional timestamp (will use current time if not provided)
        
    Returns:
        Boolean indicating success
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['word_operations']
    
    try:
        # Use provided timestamp or current time
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        # Create the operation record
        operation = {
            "user_id": user_id,
            "wordid": wordid,
            "word": word,
            "operation_type": operation_type,
            "timestamp": timestamp
        }
        
        # Add optional fields if provided
        if result is not None:
            operation["result"] = result
        if context is not None:
            operation["context"] = context
        if data is not None:
            operation["data"] = data
            
        # Insert the operation
        await collection.insert_one(operation)
        
        # For add/update operations, also update the global_words collection
        if operation_type == "add" and data:
            # Add or update the word in global words collection
            global_words = client.async_db['global_words']
            
            # Check if word already exists
            existing = await global_words.find_one({"word": word})
            
            if not existing:
                # Add new word to global collection
                global_word = {
                    "wordid": wordid,
                    "word": word,
                    "en_meaning": data.get("en_meaning", ""),
                    "ch_meaning": data.get("ch_meaning", ""),
                    "part_of_speech": data.get("part_of_speech", []),
                    "added_by": user_id,
                    "added_time": timestamp,
                    "last_updated_by": user_id,
                    "last_updated_time": timestamp
                }
                
                await global_words.insert_one(global_word)
        
        elif operation_type == "update" and data:
            # Update the word in global words collection
            global_words = client.async_db['global_words']
            
            # Prepare update data
            update = {}
            
            # Only include fields that are in the data
            for field in ["word", "en_meaning", "ch_meaning", "part_of_speech"]:
                if field in data:
                    update[field] = data[field]
            
            # Add attribution
            update["last_updated_by"] = user_id
            update["last_updated_time"] = timestamp
            
            # Update if the word exists
            if update:
                await global_words.update_one(
                    {"wordid": wordid},
                    {"$set": update}
                )
                
        # Add stats record for quiz operations
        if operation_type == "quiz":
            stats_collection = client.async_db['user_word_stats']
            
            # Check if stats exists for this user-word pair
            stats = await stats_collection.find_one({"user_id": user_id, "wordid": wordid})
            
            if stats:
                # Update existing stats
                update = {
                    "last_quiz": timestamp,
                    "quiz_count": stats.get("quiz_count", 0) + 1
                }
                
                if result == "correct":
                    update["correct_count"] = stats.get("correct_count", 0) + 1
                elif result == "incorrect":
                    update["incorrect_count"] = stats.get("incorrect_count", 0) + 1
                
                await stats_collection.update_one(
                    {"user_id": user_id, "wordid": wordid},
                    {"$set": update}
                )
            else:
                # Create new stats record
                stats_doc = {
                    "user_id": user_id,
                    "wordid": wordid,
                    "word": word,
                    "first_quiz": timestamp,
                    "last_quiz": timestamp,
                    "quiz_count": 1,
                    "correct_count": 1 if result == "correct" else 0,
                    "incorrect_count": 1 if result == "incorrect" else 0
                }
                
                await stats_collection.insert_one(stats_doc)
            
        return True
    except Exception as e:
        print(f"Error logging word operation in MongoDB:", e)
        return False
    

async def get_user_word_stats(client, user_id):
    """
    Get a user's word learning statistics from MongoDB
    
    Args:
        client: MongoDBClient instance
        user_id: User identifier
        
    Returns:
        Dictionary of user stats or None if not found
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    try:
        # Get operations for this user
        operations_collection = client.async_db['word_operations']
        stats_collection = client.async_db['user_word_stats']
        
        # Create aggregated stats
        user_stats = {
            "user_id": user_id,
            "total_operations": 0,
            "add_operations": 0,
            "view_operations": 0,
            "update_operations": 0,
            "delete_operations": 0,
            "quiz_attempts": 0,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "mark_operations": 0,
            "unique_words_seen": 0
        }
        
        # Count operations by type
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$operation_type",
                "count": {"$sum": 1}
            }}
        ]
        
        operations_by_type = await operations_collection.aggregate(pipeline).to_list(length=None)
        
        # Fill in counts from pipeline results
        for operation in operations_by_type:
            op_type = operation["_id"]
            count = operation["count"]
            user_stats["total_operations"] += count
            
            if op_type == "add":
                user_stats["add_operations"] = count
            elif op_type == "view":
                user_stats["view_operations"] = count
            elif op_type == "update":
                user_stats["update_operations"] = count
            elif op_type == "delete":
                user_stats["delete_operations"] = count
            elif op_type == "quiz":
                user_stats["quiz_attempts"] = count
            elif op_type == "mark":
                user_stats["mark_operations"] = count
                
        # Count unique words seen
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": "$wordid"
            }},
            {"$count": "unique_words"}
        ]
        
        unique_words_result = await operations_collection.aggregate(pipeline).to_list(length=None)
        if unique_words_result and len(unique_words_result) > 0:
            user_stats["unique_words_seen"] = unique_words_result[0].get("unique_words", 0)
            
        # Count correct/incorrect quiz answers
        pipeline = [
            {"$match": {"user_id": user_id, "operation_type": "quiz"}},
            {"$group": {
                "_id": "$result",
                "count": {"$sum": 1}
            }}
        ]
        
        quiz_results = await operations_collection.aggregate(pipeline).to_list(length=None)
        
        for result in quiz_results:
            result_type = result["_id"]
            count = result["count"]
            
            if result_type == "correct":
                user_stats["correct_answers"] = count
            elif result_type == "incorrect":
                user_stats["incorrect_answers"] = count
                
        # Get quiz success rate
        if user_stats["quiz_attempts"] > 0:
            user_stats["quiz_success_rate"] = round(
                (user_stats["correct_answers"] / user_stats["quiz_attempts"]) * 100, 2
            )
        else:
            user_stats["quiz_success_rate"] = 0
            
        # Add timestamp
        user_stats["last_updated"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        return user_stats
    except Exception as e:
        print(f"Error getting user word stats from MongoDB:", e)
        return None