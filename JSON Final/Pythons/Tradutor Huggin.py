
import json
import subprocess
import sys
import time
import importlib.util
from pathlib import Path

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
            if importlib.util.find_spec(import_import_name) is None:
                raise ImportError(f"Module '{import_name}' still not found after install.")
            return True
        except Exception as e:
            print(f"❌ Failed to install {pkg_name}: {e}")
            input("⚠️ Press Enter to exit.")
            return False

requirements_met = all([
    install_and_import("transformers"),
    install_and_import("torch"),
    install_and_import("sentencepiece"),
    install_and_import("sacremoses"),
    install_and_import("tqdm")
])

if not requirements_met:
    sys.exit(1)

import torch
from tqdm import tqdm
from transformers import MarianMTModel, MarianTokenizer

def safe_generate(model, tokenizer, text):
    try:
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
            model = model.to("cuda")
        outputs = model.generate(**inputs)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        print(f"⚠️ Translation failed: {e}")
        return text

# Define models for pt -> ca -> es
models_config = {
    "pt-ca": "Helsinki-NLP/opus-mt-pt-ca",
    "ca-es": "Helsinki-NLP/opus-mt-ca-es"
}

tokenizers = {}
models = {}

for key, model_name in models_config.items():
    try:
        print(f"🔄 Loading model for {key}...")
        tokenizers[key] = MarianTokenizer.from_pretrained(model_name)
        models[key] = MarianMTModel.from_pretrained(model_name)
    except Exception as e:
        print(f"❌ Failed to load model '{key}': {e}")
        input("Press Enter to exit.")
        sys.exit(1)

# Load PT JSON
source_file = r"C:\Users\Sammu\O meu disco\SM\MusicSheets\JSON Final\Keys_String_PT.json"
try:
    with open(source_file, "r", encoding="utf-8") as f:
        pt_data = json.load(f)
    print(f"📂 Loaded source file with {len(pt_data)} entries.")
except Exception as e:
    print(f"❌ Failed to load JSON: {e}")
    input("Press Enter to exit.")
    sys.exit(1)

translated_ca = {}
translated_es = {}
reference_prefixes = ("s_", "im_", "Is_")

# Stage 1: pt → ca
print("\n🔁 Translating PT → CA...")
for key, val in tqdm(pt_data.items(), desc="PT → CA"):
    if isinstance(val, str) and val.startswith(reference_prefixes):
        translated_ca[key] = val
    else:
        translated_ca[key] = safe_generate(models["pt-ca"], tokenizers["pt-ca"], val)

# Stage 2: ca → es
print("\n🔁 Translating CA → ES...")
for key, val in tqdm(translated_ca.items(), desc="CA → ES"):
    translated_es[key] = safe_generate(models["ca-es"], tokenizers["ca-es"], val)

# Save files
outputs = {"CA": translated_ca, "ES": translated_es}
for lang, data in outputs.items():
    try:
        path = Path(f"Keys_String_{lang}.json")
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved: {path.name}")
    except Exception as e:
        print(f"❌ Failed to save {lang} file: {e}")

input("\n✅ Done! Press Enter to exit.")
