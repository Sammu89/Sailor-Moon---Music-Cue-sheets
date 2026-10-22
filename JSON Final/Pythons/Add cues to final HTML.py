#!/usr/bin/env python3
"""
Script to augment JSON files starting with 'S' in a given folder by inserting cue values
from corresponding entries in another set of JSON files.

Usage (console):
    python augment_json_cues.py <folder_a> <folder_b>

If run by double-click, you'll be prompted for input paths, and the window will stay open
until you press Enter.

This version also logs all missing code mappings to a TXT file named 'missing_references.txt'
in the target folder, listing unique codes only, sorted alphabetically.

It now captures mapping codes from any array of strings length>=4:
- For lists of length>=5, it treats element[1] as the code, element[-1] as the cue.
- For lists of exactly 4, it treats element[0] as the code, element[-1] as the cue.
"""
import os
import sys
import json
import logging


def strip_quotes(path):
    """
    Remove surrounding single or double quotes from a path string, if present.
    """
    if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
        return path[1:-1]
    return path


def build_code_mapping(folder):
    """
    Walk through all .json files in `folder`, find lists of strings length>=4,
    and build a mapping from the code element to the cue element:
      - length>=5: code=obj[1], cue=obj[-1]
      - length==4: code=obj[0], cue=obj[-1]
    """
    mapping = {}
    for fname in os.listdir(folder):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path) or not fname.lower().endswith('.json'):
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load JSON %s: %s", path, e)
            continue

        def traverse(obj):
            if isinstance(obj, list):
                if all(isinstance(el, str) for el in obj) and len(obj) >= 4:
                    if len(obj) >= 5:
                        code = obj[1]
                    else:
                        code = obj[0]
                    if code not in mapping:
                        mapping[code] = obj[-1]
                for item in obj:
                    traverse(item)
            elif isinstance(obj, dict):
                for value in obj.values():
                    traverse(value)

        traverse(data)
    logging.info("Built mapping with %d codes", len(mapping))
    return mapping


def process_folder_b(folder, mapping):
    """
    Process each JSON file in `folder` starting with 'S'.
    Insert cue (or '?') at index 3 for entries of length>=4, then save with '_cues'.
    Also collect any missing mapping codes and write them uniquely sorted.
    """
    missing_codes = set()

    for fname in os.listdir(folder):
        if not fname.startswith('S') or not fname.lower().endswith('.json'):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load JSON %s: %s", path, e)
            continue

        episodes = data.get('episodes')
        if not isinstance(episodes, list):
            logging.warning("No 'episodes' list in %s", path)
            continue

        for ep in episodes:
            parts = ep.get('parts') if isinstance(ep, dict) else None
            if not isinstance(parts, dict):
                continue
            for lists in parts.values():
                if not isinstance(lists, list):
                    continue
                for entry in lists:
                    if isinstance(entry, list) and len(entry) >= 4:
                        code = entry[2]
                        cue = mapping.get(code, '?')
                        entry.insert(3, cue)
                        if cue == '?':
                            missing_codes.add(code)
                            logging.warning("No mapping for code '%s' in %s", code, path)

        out_path = os.path.join(folder, os.path.splitext(fname)[0] + '_cues.json')
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            logging.info("Wrote updated file: %s", out_path)
        except Exception as e:
            logging.error(f"Failed to write JSON %s: %s", out_path, e)

    # Write unique missing codes sorted alphabetically
    if missing_codes:
        sorted_codes = sorted(missing_codes)
        log_path = os.path.join(folder, 'missing_references.txt')
        try:
            with open(log_path, 'w', encoding='utf-8') as lf:
                for code in sorted_codes:
                    lf.write(code + "\n")
            logging.info("Wrote unique missing references log: %s", log_path)
        except Exception as e:
            logging.error(f"Failed to write missing references log %s: %s", log_path, e)


def prompt_paths():
    a = input("Enter path to folder A (first batch): ").strip()
    b = input("Enter path to folder B (second batch, S*.json): ").strip()
    return strip_quotes(a), strip_quotes(b)


def main():
    if len(sys.argv) >= 3:
        folder_a, folder_b = strip_quotes(sys.argv[1]), strip_quotes(sys.argv[2])
    else:
        print("No paths provided via command line. Enter interactively below.")
        folder_a, folder_b = prompt_paths()

    if not os.path.isdir(folder_a):
        print(f"ERROR: Folder A not found: {folder_a}")
        return
    if not os.path.isdir(folder_b):
        print(f"ERROR: Folder B not found: {folder_b}")
        return

    mapping = build_code_mapping(folder_a)
    process_folder_b(folder_b, mapping)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    try:
        main()
    except Exception as e:
        print(f"Unexpected error: {e}")
    input("\nProcessing complete. Press Enter to exit...")
