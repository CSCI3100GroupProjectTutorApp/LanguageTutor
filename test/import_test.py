# test/import_test.py
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
print(f"Added to path: {project_root}")

# Try to import with plain Python
try:
    import backend
    print("✓ Successfully imported 'backend'")
except ImportError as e:
    print(f"✗ Failed to import 'backend': {e}")

try:
    import backend.app
    print("✓ Successfully imported 'backend.app'")
except ImportError as e:
    print(f"✗ Failed to import 'backend.app': {e}")

try:
    from backend.app import main
    print("✓ Successfully imported 'backend.app.main'")
except ImportError as e:
    print(f"✗ Failed to import 'backend.app.main': {e}")