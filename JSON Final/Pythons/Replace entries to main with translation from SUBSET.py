import json
from pathlib import Path

# Paths
base_dir = Path(__file__).resolve().parent
main_json_path = base_dir / "Keys_String_Combined.json"
subset_json_path = base_dir / "Keys_String_Extracted_English.json"
output_path = base_dir / "Keys_String_Combined_cleaned_replaced.json"

def main():
    try:
        # Load main cleaned JSON
        with open(main_json_path, "r", encoding="utf-8") as f:
            main_data = json.load(f)
        print(f"📥 Main JSON loaded: {len(main_data)} entries")

        # Load subset JSON
        with open(subset_json_path, "r", encoding="utf-8") as f:
            subset_data = json.load(f)
        print(f"🔁 Subset JSON loaded: {len(subset_data)} entries to replace")

        # Replace entries
        replaced_count = 0
        for key, value in subset_data.items():
            if key in main_data:
                main_data[key] = value
                replaced_count += 1
            else:
                print(f"⚠️ Key '{key}' not found in main JSON — skipped")

        # Save updated JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(main_data, f, ensure_ascii=False, indent=4)
        print(f"✅ Replaced {replaced_count} entries")
        print(f"📤 Updated JSON saved to: {output_path}")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
input()