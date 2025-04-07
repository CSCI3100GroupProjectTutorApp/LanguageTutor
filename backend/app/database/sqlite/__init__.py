"""
SQLite database storage package for word management.

This package provides SQLite-based storage for words with MongoDB synchronization.
It enables offline-first capabilities with background sync when connectivity is available.
"""

from .sqlite_storage import WordStorage

__all__ = ['WordStorage']