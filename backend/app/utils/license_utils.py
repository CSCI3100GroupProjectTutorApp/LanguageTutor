# app/utils/license_utils.py
import uuid
import hashlib
import random
import string
import re
from datetime import datetime

def generate_license_key():
    """Generate a license key in format AAAA-BBBB-CCCC-DDDD"""
    segments = []
    chars = string.ascii_uppercase + string.digits
    
    for _ in range(4):
        segment = ''.join(random.choices(chars, k=4))
        segments.append(segment)
    
    return "-".join(segments)

def validate_license_format(license_key):
    """Validate the format of a license key"""
    pattern = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
    return bool(re.match(pattern, license_key))

def parse_license_file(file_content):
    """Parse a license file and extract valid license keys"""
    valid_keys = []
    
    # Split by common separators and clean up
    lines = file_content.replace(',', '\n').split('\n')
    
    for line in lines:
        # Clean up whitespace and remove quotes
        line = line.strip().replace('"', '').replace("'", '')
        
        # Check if this line contains a valid license key
        if validate_license_format(line):
            valid_keys.append(line)
    
    return valid_keys