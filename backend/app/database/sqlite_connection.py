"""
SQLite connection utilities for the language tutoring API.
This module provides SQLite database connections for local word storage.
"""
import os
import sys
import asyncio
import aiosqlite
from pathlib import Path

# Add the root directory to the Python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))

from ..config import settings

# Default database path - you can override this in your settings
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 
    "data", 
    "word_storage.db"
)

class SQLiteManager:
    """SQLite database manager for word storage"""
    
    def __init__(self, db_path=None):
        """Initialize the SQLite manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses settings or default.
        """
        self.db_path = db_path or getattr(settings, "SQLITE_DB_PATH", DEFAULT_DB_PATH)
        self.connection = None
        
        # Ensure the directory for the database exists
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
    
    async def connect(self):
        """Connect to the SQLite database."""
        if self.connection is None or self.connection.closed:
            self.connection = await aiosqlite.connect(self.db_path)
            self.connection.row_factory = aiosqlite.Row  # Enable dictionary access
        return self.connection
    
    async def close(self):
        """Close the database connection."""
        if self.connection and not self.connection.closed:
            await self.connection.close()
            self.connection = None
    
    async def execute(self, query, params=None):
        """Execute a query.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            The cursor object after execution
        """
        conn = await self.connect()
        if params:
            return await conn.execute(query, params)
        else:
            return await conn.execute(query)
    
    async def execute_many(self, query, params_list):
        """Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            The cursor object after execution
        """
        conn = await self.connect()
        return await conn.executemany(query, params_list)
    
    async def fetch_all(self, query, params=None):
        """Execute a query and fetch all results.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            List of row dictionaries
        """
        cursor = await self.execute(query, params)
        rows = await cursor.fetchall()
        # Convert Row objects to dictionaries
        return [dict(row) for row in rows]
    
    async def fetch_one(self, query, params=None):
        """Execute a query and fetch one result.
        
        Args:
            query: SQL query to execute
            params: Parameters for the query
            
        Returns:
            Row dictionary or None
        """
        cursor = await self.execute(query, params)
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    async def commit(self):
        """Commit the current transaction."""
        if self.connection and not self.connection.closed:
            await self.connection.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        if self.connection and not self.connection.closed:
            await self.connection.rollback()
    
    async def init_tables(self):
        """Initialize database tables."""
        conn = await self.connect()
        
        # Create words table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS words (
            wordid INTEGER PRIMARY KEY,
            word TEXT UNIQUE NOT NULL,
            en_meaning TEXT,
            ch_meaning TEXT,
            part_of_speech TEXT,
            wordtime TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
        ''')
        
        # Create sync_queue table
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            wordid INTEGER,
            word TEXT,
            data TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        
        await conn.commit()

# Global instance
sqlite_manager = None

async def get_sqlite_manager():
    """Get or create the SQLite manager."""
    global sqlite_manager
    if sqlite_manager is None:
        sqlite_manager = SQLiteManager()
        await sqlite_manager.init_tables()
    return sqlite_manager

async def init_sqlite():
    """Initialize SQLite database."""
    manager = await get_sqlite_manager()
    await manager.init_tables()
    print(f"SQLite database initialized at {manager.db_path}")
    return manager

async def close_sqlite_connection():
    """Close SQLite connection."""
    global sqlite_manager
    if sqlite_manager:
        await sqlite_manager.close()
        print("SQLite connection closed")