import os
import json
import re

def resolve_reference(lib_refs, key, visited=None):
    """
    Recursively resolves a reference to the final symbolic key before hitting an actual value.
    Avoids infinite loops by tracking visited keys.
    """
    if visited is None:
        visited = set()

    original_key = key
    while key in lib_refs and isinstance(lib_refs[key], str):
        if key in visited:
            print(f"⚠️ Loop detected: {key} already visited while resolving {original_key}")
            break
        visited.add(key)
        key = lib_refs[key]

    if key not in lib_refs or not isinstance(lib_refs[key], list):
        print(f"❌ Final resolved key '{key}' is not a list-type value. Skipping.")
        return original_key  # Fall back to original if something goes wrong

    return key

def list_json_files():
    """Lists all .json files in the current directory."""
    return [f for f in os.listdir() if f.endswith(".json")]

def choose_file(json_files, prompt):
    """Prompts user to select a file by number from the list."""
    print(prompt)
    for idx, filename in enumerate(json_files):
        print(f"{idx + 1}. {filename}")
    
    while True:
        try:
            choice = int(input("Escolha o número do ficheiro: "))
            if 1 <= choice <= len(json_files):
                return json_files[choice - 1]
            else:
                print("❌ Escolha inválida. Tente novamente.")
        except ValueError:
            print("❌ Entrada inválida. Insira um número.")

def is_reference_key(key):
    """Returns True if the key appears to be a symbolic reference (s_, is_, im_)"""
    return isinstance(key, str) and re.match(r'^(s_|is_|im_)\d+$', key)

def process_reference_resolution():
    json_files = list_json_files()
    if not json_files:
        print("❌ Nenhum ficheiro JSON encontrado nesta pasta.")
        return

    ref_file = choose_file(json_files, "Escolha o ficheiro de REFERÊNCIAS (ex: library.json):")
    main_file = choose_file(json_files, "Escolha o ficheiro PRINCIPAL (ex: main.json):")

    try:
        with open(ref_file, "r", encoding="utf-8") as f:
            lib_refs = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler ficheiro de referências '{ref_file}': {e}")
        return

    try:
        with open(main_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler ficheiro principal '{main_file}': {e}")
        return

    updated = False
    for episode in data.get("episodes", [data]):  # allow fallback if data is not wrapped in episodes
        for part_key, part in episode.get("parts", {}).items():
            for cue in part:
                if len(cue) > 1:
                    cue_key = cue[1]
                    if is_reference_key(cue_key) and cue_key in lib_refs:
                        try:
                            resolved_key = resolve_reference(lib_refs, cue_key)
                            if resolved_key != cue_key:
                                print(f"🔁 Resolving {cue_key} → {resolved_key}")
                                cue[1] = resolved_key
                                updated = True
                        except Exception as e:
                            print(f"⚠️ Erro ao resolver '{cue_key}': {e}")

    if updated:
        output_file = main_file.replace(".json", "_resolved.json")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"✅ Ficheiro atualizado guardado como: {output_file}")
        except Exception as e:
            print(f"❌ Erro ao guardar ficheiro de saída '{output_file}': {e}")
    else:
        print("ℹ️ Nenhuma referência precisou ser resolvida.")

if __name__ == "__main__":
    process_reference_resolution()
