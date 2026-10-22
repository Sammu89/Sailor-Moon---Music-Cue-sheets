#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gera_html_v5.py  — May 2025

Generate per‑season HTML cue‑sheets for all languages defined in the "strings-dictionary" JSON,
plus a single consolidated log per season.

Inputs:
• S01.json … S99.json           → main episode / track data
• *any* JSON whose first object contains {"id": "episodes-episodes"}
• *any* JSON whose first object contains {"id": "strings-dictionary"}

Outputs (in ./HTML/):
• SXX_<lang>.html  (one per language)
• SXX.log          (unified log for all languages)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

#######################################################################################
# Configuration
#######################################################################################

# HARDCODED CD EXCEPTIONS -------------
HARDCODED_CD: Dict[str, str] = {
    # e.g. "M-6035": "XX-XX-XX",
}


# Labels for the HTML table -------------
LABELS_BY_LANG: Dict[str, Dict[str, Any]] = {
    "ja": {
        "part": {"top": "TOPパート", "a": "Aパート", "b": "Bパート"},
        "num": "M", "name": "曲の内容", "ref": "クレジット", "time": "秒",
    },
    "en": {
        "part": {"top": "Featured Part", "a": "Part A", "b": "Part B"},
        "num": "M‑No.", "name": "Track name", "ref": "Cue Sheet", "time": "Running Time",
    },
    "pt": {
        "part": {"top": "Parte de Abertura", "a": "Parte A", "b": "Parte B"},
        "num": "Nº", "name": "Nome da faixa", "ref": "Referência", "time": "Duração",
    },
    "pt-dub": {
        "part": {"top": "Parte de Abertura", "a": "Parte A", "b": "Parte B"},
        "num": "Nº", "name": "Nome da faixa", "ref": "Referência", "time": "Duração",
    },
    "es": {
        "part": {"top": "Parte de Apertura", "a": "Parte A", "b": "Parte B"},
        "num": "Nº", "name": "Nombre de la pista", "ref": "Referencia", "time": "Duración",
    },
    "fr": {
        "part": {"top": "Partie d'Ouverture", "a": "Partie A", "b": "Partie B"},
        "num": "N°", "name": "Nom de la piste", "ref": "Référence", "time": "Durée",
    },
    "it": {
        "part": {"top": "Parte di Apertura", "a": "Parte A", "b": "Parte B"},
        "num": "N°", "name": "Nome del brano", "ref": "Riferimento", "time": "Durata",
    },
}

# CSS embedded in the generated HTML ------------------------------------------------
STYLE_BLOCK = """
    <style>
        /* Container */
        .episodio { width: 800px; border: 1px solid #333; font-family: sans-serif; margin: 32px auto; }
        /* Section titles  */
        .titulo { background: #e0e0e0; padding: 8px; font-weight: bold; border-bottom: 1px solid #333; }
        /* Header row */
        .linha-cabecalho { display: flex; background: #f5f5f5; font-weight: bold; border-bottom: 1px solid #333; }
        /* Data rows */
        .linha { display: flex; border-bottom: 1px solid #ddd; }
        /* Cells */
        .celula { padding: 6px 8px; box-sizing: border-box; }
        /* Column widths */
        .coluna-n-faixa  { width: 50px;  text-align: center; }
        .coluna-nome-faixa { flex: 1; }
        .coluna-faixa   { width: 100px; text-align: center; }
        .coluna-cd      { width: 60px;  text-align: center; }
        .coluna-tempo   { width: 70px;  text-align: center; }
    </style>
"""

# RegEx helpers for time conversion / validation ------------------------------------------
SECONDS_ONLY_RE = re.compile(r"^(?P<secs>\d+(?:\.\d+)?)s$", re.IGNORECASE)
MIN_SECS_RE     = re.compile(r"^(?P<mins>\d+)m(?P<secs>\d{2}(?:\.\d+)?)s$", re.IGNORECASE)

#######################################################################################
# JSON loading & dynamic language maps
#######################################################################################

def load_inputs(season_num: int):
    """Return a tuple with:
       - *season_data*    (dict)
       - *episodes_dict*  (dict)
       - *strings_dict*   (dict)
       - TITLE_INDEX      {lang: idx}
       - STR_INDEX        {lang: idx}
    """
    base = Path.cwd()
    season_path = base / f"S{season_num:02}.json"
    if not season_path.exists():
        raise FileNotFoundError(f"{season_path} not found")

    with season_path.open(encoding="utf-8") as f:
        season_data = json.load(f)

    episodes_dict = None
    strings_dict  = None

    for p in base.glob("*.json"):
        if p == season_path:
            continue
        try:
            with p.open(encoding="utf-8") as f:
                header = json.load(f)
        except json.JSONDecodeError:
            continue

        match header.get("id"):
            case "episodes-episodes":
                episodes_dict = header
            case "strings-dictionary":
                strings_dict = header

    if episodes_dict is None or strings_dict is None:
        raise RuntimeError("Could not locate both 'episodes-episodes' and 'strings-dictionary' JSON files")

    # Build dynamic maps
    TITLE_INDEX = {code: i for i, code in enumerate(episodes_dict["languages"])}
    STR_INDEX   = {code: i for i, code in enumerate(strings_dict["languages"])}

    return season_data, episodes_dict, strings_dict, TITLE_INDEX, STR_INDEX

#######################################################################################
# Cross‑reference resolution
#######################################################################################

def _is_ref(token: str) -> bool:
    return token.lower().startswith("string_")


def pick_text(lst: List[str], lang: str, idx_map: Dict[str, int], log: List[str] | None = None,
              default_lang: str = "en") -> str:
    if not lst:
        return ""
    if lang in idx_map:
        idx = idx_map[lang]
    elif default_lang in idx_map:
        idx = idx_map[default_lang]
        if log is not None:
            log.append(f"⚠️  Idioma '{lang}' ausente; usando '{default_lang}'.")
    else:
        idx = 0
        if log is not None:
            log.append(f"⚠️  Idioma '{lang}' ausente; usando índice 0.")
    return lst[idx] if idx < len(lst) else lst[0]


def resolve_ref(token: str, mapping: Dict[str, Any], lang: str, str_index: Dict[str, int],
                log: List[str], ep_ctx: str, row_idx: int, max_hops: int = 15) -> str:
    if not _is_ref(token):
        return token

    current = token.lower()
    visited: set[str] = set()

    for _ in range(max_hops):
        if current in visited:
            log.append(f"{ep_ctx} linha{row_idx}: referência circular em '{current}'")
            return token
        visited.add(current)

        entry = mapping.get(current) or HARDCODED_STRINGS.get(current)
        if entry is None:
            log.append(f"{ep_ctx} linha{row_idx}: referência não encontrada → '{current}'")
            return token

        if isinstance(entry, list):
            if len(entry) == 1:
                return entry[0]
            return pick_text(entry, lang, str_index, log)

        if isinstance(entry, str):
            if _is_ref(entry):
                current = entry.lower()
                continue
            return entry

        log.append(f"{ep_ctx} linha{row_idx}: tipo inesperado para '{current}': {type(entry)}")
        return token

    log.append(f"{ep_ctx} linha{row_idx}: excedido o limite de {max_hops} referências cruzadas")
    return token

#######################################################################################
# Time normalisation & validation
#######################################################################################

def seconds_to_minsec_from_digits(seconds_str: str) -> str:
    if "." in seconds_str:
        int_part, dec_part = seconds_str.split(".", 1)
        dec = f".{dec_part}"
    else:
        int_part, dec = seconds_str, ""
    mins_part = int(int_part[:-2] or "0")
    secs_part = int_part[-2:].zfill(2)
    return f"{mins_part}m{secs_part}{dec}s"


def validate_time(t: str) -> Tuple[bool, str]:
    m = MIN_SECS_RE.match(t)
    if m:
        mins = int(m.group("mins"))
        secs = float(m.group("secs"))
        if mins > 4 or secs >= 61:
            return True, "Duração excede limites"
        return False, ""

    m = SECONDS_ONLY_RE.match(t)
    if m:
        secs = float(m.group("secs"))
        if secs >= 61:
            return True, "Segundos ≥ 61"
        return False, ""

    return True, "!!!!!!!!!!Formato não reconhecido"


def normalize_time(t: str, log: List[str], ep_ctx: str, row_idx: int) -> str:
    original = t
    t = t.replace("%", "s")
    if not t.lower().endswith(("s", "m")):
        t += "s"

    sec_match = SECONDS_ONLY_RE.match(t)
    if sec_match and len(sec_match.group("secs").split(".")) >= 3:
        new_t = seconds_to_minsec_from_digits(sec_match.group("secs"))
        log.append(f"{ep_ctx} linha{row_idx}: Tempo convertido ({t} → {new_t})")
        t = new_t

    exceeds, msg = validate_time(t)
    if exceeds:
        log.append(f"{ep_ctx} linha{row_idx}: {msg} -> '{t}'")

    return t

#######################################################################################
# HTML building helpers
#######################################################################################

def build_line_html(idx: str, track: List[str], labels: Dict[str, str]) -> str:
    try:
        num, name, ref, time = track
    except ValueError:
        num, name, ref, time = ("?", "?", "?", "?")
    return (
        "        <div class=\"linha\">\n"
        f"          <div class=\"celula coluna-n-faixa\">{idx}</div>\n"
        f"          <div class=\"celula coluna-nome-faixa\">{name}</div>\n"
        f"          <div class=\"celula coluna-faixa\">{ref}</div>\n"
        "          <div class=\"celula coluna-cd\"> </div>\n"
        f"          <div class=\"celula coluna-tempo\">{time}</div>\n"
        "        </div>\n"
    )

def build_part_html(part_key: str, tracks_html: List[str], labels: Dict[str, str]) -> str:
    part_html = [f"    <div class=\"titulo\">{labels['part'][part_key]}</div>\n"]
    part_html.append(
        "    <div class=\"linha-cabecalho\">\n"
        f"      <div class=\"celula coluna-n-faixa\">{labels['num']}</div>\n"
        f"      <div class=\"celula coluna-nome-faixa\">{labels['name']}</div>\n"
        f"      <div class=\"celula coluna-faixa\">{labels['ref']}</div>\n"
        "      <div class=\"celula coluna-cd\">CD</div>\n"
        f"      <div class=\"celula coluna-tempo\">{labels['time']}</div>\n"
        "    </div>\n")
    part_html.extend(tracks_html)
    return "".join(part_html)

def build_episode_html(ep: Dict[str, Any], labels: Dict[str, str], titles_map: Dict[str, List[str]],
                       title_index: Dict[str, int], mapping: Dict[str, Any], lang: str,
                       str_index: Dict[str, int], log: List[str]) -> str:
    ep_number = ep.get("number", "?")
    ep_ctx = f"Ep{ep_number}"
    title_list = titles_map.get(str(ep_number), [])
    title = pick_text(title_list, lang, title_index, log)

    html_parts: List[str] = [
        "  <div class=\"episodio\">\n",
        f"    <div class=\"titulo\">Ep. {ep_number} – {title}</div>\n",
    ]

    for part_key, json_key in (("top", "Top"), ("a", "A"), ("b", "B")):
        tracks_raw = ep.get("parts", {}).get(json_key)
        if not tracks_raw:
            continue

        track_blocks: List[str] = []
        for row_idx, track in enumerate(tracks_raw, start=1):
            if len(track) != 4:
                log.append(f"{ep_ctx} linha{row_idx}: Elementos insuficientes (tamanho={len(track)}) → ignorado")
                continue
            num, name, ref, time = track
            time = normalize_time(time, log, ep_ctx, row_idx)
            name = resolve_ref(name, mapping, lang, str_index, log, ep_ctx, row_idx)
            ref  = resolve_ref(ref,  mapping, lang, str_index, log, ep_ctx, row_idx)
            track_blocks.append(build_line_html(num, [num, name, ref, time], labels))

        if track_blocks:
            html_parts.append(build_part_html(part_key, track_blocks, labels))

    html_parts.append("  </div>\n")
    return "".join(html_parts)

def build_html(season_data: Dict[str, Any], labels: Dict[str, str], titles_map: Dict[str, List[str]],
               title_index: Dict[str, int], mapping: Dict[str, Any], lang: str,
               str_index: Dict[str, int], log: List[str]) -> str:
    body_parts = [
        build_episode_html(ep, labels, titles_map, title_index, mapping, lang, str_index, log)
        for ep in season_data.get("episodes", [])
    ]
    return (
        f"<!DOCTYPE html>\n<html lang=\"{lang}\">\n<head>\n  <meta charset=\"UTF-8\">\n  <title>{lang}</title>\n"
        + STYLE_BLOCK + "\n</head>\n<body>\n\n" + "\n".join(body_parts) + "\n</body>\n</html>\n"
    )

#######################################################################################
# CD post-processing implementation
#######################################################################################

def build_cues_map(root_dir: Path) -> Dict[str, str]:
    """
    Scan every JSON in root_dir whose top-level "id" contains "cue" (case-insensitive),
    and return a dict mapping entry[0] → entry[-1] for every list-of-lists of length ≥4.
    """
    cues_map: Dict[str, str] = {}
    # 1) Iterate all .json files at the project root
    for p in root_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        # 2) Only care about files where id contains "cue"
        id_val = data.get("id", "")
        if not (isinstance(id_val, str) and "cue" in id_val.lower()):
            continue

        # 3) Walk every value in the JSON and look for list-of-lists
        for v in data.values():
            if isinstance(v, list):
                for entry in v:
                    if isinstance(entry, list) and len(entry) >= 4:
                        # map the first element to the last element
                        key = entry[0]
                        val = entry[-1]
                        cues_map[key] = val

    return cues_map


def complete_cd_column(html_path: Path, log: List[str]) -> None:
    # assume your HTML/ folder is one level below the JSON root
    root_dir = html_path.parent.parent

    # build the full map in memory
    cues_map = build_cues_map(root_dir)
    if not cues_map:
        log.append("Aviso: nenhum arquivo 'Cues' encontrado ou extraído.")

    # read & split your generated HTML
    lines = html_path.read_text(encoding="utf-8").splitlines()
    missing: List[str] = []

    # for each <div class="celula coluna-faixa">REF</div>, look up REF → cd_code
    import re
    for i, line in enumerate(lines):
        if 'class="celula coluna-faixa"' in line:
            m = re.search(r'>([^<]+)<', line)
            if not m:
                continue
            ref = m.group(1).strip()
            cd_val = HARDCODED_CD.get(ref) or cues_map.get(ref)
            if cd_val:
                # inject into the very next coluna-cd cell
                j = i + 1
                if j < len(lines) and 'class="celula coluna-cd"' in lines[j]:
                    lines[j] = re.sub(
                        r'(<div class="celula coluna-cd">).*?(</div>)',
                        rf'\1{cd_val}\2',
                        lines[j]
                    )
            else:
                missing.append(ref)

    # log any truly missing
    for ref in sorted(set(missing)):
        log.append(f"CD não encontrado para '{ref}'")

    # write it back
    html_path.write_text("\n".join(lines), encoding="utf-8")


#######################################################################################
# Logging helpers
#######################################################################################

def write_log(log: List[str], path: Path):
    if not log:
        log.append("Sem avisos.")
    path.write_text("\n".join(log), encoding="utf-8")
    print("\n---- LOG ----")
    for line in log:
        print(line)
    print("------------\n")


#######################################################################################
# CLI / main
#######################################################################################

def main(argv: List[str] | None = None):
    parser = argparse.ArgumentParser(description="Gera ficheiros HTML + log para uma temporada.")
    parser.add_argument("season", nargs="?", type=int, help="Número da temporada (ex.: 3 → S03.json)")
    args = parser.parse_args(argv)

    # Season number – interactive fallback
    if args.season is None:
        # Preserve original interactive prompt for season
        while True:
            num = input("Escolha o ficheiro principal (1‑99): S").strip()
            if num.isdigit() and 1 <= int(num) <= 99:
                season_num = int(num)
                break
            print("Valor inválido. Tente novamente.")
    else:
        season_num = args.season

    # Load inputs
    try:
        season_data, episodes_dict, strings_dict, TITLE_INDEX, STR_INDEX = load_inputs(season_num)
    except Exception as e:
        print("Erro ao carregar JSON:", e)
        sys.exit(1)

    # Languages to process: only those from strings-dictionary
    langs = strings_dict.get("languages", [])
    if not langs:
        print("Nenhuma língua encontrada em 'strings-dictionary'.")
        sys.exit(1)

    out_dir = Path.cwd() / "HTML"
    out_dir.mkdir(exist_ok=True)

    global_log: List[str] = []

    # Generate for each language
    for lang in langs:
        labels = LABELS_BY_LANG.get(lang, LABELS_BY_LANG.get("en"))
        log: List[str] = []

        html_content = build_html(
            season_data,
            labels,
            episodes_dict.get("episodes", episodes_dict),
            TITLE_INDEX,
            strings_dict.get("strings", strings_dict),
            lang,
            STR_INDEX,
            log
        )

        out_html = out_dir / f"S{season_num:02}_{lang}.html"
        out_html.write_text(html_content, encoding="utf-8")
        # ← here: fill in the CD column based on Cues JSONs
        complete_cd_column(out_html, log)


        # Append to unified log
        if log:
            global_log.extend([f"[{lang}] {line}" for line in log])
        else:
            global_log.append(f"[{lang}] Sem avisos.")
        global_log.append("")

    # Write unified log
    out_log = out_dir / f"S{season_num:02}.log"
    write_log(global_log, out_log)

    print(f"HTMLs gerados em → {out_dir.relative_to(Path.cwd())}")
    print(f"Log unificado em → {out_log.relative_to(Path.cwd())}")

if __name__ == "__main__":
    try:
        main()
    finally:
        if sys.stdin.isatty():
            input("\nConcluído. Pressione <ENTER> para sair…")
