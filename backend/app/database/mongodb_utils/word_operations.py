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