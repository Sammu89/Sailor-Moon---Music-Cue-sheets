# sm-cue-sheets

Cue sheets (folhas de música) dos episódios de **Sailor Moon** (anime de 1992–97): lista de todas as faixas musicais de cada episódio, com duração e CD de origem. As folhas originais só existem em japonês e em digitalizações; este projeto transforma-as em **JSON limpo**, traduz os títulos para **6 idiomas** (ja, en, pt, es, fr, it) e gera **tabelas HTML** prontas a publicar.

> Manual completo, para humanos e para agentes de IA: [`AGENTS.md`](AGENTS.md).

## Como funciona

1. **OCR** das folhas digitalizadas → texto com erros (ex.: `1′02″半`).
2. **Parsing**: scripts Python organizam o texto por episódio e parte (A/B) e corrigem tempos e códigos.
3. **Dicionário de textos**: cada título é guardado uma só vez (`string_N`); as folhas só guardam a referência.
4. **Tradução** dos títulos (DeepL / Hugging Face) e revisão.
5. **Geração de HTML** por temporada e por idioma.

## Pipeline (scripts por ordem)

Os scripts são interativos e procuram ficheiros na pasta atual ou em `Data/`.

| Passo | Script | Função |
|---|---|---|
| 1 | `1- ParsingEpisodes.py` | texto OCR → `S0X_raw.json` |
| 2 | `2- ProcessJSON_of_episodes.py` | `S0X_raw.json` → `S0X.json` + chaves `string_N` |
| 3 | `3- ProcessJSON_of_strings.py` | deduplicação do dicionário de textos |
| 4 | `ParsingIndexes.py`, `ParsingMovies.py` | índices de CD (temporadas / filmes) → JSON |
| 5 | `ProcessJSON_indexSeasons.py`, `ProcessJSON_indexMovies.py` | índices → chaves `Is_N` |
| 6 | `JSON Final/Pythons/Tradutor*.py`, `TraduitorDeepL.py` | tradução |
| 7 | `JSON Final/Reagrupar key strings.py` | fusão de chaves duplicadas |
| 8 | `JSON Final/Pythons/*.py` | utilitários de correção |
| 9 | `JSON Final/Gerar HTML final.py` | JSON + dicionários → HTML |

Dependências: Python 3; `deepl`, `tqdm` (instalados automaticamente) e `transformers` para a tradução.

## Dados e resultados

- `JSON Final/S01.json … S05.json` — cue sheets das 5 temporadas.
- `JSON Final/Key_Strings.json` — dicionário de textos em 6 idiomas.
- `JSON Final/Key_Episódios.json` — títulos dos episódios em 8 variantes.
- `JSON Final/Cues_Index_*.json` — índices por CD de cada temporada e dos filmes/especiais.
- `JSON Final/HTML/S0X_<idioma>.html` — tabelas finais (por agora só a S01).

### Gerar o HTML

```bash
cd "JSON Final"
python "Gerar HTML final.py"
```

Produz `HTML/S0X_<idioma>.html` e um log `S0X.log` por temporada.

## Sincronização

A fonte de verdade é a pasta Nextcloud `Projetos/SMPT/MusicSheets`; este repositório é uma cópia derivada, sem binários pesados (PDF, imagens, `.7z`, ver `.gitignore`).
