#!/usr/bin/env python3
"""
Script to remove all Google Sheets references from all Python files
"""
import re
import os

files_to_update = [
    'Home.py',
    'pages/1_Log_Workout.py',
    'pages/2_Progress.py',
    'pages/3_Goals.py',
    'pages/4_Leaderboard.py',
    'pages/5_Profile.py',
    'pages/6_Custom_Workouts.py'
]

def update_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove get_google_sheet import
    content = re.sub(r',?\s*get_google_sheet,?\s*', ', ', content)
    content = re.sub(r'from utils\.helpers import \(([^)]*)\)', 
                     lambda m: f'from utils.helpers import ({m.group(1).replace(", ,", ",").replace(",,", ",")})',
                     content)
    
    # Remove spreadsheet = get_google_sheet() and worksheet lines
    content = re.sub(r'spreadsheet = get_google_sheet\(\)\s*\n', '', content)
    content = re.sub(r'workout_sheet = spreadsheet\.worksheet\([^)]+\)[^\n]*\n', '', content)
    
    # Remove spreadsheet comments
    content = re.sub(r'# Connect to Google Sheets\s*\n', '', content)
    content = re.sub(r'# Load users dynamically from Google Sheets\s*\n', '# Load users\n', content)
    
    # Update function calls - remove spreadsheet argument
    # Pattern: func(spreadsheet, ...)
    content = re.sub(r'(\w+)\(spreadsheet,\s*', r'\1(', content)
    
    # Pattern: func(..., spreadsheet)
    content = re.sub(r'(\w+)\(([^)]+),\s*spreadsheet\)', r'\1(\2)', content)
    
    # Remove if spreadsheet: blocks and fix indentation
    # Simple version - just remove the condition
    content = re.sub(r'if spreadsheet:\s*\n\s+available_users = load_users_from_sheets\(([^)]*)\)\s*\n\s+user_pins = load_user_pins_from_sheets\(([^)]*)\)\s*\nelse:\s*\n\s+available_users = USER_LIST\.copy\(\)\s*\n\s+user_pins = \{user: "0000" for user in available_users\}',
                     'available_users = load_users_from_sheets()\nuser_pins = load_user_pins_from_sheets()',
                     content)
    
    # Remove other if spreadsheet: checks
    content = re.sub(r'if spreadsheet:\s*\n', '', content)
    content = re.sub(r'if not spreadsheet:\s*\n\s+st\.error\([^)]+\)\s*\n(?:\s+st\.stop\(\)\s*\n)?', '', content)
    
    # Clean up double blank lines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Updated {filepath}")
        return True
    else:
        print(f"ℹ️  No changes needed for {filepath}")
        return False

# Update all files
updated_count = 0
for filepath in files_to_update:
    if os.path.exists(filepath):
        if update_file(filepath):
            updated_count += 1
    else:
        print(f"⚠️  File not found: {filepath}")

print(f"\n✨ Updated {updated_count} files")
