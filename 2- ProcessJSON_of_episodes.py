import os
import json
import re
import shutil

# Function to remove fields with "—"
def remove_extra_field_with_dash(episodes):
    for episode in episodes:
        parts = episode.get("parts", {})
        for part_name, part_lists in parts.items():
            for idx, item in enumerate(part_lists):
                if len(item) == 5 and "—" in item:
                    part_lists[idx] = [field for field in item if field != "—"]

# Setup for directories and files
current_directory = os.getcwd()
data_directory = current_directory
json_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]

# Select JSON file
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

# Validate selected file
if not os.path.exists(json_file_path):
    print(f"Error: The file '{json_file_path}' does not exist.")
    input("Press ENTER to exit.")
    exit(1)

# Load JSON data
input("Press ENTER to load and validate the JSON file.")
try:
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
except json.JSONDecodeError as e:
    print("\nError: Failed to decode JSON.")
    print(f"Details: {e}")
    input("Press ENTER to debug or check the file structure.")
    exit(1)

# If JSON is successfully loaded
episodes = data.get("episodes", [])
print(f"Number of episodes found: {len(episodes)}")

# Regex for valid first fields
valid_first_field_pattern = re.compile(r"^\d+['AaBbCc]?$")
validation_errors = []

# Helper function for unique string keys
string_index = {}
string_counter = 1

# Prompt user for custom key prefix and starting number
key_prefix = input("Enter the prefix for unique keys (default: 's'): ").strip() or "s"
while True:
    try:
        key_start = int(input(f"Enter the starting number for {key_prefix}_ (default: 1): ").strip() or "1")
        break
    except ValueError:
        print("Invalid input. Please enter a valid number.")

# Helper function for unique string keys
string_index = {}
string_counter = key_start

def get_unique_key(value):
    """Generate and return a unique key for a given value."""
    global string_counter
    # Check if the value already has a unique key
    for key, val in string_index.items():
        if val == value:
            return key
    # If not, create a new unique key and store it
    key = f"{key_prefix}_{string_counter}"
    string_index[key] = value
    string_counter += 1
    return key


# Process episodes
for episode in episodes:
    episode_number = episode.get("number", "Unknown")
    parts = episode.get("parts", {})
    for part_name, part_lists in parts.items():
        for idx, item in enumerate(part_lists):
            # Handle specific case where the first field starts with a number and is longer than 5 chars, and the second field is "—"
            if len(item) > 1 and re.match(r"^\d+", item[0]) and len(item[0]) > 5 and item[1] == "—":
                # Split the first field
                parts_of_first = item[0].split(maxsplit=1)
                if len(parts_of_first) == 2:
                    item[0], item[1] = parts_of_first[0], parts_of_first[1]
                else:
                    item[0] = parts_of_first[0]
                    item[1] = ""
                continue

            # Apply the unique key function to the second field (item[1])
            if len(item) > 1:  # Ensure the second field exists
                item[1] = get_unique_key(item[1])

            # Process the first field
            first_field = str(item[0])
            first_field = re.sub(r"(\d+)\.", r"\1'", first_field)
            first_field = re.sub(r"′", "'", first_field)
            first_field = re.sub(r"(\d+)A", r"\1a", first_field)
            first_field = re.sub(r"(\d+)B", r"\1b", first_field)
            first_field = re.sub(r"(\d+)C", r"\1c", first_field)
            item[0] = first_field

            # Validate the processed first field
            if not valid_first_field_pattern.match(first_field):
                validation_errors.append(
                    f"Episode {episode_number}, Part {part_name}, List index {idx}: invalid first field '{first_field}'"
                )


# Print validation errors if any
if validation_errors:
    print("\nValidation Errors:")
    for error in validation_errors:
        print(error)
    input("Press ENTER to exit.")
    exit(1)

# Remove extra fields and validate
remove_extra_field_with_dash(episodes)

# Save results
base_filename = os.path.basename(json_file_path)
if "_raw" in base_filename:
    base_filename = base_filename.replace("_raw", "")

output_json_path = os.path.join(os.path.dirname(json_file_path), os.path.splitext(base_filename)[0] + "_processed.json")
keys_json_path = os.path.join(os.path.dirname(json_file_path), os.path.splitext(base_filename)[0] + "_keys.json")

with open(output_json_path, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

with open(keys_json_path, 'w', encoding='utf-8') as file:
    json.dump(string_index, file, ensure_ascii=False, indent=4)

print(f"Processed JSON saved to {output_json_path}")
print(f"Keys JSON saved to {keys_json_path}")

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