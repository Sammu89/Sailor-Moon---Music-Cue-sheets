import re
import os
import json
import shutil
# Prompt user for JSON filename
json_filename = input("Enter the JSON filename (without .json extension): ").strip() + "_raw.json"
json_data = {
    "headers": ["M", "曲の内容", "クレジット", "秒"],
    "movies": []
}

# Get the current directory and set data folder
current_directory = os.getcwd()
data_directory = os.path.join(current_directory, 'Data')

# Check if 'Data' directory exists
if not os.path.exists(data_directory):
    input(f"Error: 'Data' directory not found in {current_directory}. Press Enter to exit.")
    exit(1)

# List all .txt files in the 'Data' folder
txt_files = [f for f in os.listdir(data_directory) if f.endswith('.txt')]

# If there are no .txt files, prompt the user for the file path
if not txt_files:
    text_file_path = input("Enter the full path of the text file (default: 'C:\\Users\\Sammu\\Desktop\\Cues\\season1.txt'): ").strip()
else:
    print("Please select the input text file:")
    for i, file in enumerate(txt_files, 1):
        print(f"{i}. {file}")
    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(txt_files):
                break
            else:
                print("Invalid choice. Please enter a number between 1 and", len(txt_files))
        except ValueError:
            print("Invalid input. Please enter a number.")
    text_file_path = os.path.join(data_directory, txt_files[choice - 1])

# Check if file exists
if not os.path.exists(text_file_path):
    input(f"Error: The file '{text_file_path}' does not exist. Press Enter to exit.")
    exit(1)

# Debug: confirm file selection
print(f"Selected file path: {text_file_path}")
input("Press Enter to continue...")

# Read and clean text file
try:
    with open(text_file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]
    print("File read successfully.")
    input("Press Enter to continue...")
except FileNotFoundError:
    input(f"Error: The file at '{text_file_path}' could not be found. Press Enter to exit.")
    exit(1)

# Start processing episodes based on "&" identifier and "NO." for cue lists
episodes_data = {}
current_episode = []
current_list = []
recording = False

for line in lines:
    print(f"Processing line: {line}")  # Debugging line

    # If the line starts with "&", we begin a new episode
    if line.startswith("&"):
        # Save the previous episode if there was one
        if current_episode:
            episodes_data[' '.join(current_episode)] = current_list

        # Extract the episode name by concatenating lines starting with "&"
        current_episode = [line[1:].strip()]  # Start with the first part after "&"
        current_list = []
        recording = False  # Reset recording until we encounter a line with "CD"
        print(f"New Episode Detected: {current_episode[-1]}")

    # If "NO." appears, that ends the episode's name (we don't include it)
    elif "NO." in line and current_episode:
        print(f"Episode name completed: {' '.join(current_episode)}")
        continue  # Skip to next part, as episode name is now complete

    # Start recording lists after detecting any "CD" in the line (more flexible)
    elif "CD" in line:
        recording = True
        print(f"Starting list collection for episode: {' '.join(current_episode)}")
        input("Press Enter to continue...")

    elif recording:
        # Process list entries, assuming 5 fields per entry
        # We'll skip the regular expression matching and just focus on list formatting
        # Example format: 1 M-201 1'05° TVのセーラームーンのプロローグ調 8-1
        parts = line.split()
        if len(parts) >= 5:
            # Directly handle the 5 fields for list entry
            entry = parts[:5]  # We take the first 5 parts
            current_list.append(entry)
        else:
            # If the line doesn't have 5 parts, log it for review
            with open("log.txt", "a", encoding='utf-8') as log_file:
                log_file.write(f"Invalid list entry: {line}\n")

# If there was an ongoing episode, store it at the end
if current_episode:
    episodes_data[' '.join(current_episode)] = current_list

# Check the resulting episode data
print(f"Processed episodes: {episodes_data.keys()}")

# Now save the results to the JSON file
json_data = {
    "headers": ["M", "曲の内容", "クレジット", "秒"],
    "movies": [{"name": name, "list": entries} for name, entries in episodes_data.items()]
}

json_filename = "Movieeees_raw.json"
json_filepath = os.path.join(current_directory, json_filename)
with open(json_filepath, 'w', encoding='utf-8') as json_file:
    json.dump(json_data, json_file, ensure_ascii=False, indent=2)

print(f"\n\nJSON file '{json_filename}' created successfully at {json_filepath}")
input("Press Enter to finish processing.")


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
