"""
Logging configuration for the application.
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure the logger
logger = logging.getLogger("tutor_app")
logger.setLevel(logging.INFO)  # Set the minimum log level to capture

# Create formatters
simple_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
)

# Console handler (for development and immediate feedback)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(simple_formatter)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# File handler (for persistent logs)
file_handler = RotatingFileHandler(
    "logs/app.log",        # Log file path
    maxBytes=10485760,     # 10MB per file
    backupCount=5          # Keep 5 backup files
)
file_handler.setFormatter(detailed_formatter)
file_handler.setLevel(logging.DEBUG)  # More detailed in the file
logger.addHandler(file_handler)

# Optional: Error file handler (for capturing only errors)
error_file_handler = RotatingFileHandler(
    "logs/error.log", 
    maxBytes=10485760,
    backupCount=5
)
error_file_handler.setFormatter(detailed_formatter)
error_file_handler.setLevel(logging.ERROR)
logger.addHandler(error_file_handler)

# Prevent logs from propagating to the root logger
logger.propagate = False

# Export the configured logger
__all__ = ["logger"]