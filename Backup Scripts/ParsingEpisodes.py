import re 
import os 
import json 



# Helper function to process the Time field
def process_time_field(time_value):
    time_value = time_value.replace("′", "'").replace("″", "\"").replace("°", "º").replace("º", "").replace("\"", "")
    time_value = time_value.replace("'", "m").replace("半", ".5")
    if re.fullmatch(r'\d+(\.\d+)?', time_value):  
        time_value += "s"
    return time_value

processing_errors = []

# Helper function to check and correct the third element pattern
def check_and_correct_cue(entry, episode_num, part_label):
    corrected_cue = None
    if len(entry) >= 4 and re.match(r'^[A-Z1]-\s*', entry[2]):
        original_value = entry[2]
        
        # Perform substitutions, checking each for changes
        corrected = re.sub(r'^1-', 'I-', entry[2])  # Step 1
        if corrected != entry[2]:  # Log only if the first substitution was effective
            entry[2] = corrected
        
        corrected = re.sub(r'(?<!^)I', '1', entry[2])  # Step 2
        if corrected != entry[2]:  # Log only if the second substitution was effective
            entry[2] = corrected
        
        corrected = entry[2].replace('l', '1')  # Step 3
        if corrected != entry[2]:  # Log only if the third substitution was effective
            entry[2] = corrected

        # Log only if the final result differs from the original
        if entry[2] != original_value:
            corrected_cue = entry[2]
            processing_errors.append((episode_num, part_label, entry.copy(), corrected_cue))
            
    return entry, corrected_cue

# Updated complete_fields function
def complete_fields(entry, episode_num, part_label):
    if len(entry) < 3 or len(entry) > 4:  # Trigger if the length is less than 3 or greater than 4
        # Log as an incomplete entry without a correction cue
        processing_errors.append((episode_num, part_label, entry.copy(), None))
    while len(entry) < 4:  # Ensure the entry has at least 4 elements, filling with "—" if necessary
        entry.insert(1, "—")
    return entry


# Prompt user for JSON filename 
json_filename = input("Enter the JSON filename (without .json extension): ").strip() + "_raw.json"
json_data = {
    "global_headers": {"A": "A パート", "B": "B パート"},
    "global_subheaders": ["M", "曲の内容", "クレジット", "秒"],
    "episodes": []
}

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

# Debug: print the chosen file path to check correctness
print(f"Selected file path: {text_file_path}")

# Check if file exists
if not os.path.exists(text_file_path):
    print(f"Error: The file '{text_file_path}' does not exist.")
    exit(1)

# Read and clean text file 
try:
    with open(text_file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print(f"Error: The file at '{text_file_path}' could not be found.")
    exit(1)

# Debug: Check if lines are read correctly
if not lines:
    print("Warning: The file is empty or contains only blank lines.")
else:
    print(f"Successfully read {len(lines)} lines.")


# Processing lines
cleaned_lines = [
    re.sub(r"^\| (.*)", r"1\n\1",  # Replace '|' with '1' and add line break
           re.sub(r"(?<!\s)\+(?!\s)", " + ",  # Add spaces around '+' if missing
                  re.sub(r"//", "!!",  # Replace '//' with '!!'
                         re.sub(r"^「", "",  # Remove '「' if the line starts with it
                                re.sub(r"ライブラリー", "Ｌｉｂｒａｒｙ",  # Replace 'ライブラリー' with 'Ｌｉｂｒａｒｙ'
                                       re.sub(r"半", '.5"',  # Replace '半' with '.5'
                                              re.sub(r"「第", '第',  # Replace '「第' with '第'
                                                     re.sub(r"【第", '第', line))))))))
    for line in lines
    # Skip lines that are exactly "バート", "M", "曲の内容", "クレジット", or "秒"
    if not re.match(r"^(バート|M|曲の内容|クレジット|秒)$", line.strip())
]

# Identify episodes using "第+number" pattern
episodes_data = {}
episode_pattern = re.compile(r"第(\d{1,3})話")
current_episode = None
current_episode_lines = []

# List to store identified episode numbers for later comparison
identified_episodes = []

for line in cleaned_lines:
    match = episode_pattern.match(line)
    if match:
        if current_episode is not None:
            episodes_data[current_episode] = current_episode_lines
            print(f"Found episode {current_episode}.")
        episode_number = match.group(1)
        current_episode = episode_number[:3]
        current_episode_lines = []
        identified_episodes.append(int(current_episode))  # Store episode number as integer for comparison
    else:
        current_episode_lines.append(line)

if current_episode is not None:
    episodes_data[current_episode] = current_episode_lines
    identified_episodes.append(int(current_episode))  # Store the last episode

print(f"Found episodes: {identified_episodes}\n")

# Check for missing episodes in the sequence
min_episode = min(identified_episodes)
max_episode = max(identified_episodes)

missing_episodes = [i for i in range(min_episode, max_episode + 1) if i not in identified_episodes]

if missing_episodes:
    input("Warning: The following episodes are missing from the sequence:")
    for missing_episode in missing_episodes:
        print(f"Episode {missing_episode}")
else:
    input("Nice! Every episode is here.")

# Divide each episode into parts TOP, A, and B
episodes_parts = {}
for episode, data in episodes_data.items():
    part_top, part_a, part_b = [], [], []
    in_part_top = in_part_a = in_part_b = False
    for line in data:
        # Detect the start of TOP
        if line.startswith(("TOPパート", "TOP パート", "TOP")):
            in_part_top, in_part_a, in_part_b = True, False, False
            continue

        # Detect the start of Part A
        elif line.startswith(("Aパ", "A パ", "Aバ", "A バ", "Aハ", "A ハ")) or line.strip() == "A":
            in_part_top, in_part_a, in_part_b = False, True, False
            continue

        # Detect the start of Part B
        elif line.startswith(("Bパ", "B パ", "Bバ", "B バ", "Bハ", "B ハ")) or line.strip() == "B":
            in_part_top, in_part_a, in_part_b = False, False, True
            continue

        # Store lines in the correct part
        if in_part_top:
            part_top.append(line.replace("パート", "").strip())
        elif in_part_a and line.strip() != "パート":
            part_a.append(line)
        elif in_part_b and line.strip() != "パート":
            part_b.append(line)

    # Check for missing parts and raise errors if necessary
    if not part_a:
        print(f"Error: Part A is missing in Episode {episode}.")
        input("Press Enter to exit...")  
        raise ValueError(f"Error: Part A is missing in Episode {episode}.")
    if not part_b:
        print(f"Error: Part B is missing in Episode {episode}.")
        input("Press Enter to exit...")  
        raise ValueError(f"Error: Part B is missing in Episode {episode}.")

    # Prepare the parts dictionary
    episode_parts = {
        "A": part_a,
        "B": part_b
    }

    # Add TOP part only if it is not empty
    if part_top:
        episode_parts["Top"] = part_top

    # Store the parts for the episode
    episodes_parts[episode] = episode_parts

    print(f"\n\nEpisode {episode}:")
    print(f"TOP: {episode_parts.get('Top', 'Not included')}")
    print(f"A: {part_a}")
    print(f"B: {part_b}")
print("Episodes divided into parts TOP, A, and B.\n\n")

# Process episodes parts and prepare final JSON structure
input("Dividing parts into individual arrays...")

# Loop over each episode and its associated parts
for episode, parts in episodes_parts.items():
    # Initialize episode data with the episode number and empty parts structure
    episode_data = {"number": int(episode), "parts": {"A": [], "B": []}}

    # Loop through each part (A or B) and its data
    for part_key, part_data in parts.items():
        output = []  # This will hold the processed output for each part
        comparator = None  # Comparator to track line indices
        temp_array = []  # Temporary array to collect lines until a new section is identified

        # Process each line in the part's data
        for line in part_data:
            if comparator is None:
                # If comparator is not set, try to initialize it with a matched integer at the start of the line
                match = re.match(r"(\d+)", line)
                if match:
                    comparator = int(match.group(1))  # Set comparator to the matched integer
                    temp_array.append(line)  # Start a new section with this line
                else:
                    temp_array.append(line)  # Add non-matching line to temp_array
            else:
                # Match integer at the start of the line for comparison
                match = re.match(r"(\d+)", line)
                if match:
                    current_int = int(match.group(1))  # Get current line index as an integer

                    # Check if the last line in temp_array matches a specific pattern
                    if temp_array and re.match(r"^[A-Z1]-", temp_array[-1]):
                        # If last line in temp_array matches pattern, continue appending lines
                        temp_array.append(line)
                    else:
                        # Otherwise, check if the current line should start a new section
                        if current_int == comparator or current_int == comparator + 1:
                            output.append(temp_array)  # Add the current section to output
                            temp_array = [line]  # Start a new section
                            comparator = current_int  # Update comparator
                        else:
                            temp_array.append(line)  # Continue appending to temp_array if no new section
                else:
                    temp_array.append(line)  # Append non-matching line to temp_array

        # Append any remaining lines in temp_array to the output
        if temp_array:
            output.append(temp_array)

        # Process each entry in the output to complete fields and correct cues
        processed_part = []
        for entry in output:
            # Complete any missing fields in the entry
            completed_entry = complete_fields(entry, episode, part_key)
            # Check and correct cues in the completed entry
            corrected_entry, corrected_cue = check_and_correct_cue(completed_entry, episode, part_key)
            processed_part.append(corrected_entry)

        # Print processed part for debugging
        print(processed_part)
        print("\n")

        # Process the last field (cue) in each entry and replace 'mm' with 's' in time formats
        for entry in processed_part:
            entry[-1] = process_time_field(entry[-1]).replace("mm", "s")

        # Add the processed entries for this part (A or B) to the episode data
        episode_data["parts"][part_key].extend(processed_part)

    # Append the completed episode data to the JSON structure
    json_data["episodes"].append(episode_data)


json_filepath = os.path.join(current_directory, json_filename)
with open(json_filepath, 'w', encoding='utf-8') as json_file:
    json.dump(json_data, json_file, ensure_ascii=False, indent=2)
input(f"\n\nJSON file '{json_filename}' created successfully at {json_filepath}")




# Define labels for different types of log entries
faulty_array = "Array:"
cue = "Corrected Cue:"

# Sort processing_errors by episode, then part (A before B), and then by type of log entry
processing_errors_sorted = sorted(
    processing_errors,
    key=lambda x: (f"{int(x[0]):03}", x[1], faulty_array if x[3] is None else cue)
)

# Write processing errors to a text file with line breaks between episodes
error_filepath = os.path.join(current_directory, f"{json_filename.replace('.json', '')}_logs.txt")
current_episode = None

with open(error_filepath, 'w', encoding='utf-8') as error_file:
    for episode, part, entry, corrected_cue in processing_errors_sorted:
        # Format the episode number with leading zeros for sorting
        formatted_episode = f"{int(episode):03}"
        
        # Check if we're starting a new episode and add a line break if so
        if formatted_episode != current_episode:
            if current_episode is not None:  # Avoid line break at the start
                error_file.write("\n")  # Add a line break between episodes
            current_episode = formatted_episode

        # Finalize episode number formatting by removing leading zeros in '第0' or '第00'
        display_episode = re.sub(r"^0+", "", formatted_episode)  # Remove leading zeros for display

        # Write the error entry
        if corrected_cue is None:
            error_file.write(f"Episode {display_episode} ({part}) - {faulty_array} {entry}\n")
        else:
            continue
            
            # error_file.write(f"Episode 第{display_episode}話 - Part {part} - {cue} {corrected_cue}\n")

print(f"Processing logs written to '{error_filepath}'")

import shutil

# Get the current script file name
script_filename = os.path.basename(__file__)  # Get the filename of the current script
backup_filename = os.path.splitext(script_filename)[0] + "_backup.py"
# Make a backup by copying the script file to the 'Data' folder
backup_path = os.path.join(data_directory, backup_filename)
shutil.copy(script_filename, backup_path)


input(f"Backup of the script created at: {backup_path}. Bye!")