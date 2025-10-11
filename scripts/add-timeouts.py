#!/usr/bin/env python3
"""
Add timeout parameters to all zmq_client.call() invocations in router files.

This script adds timeout=5.0 to all zmq_client.call() that don't already have it.
"""

import re
import sys
from pathlib import Path

def add_timeouts_to_file(filepath):
    """Add timeout parameters to zmq_client.call() in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    
    # Pattern to match zmq_client.call without timeout parameter
    # Matches: zmq_client.call("service", "method", **kwargs) or similar
    pattern = r'(zmq_client\.call\([^)]+?)(\))'
    
    def add_timeout(match):
        call_content = match.group(1)
        closing_paren = match.group(2)
        
        # Skip if already has timeout
        if 'timeout=' in call_content:
            return match.group(0)
        
        # Add timeout before closing paren
        # If there are keyword args, add comma
        if '**' in call_content or '=' in call_content:
            return f"{call_content}, timeout=5.0{closing_paren}"
        else:
            return f"{call_content}, timeout=5.0{closing_paren}"
    
    content = re.sub(pattern, add_timeout, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    routers_dir = Path(__file__).parent.parent / 'client-interface' / 'web_api' / 'api' / 'routers'
    
    if not routers_dir.exists():
        print(f"Error: Routers directory not found: {routers_dir}")
        return 1
    
    files_modified = 0
    for router_file in routers_dir.glob('*.py'):
        if router_file.name.startswith('__'):
            continue
        
        print(f"Processing {router_file.name}...", end=' ')
        if add_timeouts_to_file(router_file):
            print("✓ Modified")
            files_modified += 1
        else:
            print("○ No changes needed")
    
    print(f"\n✅ Processed {files_modified} files")
    return 0

if __name__ == '__main__':
    sys.exit(main())
