import re
import os
import json
import shutil

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

        corrected = re.sub(r'^1-', 'I-', entry[2])
        if corrected != entry[2]:
            entry[2] = corrected

        corrected = re.sub(r'(?<!^)I', '1', entry[2])
        if corrected != entry[2]:
            entry[2] = corrected

        corrected = entry[2].replace('l', '1')
        if corrected != entry[2]:
            entry[2] = corrected

        if entry[2] != original_value:
            corrected_cue = entry[2]
            processing_errors.append((episode_num, part_label, entry.copy(), corrected_cue))

    return entry, corrected_cue

# Updated complete_fields function
def complete_fields(entry, episode_num, part_label):
    if len(entry) < 3 or len(entry) > 4:
        processing_errors.append((episode_num, part_label, entry.copy(), None))
    while len(entry) < 4:
        entry.insert(1, "—")
    return entry

json_filename = input("Enter the output JSON filename (without the extension): ").strip() + "_raw.json"
json_data = {
    "global_headers": {"A": "A パート", "B": "B パート"},
    "global_subheaders": ["M", "曲の内容", "クレジット", "秒"],
    "episodes": []
}

current_directory = os.getcwd()
data_directory = os.path.join(current_directory, 'Data')

if not os.path.exists(data_directory):
    print(f"Error: 'Data' directory not found in {current_directory}.")
    exit(1)

txt_files = [f for f in os.listdir(data_directory) if f.endswith('.txt')]

def clean_path(path):
    return path.strip('"').strip()

if not txt_files:
    text_file_path = input("Enter the full path of the text file to process: ").strip()
    text_file_path = clean_path(text_file_path)
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
    text_file_path = clean_path(os.path.join(data_directory, txt_files[choice - 1]))

print(f"Selected file path: {text_file_path}")

if not os.path.exists(text_file_path):
    print(f"Error: The file '{text_file_path}' does not exist.")
    exit(1)

try:
    with open(text_file_path, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print(f"Error: The file at '{text_file_path}' could not be found.")
    exit(1)

if not lines:
    print("Warning: The file is empty or contains only blank lines.")
else:
    print(f"Successfully read {len(lines)} lines.")

cleaned_lines = [
    re.sub(r"^\| (.*)", r"1\n\1",
           re.sub(r"(?<!\s)\+(?!\s)", " + ",
                  re.sub(r"//", "!!",
                         re.sub(r"^「", "",
                                re.sub(r"ライブラリー", "Ｌｉｂｒａｒｙ",
                                       re.sub(r"半", '.5"',
                                              re.sub(r"「第", '第',
                                                     re.sub(r"【第", '第', line))))))))
    for line in lines
    if not re.match(r"^(バート|M|曲の内容|クレジット|秒)$", line.strip())
]

episodes_data = {}
episode_pattern = re.compile(r"第(\d{1,3})話")
current_episode = None
current_episode_lines = []
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
        identified_episodes.append(int(current_episode))
    else:
        current_episode_lines.append(line)

if current_episode is not None:
    episodes_data[current_episode] = current_episode_lines
    identified_episodes.append(int(current_episode))

print(f"Found episodes: {identified_episodes}\n")

min_episode = min(identified_episodes)
max_episode = max(identified_episodes)
missing_episodes = [i for i in range(min_episode, max_episode + 1) if i not in identified_episodes]

if missing_episodes:
    input("Warning: The following episodes are missing from the sequence:")
    for missing_episode in missing_episodes:
        print(f"Episode {missing_episode}")
else:
    input("Nice! Every episode is here.")

episodes_parts = {}
for episode, data in episodes_data.items():
    part_top, part_a, part_b = [], [], []
    in_part_top = in_part_a = in_part_b = False
    for line in data:
        if line.startswith(("TOPパート", "TOP パート", "TOP")):
            in_part_top, in_part_a, in_part_b = True, False, False
            continue
        elif line.startswith(("Aパ", "A パ", "Aバ", "A バ", "Aハ", "A ハ")) or line.strip() == "A":
            in_part_top, in_part_a, in_part_b = False, True, False
            continue
        elif line.startswith(("Bパ", "B パ", "Bバ", "B バ", "Bハ", "B ハ")) or line.strip() == "B":
            in_part_top, in_part_a, in_part_b = False, False, True
            continue

        if in_part_top:
            part_top.append(line.replace("パート", "").strip())
        elif in_part_a and line.strip() != "パート":
            part_a.append(line)
        elif in_part_b and line.strip() != "パート":
            part_b.append(line)

    if not part_a:
        print(f"Error: Part A is missing in Episode {episode}.")
        input("Press Enter to exit...")
        raise ValueError(f"Error: Part A is missing in Episode {episode}.")
    if not part_b:
        print(f"Error: Part B is missing in Episode {episode}.")
        input("Press Enter to exit...")
        raise ValueError(f"Error: Part B is missing in Episode {episode}.")

    episode_parts = {"A": part_a, "B": part_b}
    if part_top:
        episode_parts["Top"] = part_top
    episodes_parts[episode] = episode_parts

    print(f"\n\nEpisode {episode}:")
    print(f"TOP: {episode_parts.get('Top', 'Not included')}")
    print(f"A: {part_a}")
    print(f"B: {part_b}")
print("Episodes divided into parts TOP, A, and B.\n\n")

input("Dividing parts into individual arrays...")

for episode, parts in episodes_parts.items():
    try:
        print(f"\n--- Debug: Processing Episode {episode} ---")
        episode_data = {"number": int(episode), "parts": {key: [] for key in parts.keys()}}

        for part_key, part_data in parts.items():
            print(f"Processing Part: {part_key}")
            output = []
            comparator = None
            temp_array = []

            try:
                for line in part_data:
                    if comparator is None:
                        match = re.match(r"(\d+)", line)
                        if match:
                            comparator = int(match.group(1))
                            temp_array.append(line)
                        else:
                            temp_array.append(line)
                    else:
                        match = re.match(r"(\d+)", line)
                        if match:
                            current_int = int(match.group(1))
                            if temp_array and re.match(r"^[A-Z1]-", temp_array[-1]):
                                temp_array.append(line)
                            else:
                                if current_int == comparator or current_int == comparator + 1:
                                    output.append(temp_array)
                                    temp_array = [line]
                                    comparator = current_int
                                else:
                                    temp_array.append(line)
                        else:
                            temp_array.append(line)
            except Exception as e:
                print(f"💥 Error while processing Episode {episode}, Part {part_key}")
                print(f"Line: {line}")
                print(f"Exception: {e}")
                input("Press Enter to continue...")

            if temp_array:
                output.append(temp_array)

            processed_part = []
            for entry in output:
                completed_entry = complete_fields(entry, episode, part_key)
                corrected_entry, corrected_cue = check_and_correct_cue(completed_entry, episode, part_key)
                processed_part.append(corrected_entry)

            print(processed_part)
            print("\n")

            for entry in processed_part:
                entry[-1] = process_time_field(entry[-1]).replace("mm", "s")

            episode_data["parts"][part_key].extend(processed_part)

        json_data["episodes"].append(episode_data)
    except Exception as e:
        print(f"\n[DEBUG ERROR] Episode {episode} failed.")
        print(f"Exception: {e}")
        input("Press Enter to continue...")

json_filepath = os.path.join(current_directory, json_filename)
with open(json_filepath, 'w', encoding='utf-8') as json_file:
    json.dump(json_data, json_file, ensure_ascii=False, indent=2)
input(f"\n\nJSON file '{json_filename}' created successfully at {json_filepath}")

faulty_array = "Array:"
cue = "Corrected Cue:"

processing_errors_sorted = sorted(
    processing_errors,
    key=lambda x: (f"{int(x[0]):03}", x[1], faulty_array if x[3] is None else cue)
)

error_filepath = os.path.join(current_directory, f"{json_filename.replace('.json', '')}_logs.txt")
current_episode = None

with open(error_filepath, 'w', encoding='utf-8') as error_file:
    for episode, part, entry, corrected_cue in processing_errors_sorted:
        formatted_episode = f"{int(episode):03}"
        if formatted_episode != current_episode:
            if current_episode is not None:
                error_file.write("\n")
            current_episode = formatted_episode
        display_episode = re.sub(r"^0+", "", formatted_episode)
        if corrected_cue is None:
            error_file.write(f"Episode {display_episode} ({part}) - {faulty_array} {entry}\n")

print(f"Processing logs written to '{error_filepath}'")

script_filename = os.path.basename(__file__)
backup_filename = os.path.splitext(script_filename)[0] + "_backup.py"
backup_path = os.path.join(data_directory, backup_filename)
shutil.copy(script_filename, backup_path)

input(f"Backup of the script created at: {backup_path}. Bye!")
