# mongodb_utils/usage_log.py

"""
Attributes in collection 'event_logs':
    eventid: ID of the event
    userid: id of the user carrying out the event
    event_type: Type of event (e.g., "register", "login")
    event_time: Timestamp of when the event occurred
"""

async def add_event(client, userid, event_type, event_time) -> int:
    """
    Add a new event to the usage_logs collection
    
    Args:
        client: MongoDBClient instance
        userid: id of the user carrying out the event
        event_type: Type of event (e.g., "register", "login")
        event_time: Timestamp of when the event occurred
        
    Returns:
        wordid: The ID of the newly created event
    """
    # Ensure client is connected asynchronously
    if client.async_db is None:
        await client.connect_async()
        
    collection = client.async_db['usage_logs']
            
    # Find the maximum event ID
    max_event = await collection.find_one({}, sort=[("eventid", -1)])
    if max_event and "eventid" in max_event:
        eventid = max_event["eventid"] + 1
    else:
        eventid = 1  # Start with ID 1 if collection is empty
  
    # Add a new word to the collection
    document = {
        "eventid": eventid, 
        "userid": userid, 
        "event_type": event_type, 
        "event_time": event_time,
    }
        
    result = await collection.insert_one(document)
    print(f"Event added. Inserted document ID: {result.inserted_id}")
    return eventid
