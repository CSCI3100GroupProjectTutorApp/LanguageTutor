# test/debug_imports.py - updated
import os
import sys
from pathlib import Path  # Use pathlib for cross-platform paths

print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")

# Check paths using pathlib (cross-platform)
backend_path = Path("backend")
app_path = backend_path / "app"
main_path = app_path / "main.py"

print(f"Does backend directory exist? {backend_path.exists()}")
print(f"Does backend/app directory exist? {app_path.exists()}")
print(f"Does backend/app/main.py exist? {main_path.exists()}")

# Print content of directories to verify
print("\nContents of current directory:")
print(os.listdir("."))

print("\nContents of backend directory:")
if backend_path.exists():
    print(os.listdir(backend_path))

print("\nContents of backend/app directory:")
if app_path.exists():
    print(os.listdir(app_path))