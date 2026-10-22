import os
import json
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

# Step 2: Process JSON for duplicates
value_to_key_map = {}
processed_data = {}

for key, value in data.items():
    if value in value_to_key_map:
        # If the value is a duplicate, reference the first key
        processed_data[key] = value_to_key_map[value]
    else:
        # If the value is unique, add it to the map
        value_to_key_map[value] = key
        processed_data[key] = value

# Step 3: Save the processed data back to a JSON file
output_file_path = os.path.join(data_directory, 'processed_' + os.path.basename(json_file_path))
with open(output_file_path, 'w', encoding='utf-8') as file:
    json.dump(processed_data, file, ensure_ascii=False, indent=4)

print(f"Processed JSON saved to: {output_file_path}")

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
