import os
import json
import logging
import sys
from collections import defaultdict

# Configure logging for debug output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Absolute path to the string mapping file
MAPPING_FILE = r"G:\O meu disco\SM\MusicSheets\JSON Final\Key_Episódios_novas.txt"
# Directory containing JSON files to update (current directory)
JSON_DIR = os.getcwd()
# Backup suffix for safety
BACKUP_SUFFIX = '.bak'


def load_mapping(mapping_path):
    """
    Loads the string mapping from the text file.
    Each line should be: string_N: [key1, key2, ...]
    Returns dict original_key -> string_key
    """
    mapping = {}
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                string, rest = line.split(':', 1)
                string = string.strip()
                if '[' in rest and ']' in rest:
                    contents = rest.split('[', 1)[1].rsplit(']', 1)[0]
                    originals = [k.strip() for k in contents.split(',') if k.strip()]
                    for orig in originals:
                        mapping[orig] = string
        logging.info(f"Loaded {len(mapping)} mappings from {mapping_path}")
    except FileNotFoundError:
        logging.error(f"Mapping file not found: {mapping_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading mapping file '{mapping_path}': {e}")
        sys.exit(1)
    return mapping


def replace_in_obj(obj, mapping, counts):
    """
    Recursively replace keys and string values in obj according to mapping.
    counts: dict tracking replacements per original key.
    """
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_key = mapping.get(k, k)
            if new_key != k:
                counts[k] += 1
            new_dict[new_key] = replace_in_obj(v, mapping, counts)
        return new_dict
    elif isinstance(obj, list):
        return [replace_in_obj(item, mapping, counts) for item in obj]
    elif isinstance(obj, str):
        if obj in mapping:
            counts[obj] += 1
            return mapping[obj]
        return obj
    else:
        return obj


def main():
    mapping = load_mapping(MAPPING_FILE)
    summary = defaultdict(int)

    for filename in os.listdir(JSON_DIR):
        if not filename.lower().endswith('.json'):
            continue
        if filename == os.path.basename(MAPPING_FILE):
            continue
        filepath = os.path.join(JSON_DIR, filename)
        logging.info(f"Processing '{filename}'...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load JSON '{filename}': {e}")
            continue

        counts = defaultdict(int)
        new_data = replace_in_obj(data, mapping, counts)
        total_changes = sum(counts.values())

        if total_changes > 0:
            backup_path = filepath + BACKUP_SUFFIX
            os.rename(filepath, backup_path)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            logging.info(f"Updated '{filename}': {total_changes} replacements; backup at '{backup_path}'")
            for orig_key, cnt in counts.items():
                summary[orig_key] += cnt
        else:
            logging.info(f"No replacements in '{filename}'")

    # Print summary of all replacements
    print("\nSummary of replacements:")
    for orig, cnt in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"{orig} -> {mapping.get(orig)}: {cnt} times")
    print(f"Processed all JSON files in '{JSON_DIR}'.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error during processing: {e}", exc_info=True)
    finally:
        # Ensure pause even if errors occur
        try:
            input("\nFinished (with or without errors). Press Enter to exit...")
        except EOFError:
            pass
