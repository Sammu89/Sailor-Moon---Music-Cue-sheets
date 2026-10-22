import json
import os
import re
import logging
import sys


def main():
    try:
        # 1) Prompt (accept path with or without quotes)
        file_path = input("Enter path to JSON file: ").strip().strip('"').strip("'")
        start_string_str = input("Enter starting index number: ").strip()
        try:
            start_index = int(start_string_str)
        except ValueError:
            print(f"Invalid starting index '{start_string_str}'. Must be an integer.")
            sys.exit(1)

        # Prepare output paths
        base, ext = os.path.splitext(file_path)
        references_path = f"{base}_references.json"
        error_log_path = f"{base}_errors.log"

        # 2) Logging setup (console + file)
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        logger = logging.getLogger()
        fh = logging.FileHandler(error_log_path, encoding="utf-8")
        fh.setLevel(logging.ERROR)
        fh.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(fh)

        # 3) Load JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read '{file_path}': {e}")
            print(f"Failed to read '{file_path}': {e}")
            sys.exit(1)

        # 4) Build reference mapping and replace in data
        mapping = {}
        idx = start_index

        root_key = next(iter(data))
        section_root = data[root_key]

        # Headers
        orig_headers = section_root.get("Headers", [])
        for h in orig_headers:
            mapping[h] = f"string_{idx}"
            idx += 1
        section_root["Headers"] = [mapping[h] for h in orig_headers]

        # Sections (keys)
        orig_sections = section_root.get("Sections", {})
        new_sections = {}
        for sec_name, items in orig_sections.items():
            mapping[sec_name] = f"string_{idx}"
            new_key = mapping[sec_name]
            new_sections[new_key] = items
            idx += 1
        section_root["Sections"] = new_sections

        # 5) Validate & auto‑fix each 4‑element list in every section
        pat1 = re.compile(r"^[A-Za-z].*")
        pat2 = re.compile(r"^(?:\d+(?:\.\d+)?m\d+(?:\.\d+)?s|\d+(?:\.\d+)?s)$")
        pat3 = re.compile(r"^(?:is_|im_|s_)\d+$|^string_\d+$")
        pat4 = re.compile(r"^\d+(?:-\d+)*$")
        pat_jp = re.compile(r"[\u3040-\u30ff\u4e00-\u9faf]")  # Japanese characters

        errors = []
        for sec_key, items in section_root["Sections"].items():
            for i, item in enumerate(items, start=1):
                try:
                    if not (isinstance(item, list) and len(item) == 4):
                        msg = f"{sec_key} #{i}: expected 4‑element list, got {item!r}"
                        errors.append(msg); logger.error(msg)
                        continue

                    # Unpack fields
                    f1, f2, f3, f4 = item

                    # Auto‑fix field2
                    if f2 == "-s":
                        item[1] = "-"
                        f2 = "-"
                    elif f2.endswith("mm"):
                        item[1] = f2[:-2] + "s"
                        f2 = item[1]

                    # Detect and map Japanese in field1
                    if pat_jp.search(f1):
                        mapping[f1] = f"string_{idx}"
                        item[0] = mapping[f1]
                        logger.info(f"Mapped Japanese f1 '{f1}' to {mapping[f1]}")
                        idx += 1
                        f1 = item[0]

                    # Map field3 if it doesn't start with is_|im_|s_
                    if not re.match(r'^(?:is_|im_|s_)\d+$', f3):
                        mapping[f3] = f"string_{idx}"
                        item[2] = mapping[f3]
                        logger.info(f"Mapped field3 '{f3}' to {mapping[f3]}")
                        idx += 1
                        f3 = item[2]

                    # Validation
                    if not pat1.match(f1):
                        msg = f"{sec_key} #{i} field1 '{f1}' invalid"
                        errors.append(msg); logger.error(msg)
                    if not pat2.match(f2):
                        msg = f"{sec_key} #{i} field2 '{f2}' invalid"
                        errors.append(msg); logger.error(msg)
                    if not pat3.match(f3):
                        msg = f"{sec_key} #{i} field3 '{f3}' invalid"
                        errors.append(msg); logger.error(msg)
                    if not pat4.match(f4):
                        msg = f"{sec_key} #{i} field4 '{f4}' invalid"
                        errors.append(msg); logger.error(msg)

                except Exception as item_e:
                    err = f"{sec_key} #{i} processing error: {item_e}"
                    errors.append(err); logger.error(err)
                    continue

        if errors:
            print(f"Validation finished with {len(errors)} error(s). See '{error_log_path}'.")
        else:
            print("Validation passed with no errors.")

        # 6) Write back modified JSON
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Updated JSON written to '{file_path}'.")
        except Exception as e:
            logger.error(f"Failed to write updated JSON: {e}")
            print(f"Failed to write updated JSON: {e}")
            sys.exit(1)

        # 7) Invert mapping and write references file
        mapping_inv = {v: k for k, v in mapping.items()}
        try:
            with open(references_path, 'w', encoding='utf-8') as f:
                json.dump(mapping_inv, f, ensure_ascii=False, indent=4)
            print(f"Reference mapping written to '{references_path}'.")
        except Exception as e:
            logger.error(f"Failed to write references file: {e}")
            print(f"Failed to write references file: {e}")
            sys.exit(1)

    except Exception as e:
        # Catch-all for unexpected errors
        logger = logging.getLogger()
        logger.exception("Unexpected fatal error")
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
        logging.error("Unhandled exception in main invocation", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)
input()