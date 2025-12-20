#!/usr/bin/env python3
"""
Script to remove all spreadsheet parameters from function definitions and calls
"""
import re

# Read the helpers.py file
with open('utils/helpers.py', 'r') as f:
    content = f.read()

# List of functions to update (remove spreadsheet parameter)
functions_to_update = [
    'get_last_workout',
    'get_bodyweight',
    'get_bodyweight_history',
    'set_bodyweight',
    'get_user_1rms',
    'get_user_1rm',
    'get_working_max',
    'update_user_1rm',
    'add_new_user',
    'delete_user',
    'log_activity_to_sheets',
    'load_activity_log',
    'load_custom_workout_logs',
    'get_user_custom_workouts',
    'load_goals',
    'save_goal',
    'complete_goal',
    'delete_goal',
    'log_custom_workout',
    'get_user_setting',
    'set_user_setting',
    'change_user_pin',
    'get_endurance_training_enabled',
    'set_endurance_training_enabled',
    'get_workout_count',
    'increment_workout_count',
    'reset_workout_count',
    'save_custom_workout',
    'delete_custom_workout'
]

# Remove spreadsheet parameter from function definitions
for func in functions_to_update:
    # Pattern: def func(spreadsheet, other_params)
    content = re.sub(
        rf'def {func}\(spreadsheet,\s*',
        f'def {func}(',
        content
    )
    # Pattern: def func(other_params, spreadsheet)
    content = re.sub(
        rf'def {func}\(([^)]+),\s*spreadsheet\)',
        rf'def {func}(\1)',
        content
    )

# Save the updated file
with open('utils/helpers.py', 'w') as f:
    f.write(content)

print("✅ Updated utils/helpers.py - removed spreadsheet parameters from function definitions")
