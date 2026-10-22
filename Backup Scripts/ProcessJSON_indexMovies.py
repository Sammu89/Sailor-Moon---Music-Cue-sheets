import os
import json
import re
import shutil
# Step 1: Select JSON File
current_directory = os.getcwd()
data_directory = os.path.join(current_directory, 'Data')

# Check if 'Data' directory exists
if not os.path.exists(data_directory):
    print(f"Error: 'Data' directory not found in {current_directory}.")
    exit(1)

json_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]

# If no JSON files found, prompt user for file path
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

# Check if file exists
if not os.path.exists(json_file_path):
    print(f"Error: The file '{json_file_path}' does not exist.")
    exit(1)
input("Press ENTER toLoad and Validate JSON Structure.")
# Step 2: Load and Validate JSON Structure
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)
# Step 3: Function to Process the Time Field
def process_time_field(time_value):
    # Rule 1: Replace "ms" with "."
    time_value = re.sub(r'(\d+)ms(\d*)', r'\1.\2', time_value)

    # Rule 2: Add "s" for purely numerical values
    if re.match(r'^\d+(\.\d+)?$', time_value):
        time_value += 's'

    # Rule 3: Handle minute/second format
    if re.match(r'^\d+m\d+(\.\d+)?$', time_value) and not time_value.endswith(('s', 'm')):
        time_value += 's'

    return time_value

# Step 4: Process Data Field Globally Across All Lists
keys_mapping = {}
key_counter = 1

def get_key(value):
    global key_counter
    if value not in keys_mapping.values():
        key_name = f"Im_{key_counter}"
        keys_mapping[key_name] = value
        key_counter += 1
    # Return the key associated with the value
    return [key for key, val in keys_mapping.items() if val == value][0]

def process_movie_lists(lists):
    for entry in lists:
        # Process Time Field (3rd field)
        entry[2] = process_time_field(entry[2].strip())

        # Process Data Field (4th field)
        entry[3] = get_key(entry[3].strip())

# Step 5: Process Every List in Every Movie
for movie in data["movies"]:
    if "lists" in movie:
        process_movie_lists(movie["lists"])

# Step 6: Save Processed Data and Keys
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
