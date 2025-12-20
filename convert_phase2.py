#!/usr/bin/env python3
"""
Phase 2: Update all remaining database functions to use Supabase
"""
import re

# Read current helpers.py
with open('utils/helpers.py', 'r') as f:
    content = f.read()

# Define all replacements as (old_pattern, new_code) tuples
replacements = [
    # load_users_from_sheets
    (r'''def load_users_from_sheets\(spreadsheet\):
    """Load unique users from Users sheet"""
    try:
        data = _load_sheet_data\("Users"\)
        if data:
            df = pd\.DataFrame\(data\)
            if "Username" in df\.columns:
                users = df\["Username"\]\.tolist\(\)
                return users if users else USER_LIST\.copy\(\)
        return USER_LIST\.copy\(\)
    except Exception as e:
        return USER_LIST\.copy\(\)''',
     '''def load_users_from_sheets(spreadsheet):
    """Load unique users from users table"""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return USER_LIST.copy()
        
        response = supabase.table("users").select("username").execute()
        if response.data:
            users = [user["username"] for user in response.data]
            return users if users else USER_LIST.copy()
        return USER_LIST.copy()
    except Exception as e:
        return USER_LIST.copy()'''),
    
    # load_user_pins_from_sheets
    (r'''def load_user_pins_from_sheets\(spreadsheet\):
    """Return a dict mapping usernames to their 4-digit PINs\."""
    pins = \{user: None for user in USER_LIST\}
    pins\[USER_PLACEHOLDER\] = None
    if not spreadsheet:
        return pins
    try:
        data = _load_sheet_data\("Users"\)
        for record in data:
            username = record\.get\("Username"\)
            if username:
                pins\[username\] = _normalize_pin_value\(record\.get\("PIN"\)\)
        return pins
    except Exception:
        return pins''',
     '''def load_user_pins_from_sheets(spreadsheet):
    """Return a dict mapping usernames to their 4-digit PINs."""
    pins = {user: None for user in USER_LIST}
    pins[USER_PLACEHOLDER] = None
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            return pins
            
        response = supabase.table("users").select("username, pin").execute()
        for user in response.data:
            username = user.get("username")
            if username:
                pins[username] = _normalize_pin_value(user.get("pin"))
        return pins
    except Exception:
        return pins'''),
]

# Apply replacements
for old, new in replacements:
    content = re.sub(old, new, content, flags=re.MULTILINE | re.DOTALL)

# Write back
with open('utils/helpers.py', 'w') as f:
    f.write(content)

print("✅ Phase 2 complete: User functions updated")
print("📝 Next: Bodyweight, activity, and settings functions...")
