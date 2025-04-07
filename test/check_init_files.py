# test/check_init_files.py
from pathlib import Path

# Directories that should be packages
required_packages = [
    "backend",
    "backend/app",
    "backend/app/routes",
    "backend/app/models",
    # Add other directories that should be packages
]

for package in required_packages:
    # Use pathlib for cross-platform compatibility
    package_path = Path(package.replace("/", "\\"))
    init_file = package_path / "__init__.py"
    
    if not package_path.exists():
        print(f"✗ Package directory missing: {package_path}")
    elif not init_file.exists():
        print(f"✗ Missing __init__.py in {package_path}")
        # Create the file
        with open(init_file, 'w') as f:
            pass
        print(f"  ✓ Created {init_file}")
    else:
        print(f"✓ {init_file} exists")