import json
from pathlib import Path

# File paths
base_dir = Path(__file__).resolve().parent
main_json_path = base_dir / "Keys_String_Combined.json"
output_json_path = base_dir / "Keys_String_Extracted_Subset.json"
text_output_path = base_dir / "entries_with_less_than_5_values.txt"

def main():
    try:
        # Load main JSON
        with open(main_json_path, "r", encoding="utf-8") as f:
            full_data = json.load(f)
        print(f"✅ Loaded {len(full_data)} entries from JSON.")

        # Filter entries with less than 5 strings
        short_entries = {}
        short_keys = []

        for key, value in full_data.items():
            if isinstance(value, list) and len(value) < 5:
                short_entries[key] = value
                short_keys.append(key)
                print(f"🔍 {key} has only {len(value)} values.")

        # Save JSON subset
        with open(output_json_path, "w", encoding="utf-8") as f_json:
            json.dump(short_entries, f_json, ensure_ascii=False, indent=4)
        print(f"📤 Saved JSON subset to: {output_json_path}")

        # Save keys to text file
        with open(text_output_path, "w", encoding="utf-8") as f_txt:
            for key in short_keys:
                f_txt.write(f"{key}\n")
        print(f"📝 Saved key list to: {text_output_path}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

    input("\n🛑 Press Enter to exit...")

if __name__ == "__main__":
    main()

input()