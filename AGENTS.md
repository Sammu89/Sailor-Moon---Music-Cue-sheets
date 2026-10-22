# MusicSheets — Cue sheets de Sailor Moon (anime de 1992–97)

Este ficheiro tem duas partes: a **Parte 1** explica o projeto a uma pessoa; a **Parte 2** é o manual técnico para um agente de IA.
Cópia no Git: `Documents\Código\sm-cue-sheets` (repo `Sammu89/sm-cue-sheets`). **A pasta Nextcloud é a fonte de verdade.**

---

## Parte 1 — Para humanos

### O que é isto?

Cada episódio de Sailor Moon tem uma "cue sheet" (folha de música): a lista de todas as faixas musicais que tocam no episódio, por ordem, com a duração de cada uma e o disco (CD) de onde vêm. Estas folhas existem apenas em japonês, em livros/PDFs digitalizados (ver `Data\Indexes.pdf` e as imagens em `Data\Images S0X`).

Este projeto **transforma essas folhas digitalizadas em dados limpos e traduzidos** e gera **tabelas HTML** prontas a publicar, em 6 idiomas (japonês, inglês, português, espanhol, francês, italiano).

### Como funciona, em linguagem simples

1. **Digitalizar e ler** — as imagens das folhas passam por OCR e o texto sai com erros (por exemplo `1′02″半` para "1 min 02,5 s").
2. **Arrumar** — scripts Python leem o texto e organizam-no por episódio e por parte (A e B), corrigindo tempos e códigos mal lidos.
3. **Dicionário de textos** — cada nome de faixa (ex.: "静かな緊張感") é guardado **uma só vez** num dicionário com um identificador (`string_1`). As folhas só guardam o identificador. Assim cada título é traduzido uma única vez, mesmo que apareça em 50 episódios.
4. **Traduzir** — os títulos japoneses são traduzidos (DeepL / modelos Hugging Face) e revistos.
5. **Gerar HTML** — o script final junta folhas + dicionário e produz uma tabela por temporada e por idioma.

### O que é o resultado?

- `JSON Final\S01.json … S05.json` — as cue sheets das 5 temporadas (Sailor Moon, R, S, SuperS, Stars).
- `JSON Final\Key_Strings.json` — dicionário de textos em 6 idiomas.
- `JSON Final\Key_Episódios.json` — títulos dos episódios em 8 variantes (ja, romaji, pt, pt-dub, en, es, fr, it).
- `JSON Final\Cues_Index_*.json` — o "índice" de cada temporada/filmes: lista de faixas por CD (código M-NO., tempo, nome, CD).
- `JSON Final\HTML\S0X_<idioma>.html` — as tabelas finais. **Atualmente só existe a S01 gerada (6 idiomas)**; as temporadas 2–5 ainda não foram geradas.

---

## Parte 2 — Para agentes

### Modelo de dados

**Ficheiro de temporada `S0X.json`**
```json
{
  "global_headers": {"A": "string_3474", "B": "string_3469"},
  "global_subheaders": ["M", "string_3471", "string_3472", "string_3473"],
  "episodes": [
    {"number": 1, "parts": {"A": [["1", "string_16", "C-1B", "10s"], ...], "B": [...]}}
  ]
}
```
Cada faixa é `[nº M, ref_nome, ref_CD/crédito, duração]`. Durações: `1m20s`, `29s`, `1m24.5s`.
Qualquer texto que seja `string_N` (ou `Is_N` nos índices, `s_`/`im_` em ficheiros intermédios) é uma **referência** ao dicionário. `string_N` pode apontar para outra `string_M` (resolvido por `resolve_ref`; referências circulares como `string_1160 → string_1160` são erros a registar).

**Dicionário `Key_Strings.json`**: `{"id":"strings-dictionary","languages":["ja","en","pt","es","fr","it"],"string_1":[ja,en,pt,es,fr,it], ...}`. A posição no array = índice em `languages`.

**Episódios `Key_Episódios.json`**: `{"id":"episodes-episodes","languages":[...8...],"1":[...]}`.

**Índices `Cues_Index_*.json`**: `{"id": "...", "string_S01": {"Headers": [...], "Sections": {"string_X": [[M-NO, tempo, ref_nome, CD], ...]}}}`.

`Gerar HTML final.py` identifica os ficheiros pelo campo `id` (`episodes-episodes`, `strings-dictionary`), não pelo nome — manter esses `id`.

### Pipeline (ordem de execução, tudo interativo, `input()`)

| # | Script | Entrada → Saída |
|---|---|---|
| 0 | `Data\Instruções GPT\Instrucoes_*.txt` | Prompts usados para gerar/ajustar o parser com um LLM (histórico, não executar) |
| 1 | `1- ParsingEpisodes.py` | texto OCR `.txt` → `S0X_raw.json` (+ `_logs.txt`). Deteta episódios pelo padrão `第N`, separa partes A/B, corrige tempos |
| 2 | `2- ProcessJSON_of_episodes.py` | `S0X_raw.json` → `S0X.json` + `S0X_keys.json` (substitui textos por `string_N`, remove campos `—`). Pede prefixo e nº inicial |
| 3 | `3- ProcessJSON_of_strings.py` | deduplica o dicionário de textos |
| 4 | `ParsingIndexes.py` / `ParsingMovies.py` | OCR dos índices de CD → `Index_*.json` (cabeçalhos `M-NO., TIME, 内容, 収録CD`) |
| 5 | `ProcessJSON_indexSeasons.py` / `ProcessJSON_indexMovies.py` | índices → `*_processed.json` + `*_keys.json` (chaves `Is_N`) |
| 6 | `JSON Final\Pythons\Tradutor*.py`, `TraduitorDeepL.py` | `Keys_String_*.json` → traduções (DeepL EN→PT-PT; Hugging Face pt→ca→es) |
| 7 | `JSON Final\Reagrupar key strings.py` | funde chaves duplicadas segundo `Key_Episódios_novas.txt` (`string_N: [k1, k2]`), cria `.bak` |
| 8 | `JSON Final\Pythons\*.py` (utilitários) | `Process Libs`, `Resolve References…`, `Replace entries…`, `EXTRACT FROM MAIN ENTRIES…`, `Add cues to final HTML`, `fazer lista de indexes dos Index_` — correções pontuais |
| 9 | `JSON Final\Gerar HTML final.py` | `S0X.json` + dicionários → `HTML\S0X_<lang>.html` + `S0X.log` (CLI com `argparse`) |

Os scripts procuram ficheiros em `os.getcwd()` ou `.\Data` — **corre-os a partir da pasta onde estão os dados**.

### Estrutura de pastas

```
MusicSheets/
  AGENTS.md, CLAUDE.md          este manual
  1-…3-*.py, Parsing*.py, ProcessJSON_index*.py   pipeline (passos 1–5)
  S04_raw/keys.json, S05_raw/keys.json            intermédios das temporadas 4 e 5
  Backup Scripts/               versões antigas dos scripts (não editar)
  Data/                         entradas: imagens das folhas, raw/ (Index_*, S02_raw), Keys_String_JP, GIFs/PNG de apoio, Instruções GPT/
  JSON Final/                   saídas finais, dicionários, HTML/, Pythons/ (utilitários e tradutores)
```

### Regras para agentes

- **JSON em UTF-8 com `ensure_ascii=False`**; texto japonês e acentos portugueses têm de sobreviver. Nomes de ficheiro com acentos (`Key_Episódios.json`) são intencionais.
- **Nunca editar os JSON finais à mão em massa**; corrigir o script e regenerar, ou usar os utilitários de `Pythons\`. Fazer cópia antes (os scripts já criam `.bak`/backups).
- **Não inventar traduções de nomes próprios** (personagens, ataques, vilões): usar a forma já presente no dicionário.
- Tradução PT = **português europeu** (pt-PT). `pt-dub` nos episódios = título da dobragem portuguesa (RTP), não uma tradução literal.
- Ao mexer em referências: validar que todo `string_N` existe e que não há ciclos. Registar anomalias em log, não as silenciar.
- Estado conhecido: `S05_keys.json` quase vazio (6 bytes), `Cues_Index_S02.json.json` tem extensão duplicada (nome histórico, ainda usado), HTML só da S01.
- **Segredos:** o repositório é privado e a chave DeepL em `TraduitorDeepL.py` está obsoleta, por isso fica no código. Não adicionar chaves novas e válidas a scripts. Caminhos absolutos antigos (`G:\O meu disco\…`, `C:\Users\Sammu\O meu disco\…`, `/mnt/chromeos/…`) são de máquinas anteriores — adaptar.

### Sincronização com o Git

A fonte de verdade é esta pasta (Nextcloud). A cópia em `Documents\Código\sm-cue-sheets` é derivada: atualizar a partir daqui, nunca o contrário. Não se versionam binários pesados nem o `.7z` de backup; ver `.gitignore` do repo.
