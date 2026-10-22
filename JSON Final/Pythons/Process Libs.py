import os
import json
import re

# Expressão regular válida: Letra-Número ou Letra-NúmeroLetra (ex: A-2, I-3b)
valid_pattern = re.compile(r"^[A-Z]-\d+[a-zA-Z]?$")

try:
    # Lista todos os ficheiros .json no diretório atual
    json_files = [f for f in os.listdir() if f.endswith(".json")]

    if not json_files:
        print("❌ Nenhum ficheiro JSON encontrado nesta pasta.")
        exit()

    # Mostra lista de ficheiros para o utilizador escolher
    print("Escolhe o ficheiro JSON a processar:")
    for i, filename in enumerate(json_files, 1):
        print(f"{i}. {filename}")

    while True:
        try:
            choice = int(input("Número do ficheiro: ")) - 1
            if 0 <= choice < len(json_files):
                break
            else:
                print("❗ Número inválido.")
        except ValueError:
            print("❗ Introduz um número válido.")

    selected_file = json_files[choice]

    # Prompt para valores iniciais de referência
    try:
        crossref_counter = int(input("Valor inicial para crossrefs (default: 1): ") or "1")
        library_counter = int(input("Valor inicial para library refs (default: 1): ") or "1")
    except ValueError:
        print("⚠️ Valores inválidos. Usando 1 por defeito.")
        crossref_counter = 1
        library_counter = 1

    # Carrega o ficheiro JSON
    try:
        with open(selected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler o ficheiro JSON: {e}")
        exit()

    # Preparar dicionários para exportação
    crossrefs = {}
    libraryrefs = {}

    # Processa todas as partes dos episódios
    for episode in data.get("episodes", []):
        for part_key, part in episode.get("parts", {}).items():
            for cue in part:
                value = cue[2]
                if valid_pattern.match(value):
                    continue
                elif "+" in value:
                    default_key = f"crossref_{crossref_counter}"
                    key = input(f"Referência cruzada encontrada '{value}'. Chave (default: {default_key}): ") or default_key
                    crossrefs[key] = value
                    cue[2] = key
                    crossref_counter += 1
                else:
                    default_key = f"lib_{library_counter}"
                    key = input(f"Referência externa encontrada '{value}'. Chave (default: {default_key}): ") or default_key
                    libraryrefs[key] = value
                    cue[2] = key
                    library_counter += 1

    # Guarda o ficheiro principal atualizado
    try:
        with open(selected_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Ficheiro principal atualizado: {selected_file}")
    except Exception as e:
        print(f"❌ Erro ao guardar o ficheiro principal: {e}")

    # Guarda as referências cruzadas
    if crossrefs:
        try:
            crossref_file = selected_file.replace(".json", "_crossreferences.json")
            with open(crossref_file, "w", encoding="utf-8") as f:
                json.dump(crossrefs, f, indent=4, ensure_ascii=False)
            print(f"🔗 Referências cruzadas guardadas em: {crossref_file}")
        except Exception as e:
            print(f"❌ Erro ao guardar referências cruzadas: {e}")

    # Guarda as referências externas
    if libraryrefs:
        try:
            lib_file = selected_file.replace(".json", "_library.json")
            with open(lib_file, "w", encoding="utf-8") as f:
                json.dump(libraryrefs, f, indent=4, ensure_ascii=False)
            print(f"📚 Referências externas guardadas em: {lib_file}")
        except Exception as e:
            print(f"❌ Erro ao guardar referências externas: {e}")

except Exception as e:
    print(f"🚨 Ocorreu um erro inesperado: {e}")
