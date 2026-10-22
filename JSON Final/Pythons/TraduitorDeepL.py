import json
import subprocess
import sys
import time
import importlib.util
from pathlib import Path

# Auto-installer
def install_and_import(pkg_name, import_name=None):
    import_name = import_name or pkg_name
    try:
        if importlib.util.find_spec(import_name) is None:
            raise ImportError
        return True
    except ImportError:
        try:
            print(f"📦 Installing {pkg_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
            if importlib.util.find_spec(import_name) is None:
                raise ImportError(f"Module '{import_name}' still not found after install.")
            return True
        except Exception as e:
            print(f"❌ Failed to install {pkg_name}: {e}")
            input("⚠️ Press Enter to exit.")
            return False

# Ensure required packages
requirements_met = all([
    install_and_import("deepl"),
    install_and_import("tqdm")
])

if not requirements_met:
    sys.exit(1)

# Imports
import deepl
from tqdm import tqdm

# DeepL API key (Replace this with your own key)
DEEPL_AUTH_KEY = "7d1B3e81-3ea3-4d41-88b6-12ab1c9b5c88:fx"

try:
    translator = deepl.Translator(DEEPL_AUTH_KEY)
except Exception as e:
    print(f"❌ Failed to initialize DeepL Translator: {e}")
    input("⚠️ Press Enter to exit.")
    sys.exit(1)

# Target languages (DeepL language codes)
languages = {
    "pt": "PT-PT",
}

# Load source JSON
try:
    with open(r"C:\Users\Sammu\O meu disco\SM\MusicSheets\JSON Final\Keys_String_EN.json", "r", encoding="utf-8") as f:
        jp_data = json.load(f)
except Exception as e:
    print(f"❌ Error loading JSON file: {e}")
    input("⚠️ Press Enter to exit.")
    jp_data = {}

# Setup containers
translated = {lang: {} for lang in languages}
translation_cache = {}
translation_errors = {lang: False for lang in languages}
skipped_languages = []

# Symbolic reference keys
reference_prefixes = ("s_", "im_", "Is_")

# Translate with progress bar
for key, val in tqdm(jp_data.items(), desc="🔤 Translating", unit="item"):
    try:
        if isinstance(val, str) and val.startswith(reference_prefixes):
            for lang_code in translated:
                translated[lang_code][key] = val
            continue

        if val not in translation_cache:
            translation_cache[val] = {}
            for lang_code, deepl_code in languages.items():
                try:
                    result = translator.translate_text(val, source_lang="EN", target_lang=deepl_code).text
                    translation_cache[val][lang_code] = result
                    print(f"⏱️ [{lang_code}] \"{val}\" ➤ \"{result}\"")
                except Exception as e:
                    print(f"⚠️ Error translating '{val}' to '{lang_code}': {e}")
                    translation_cache[val][lang_code] = val
                    translation_errors[lang_code] = True

        for lang_code in translated:
            translated[lang_code][key] = translation_cache[val][lang_code]

    except Exception as e:
        print(f"⚠️ Error processing key '{key}': {e}")
        for lang_code in translated:
            translated[lang_code][key] = val
            translation_errors[lang_code] = True

# Save results
saved = []
skipped = []

for lang_code, content in translated.items():
    if translation_errors[lang_code]:
        print(f"⏭️ Skipping export for '{lang_code.upper()}' due to translation issues.")
        skipped.append(lang_code)
        continue
    try:
        output_path = Path(f"Keys_String_{lang_code.upper()}.json")
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved: {output_path.name}")
        saved.append(lang_code)
    except Exception as e:
        print(f"❌ Error saving file for '{lang_code}': {e}")
        skipped.append(lang_code)

# Final summary
print("\n🔚 Translation process complete.")
print(f"✅ Successfully exported: {', '.join(saved) if saved else 'None'}")
print(f"⚠️ Skipped due to issues: {', '.join(skipped) if skipped else 'None'}")

input("\n👋 Press Enter to exit.")
