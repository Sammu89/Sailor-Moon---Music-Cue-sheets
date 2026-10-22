import json
import re
import os
import shutil

# Prompt user for JSON filename and provide explanation
print("Note: Headers are ['Μ-ΝΟ.', 'Time', '内容', '収録CD'].")
print("Sections start with '【' or '&', and the section name ends when 'TIME' is detected.")
print("Each data entry consists of four values in the order of headers.")

# Request JSON filename
json_filename = input("Enter the JSON filename (without .json extension): ").strip()
dataset_name = json_filename  # The dataset name is the same as the JSON filename

# Get the current directory
current_directory = os.getcwd()
# List all .txt files in the 'Data' folder inside the current directory
data_directory = os.path.join(current_directory, 'Data')

# Check if 'Data' directory exists
if not os.path.exists(data_directory):
    print(f"Error: 'Data' directory not found in {current_directory}.")
    exit(1)

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

print(f"Selected file path: {text_file_path}")

# Check if file exists
if not os.path.exists(text_file_path):
    print(f"Error: The file '{text_file_path}' does not exist.")
    exit(1)

# Prepare the log file
log_filename = f"{json_filename}_log.txt"
log_file_path = os.path.join(current_directory, log_filename)

try:
    log_file = open(log_file_path, 'w', encoding='utf-8')

    # Read and clean text file (remove empty lines and unwanted characters)
    with open(text_file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]
        unwanted_strings = ["収録CD", "内容", "M-NO.", "M-NO", "ΜΗΝΟ.", "曲タイトル", "內容"]

        # Remove each unwanted string from each line
        cleaned_lines = []
        for line in lines:
            for unwanted in unwanted_strings:
                line = line.replace(unwanted, "")
            if line.strip():
                cleaned_lines.append(line)

    print("Cleaned lines (debug):", cleaned_lines)
except Exception as e:
    print("An error occurred:", e)
    exit(1)

data = {
    dataset_name: {
        "Headers": ["Μ-ΝΟ.", "TIME", "内容", "収録CD"],
        "Sections": {}
    }
}

def process_time_field(time_value):
    time_value = time_value.replace("′", "'").replace("″", "\"").replace("°", "º").replace("º", "")
    time_value = time_value.replace("'", "min").replace("半", ".5")
    if re.fullmatch(r'\d+(\.\d+)?', time_value):
        time_value += "sec"
    return time_value

current_section = None
section_data = []
i = 0

while i < len(cleaned_lines):
    line = cleaned_lines[i]

    if line.startswith("【") or line.startswith("&"):
        if current_section and section_data:
            data[dataset_name]["Sections"][current_section] = section_data
            print(f"\nParsed Section: {current_section}")
            print("Data:", section_data)
            print("\n")

        section_data = []
        section_lines = [line[1:] if line.startswith("&") else line]
        i += 1

        while i < len(cleaned_lines) and "TIME" not in cleaned_lines[i]:
            section_lines.append(cleaned_lines[i])
            i += 1

        current_section = " ".join(section_lines).strip()

        if i < len(cleaned_lines) and "TIME" in cleaned_lines[i]:
            i += 1

    elif current_section:
        entry = []
        for j in range(4):
            if i >= len(cleaned_lines) or cleaned_lines[i].startswith("【") or cleaned_lines[i].startswith("&"):
                break  # End list early if a new section marker is found
            value = cleaned_lines[i]
            if j == 1:
                value = process_time_field(value)
            entry.append(value)
            i += 1

        if entry:
            section_data.append(entry)
            if not re.match(r'^[A-Z]-\d+$', entry[0]):
                # Log unexpected format to the log file
                log_file.write(f"Debug: Unexpected format in section '{current_section}' - {entry}\n")

# Store last section data after loop
if current_section and section_data:
    data[dataset_name]["Sections"][current_section] = section_data
    print(f"\nParsed Section: {current_section}")
    print("Data:", section_data)

# Replace 'mm' with 's' in all time fields, if the field exists and is a string
for section in data[dataset_name]["Sections"].values():
    for entry in section:
        if len(entry) > 1 and isinstance(entry[1], str):
            entry[1] = entry[1].replace("mm", "s")

output_path = f"{json_filename}.json"
with open(output_path, 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, ensure_ascii=False, indent=4)

print(f"\nJSON file '{output_path}' created successfully!")
input("\nPress ENTER to exit.")

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


# Close the log file
log_file.close()
print(f"Log file '{log_filename}' created at {log_file_path}.")
input("Press ENTER to leave!")