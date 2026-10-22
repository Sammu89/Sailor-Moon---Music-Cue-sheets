import os
import json
import re
import shutil
# Step 1: Select JSON File
current_directory = os.getcwd()
data_directory = os.path.join(current_directory, 'Data')

if not os.path.exists(data_directory):
    print(f"Error: 'Data' directory not found in {current_directory}.")
    exit(1)

json_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]

if not json_files:
    json_file_path = input("Enter the full path of the JSON file: ").strip()
else:
    print("Please select the input JSON file:")
    for i, file in enumerate(json_files, 1):
        print(f"{i}. {file}")
    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(json_files):
                break
            else:
                print("Invalid choice. Please enter a number between 1 and", len(json_files))
        except ValueError:
            print("Invalid input. Please enter a number.")
    json_file_path = os.path.join(data_directory, json_files[choice - 1])

if not os.path.exists(json_file_path):
    print(f"Error: The file '{json_file_path}' does not exist.")
    exit(1)

input("Press ENTER to load and validate JSON structure.")
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Step 2: Prompt for starting index
while True:
    try:
        starting_index = int(input("Enter the starting index for Is_number (e.g., 1 for Is_1): "))
        if starting_index > 0:
            break
        else:
            print("The starting index must be a positive integer.")
    except ValueError:
        print("Invalid input. Please enter a positive integer.")

# Step 3: Function to process time fields
def process_time_field(time_value):
    time_value = time_value.replace("min", "m")
    time_value = time_value.replace("sec", "s")
    time_value = re.sub(r'(\d+)ms(\d*)', r'\1.\2', time_value)
    time_value = time_value.replace('"', "s")
    if not re.search(r'[ms]$', time_value):
        time_value += 's'
    return time_value

# Step 4: Process data field globally across all lists
keys_mapping = {}

def get_key(value):
    global starting_index
    if value not in keys_mapping.values():
        key_name = f"Is_{starting_index}" #Is_ = index_season
        keys_mapping[key_name] = value
        starting_index += 1
    # Return the key associated with the value
    return [key for key, val in keys_mapping.items() if val == value][0]

def process_sections(sections):
    for section_name, lists in sections.items():
        for entry in lists:
            entry[1] = process_time_field(entry[1].strip())
            entry[2] = get_key(entry[2].strip())

# Step 5: Process every section in the JSON
for index_name, index_data in data.items():
    if isinstance(index_data, dict) and "Sections" in index_data:
        process_sections(index_data["Sections"])

# Step 6: Save processed data and keys
output_file_path = json_file_path.replace(".json", "_processed.json")
keys_file_path = json_file_path.replace(".json", "_keys.json")

with open(output_file_path, 'w', encoding='utf-8') as processed_file:
    json.dump(data, processed_file, ensure_ascii=False, indent=4)

with open(keys_file_path, 'w', encoding='utf-8') as keys_file:
    json.dump(keys_mapping, keys_file, ensure_ascii=False, indent=4)

print(f"Processed JSON saved to {output_file_path}")
print(f"Keys JSON saved to {keys_file_path}")

# Backup script
try:
    # Define the backup folder
    backup_folder = os.path.join(data_directory, "Backup Scripts")
    
    # Check if the backup folder exists, create it if it doesn't
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # Get the script filename and create a backup filename
    script_filename = os.path.basename(__file__)
    backup_filename = os.path.splitext(script_filename)[0] + "_backup.py"
    
    # Define the full backup path
    backup_path = os.path.join(backup_folder, backup_filename)
    
    # Copy the script to the backup folder
    shutil.copy(script_filename, backup_path)
    
    print(f"Backup of the script created at: {backup_path}")
except Exception as e:
    print(f"Error creating backup: {e}")

input("Press ENTER to exit.")
