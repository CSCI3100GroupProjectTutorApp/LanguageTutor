# test/conftest.py
import sys
import os
from pathlib import Path

# Add the project root directory to Python's path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# For debugging - you can comment this out after fixing the issue
print(f"Python path now includes: {sys.path[0]}")