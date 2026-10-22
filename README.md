# sm-cue-sheets

Cue sheets (folhas de música) dos episódios de **Sailor Moon** (anime de 1992–97): para cada episódio, a lista de faixas musicais que tocam, na ordem, com a duração de cada uma e o CD de onde vêm. As folhas originais só existem em japonês, em digitalizações.

Este projeto transforma essas digitalizações em **JSON limpo**, traduz os títulos para **6 idiomas** (ja, en, pt, es, fr, it) e gera **tabelas HTML** para publicar.

> Este README é o "caderno de engenharia": serve para eu (daqui a anos) perceber o que fiz, por que ordem, e onde ficaram as arestas por limar. O manual curto para agentes de IA está em [`AGENTS.md`](AGENTS.md).
>
> **Marcação:** o que está escrito sem ressalvas foi confirmado a ler o código ou a correr os scripts. O que está marcado com **(inferido)** é a minha reconstrução a partir dos nomes dos ficheiros e dos dados — não há script no repo que o prove.

---

## 1. Conceitos que é preciso ter na cabeça

### A estrutura de um episódio
Cada episódio tem até **três partes**: `Top` (abertura, nem sempre existe), `A` e `B`. Cada faixa é uma linha com 4 campos:

| Campo | Exemplo | Significado |
|---|---|---|
| 0 | `1`, `5a` | número da faixa no episódio (a/b/c quando é subdividida) |
| 1 | `string_16` | **nome da faixa** (referência ao dicionário) |
| 2 | `C-1B`, `M-609` | **código da cue**: `Letra-Número` → ver CD |
| 3 | `1m20s`, `29s`, `1m24.5s` | duração |

### O truque central: o dicionário de textos
O mesmo título de faixa (ex.: "静かな緊張感") aparece em dezenas de episódios. Por isso **nenhum texto fica nas folhas**: cada texto único recebe um identificador (`string_N`) e vive numa só entrada de `Key_Strings.json`, com uma tradução por idioma. As folhas só guardam `string_N`. Traduzir uma vez = traduzir em todo o lado.

### Os prefixos de chaves (importante!)
Ao longo do pipeline os textos mudam de "nome" várias vezes. Isto é o que mais confunde quando se volta ao projeto:

| Prefixo | Quem o cria | Significa |
|---|---|---|
| `s_N` | `2- ProcessJSON_of_episodes.py` (prefixo configurável, default `s`) | texto japonês de um **episódio**, ainda provisório |
| `Is_N` | `ProcessJSON_indexSeasons.py` | texto japonês de um **índice de temporada** (I = index, s = season) |
| `Im_N` | `ProcessJSON_indexMovies.py` | texto japonês de um **índice de filmes** |
| `string_N` | `Reagrupar key strings.py` e `fazer lista de indexes…` | **chave final**, a que está em `Key_Strings.json` |
| `crossref_N` | `Process Libs.py` | cue composta, ex. `M-601+M-602` |
| `lib_N` | `Process Libs.py` | cue "externa" que não segue o padrão `A-1` (música de biblioteca) |

Uma chave pode apontar para outra chave (depois da deduplicação, `s_40: "s_5"` quer dizer "igual a `s_5`"). Quem lê tem de seguir a cadeia — é o que faz `resolve_ref` no gerador de HTML (máx. 15 saltos; ciclos são registados no log).

### Formato dos tempos
O OCR dá coisas como `1′02″半`. O parser limpa-os em passos: `′`→`'`, `″`→`"`, `半`→`.5`, `'`→`m`. O formato final é `1m02.5s`, `29s`. O `半` ("meio") é meio segundo.

---

## 2. Visão geral do fluxo

```
 Digitalizações (Data/ImagesS0X, Indexes.pdf)
        │  OCR (feito fora do projeto → ficheiros .txt)
        ▼
 Data/raw/Episodios_S0X.txt ──► [1] ParsingEpisodes ──► S0X_raw.json (+ _logs.txt)
                                       │  corrigir à mão o que o log apontar
                                       ▼
                              [2] ProcessJSON_of_episodes ──► S0X_processed.json + S0X_keys.json
                                       │                         (textos → s_N)
                                       ▼
                              [3] ProcessJSON_of_strings ──► processed_Keys_String_JP.json (dedup)
                                       │
 Data/raw/Index_*.txt ──► [4] ParsingIndexes / ParsingMovies ──► Index_*.json
                                       ▼
                              [5] ProcessJSON_indexSeasons / indexMovies ──► *_processed.json + *_keys.json
                                       ▼
                    Keys_String_JP ──► traduzir (EN → PT → ES/FR/IT) ──► Keys_String_Combined (inferido)
                                       ▼
                              [6] arrumar lacunas (Pythons/EXTRACT… + Replace…)
                                       ▼
                              [7] Reagrupar key strings (s_N → string_N, em todos os JSON)
                                       ▼
                              [8] Process Libs + Resolve References  (cues compostas / externas)
                                       ▼
        JSON Final/ (S0X.json, Key_Strings.json, Key_Episódios.json, Cues_Index_*.json)
                                       ▼
                              [9] Gerar HTML final ──► JSON Final/HTML/S0X_<idioma>.html + S0X.log
```

---

## 3. Antes de correr seja o que for

- **Python 3.12** (testado). Os scripts de tradução instalam sozinhos `deepl`, `tqdm`, `transformers`, `torch`, `sentencepiece`, `sacremoses`.
- **Correr cada script a partir da pasta onde estão os dados.** Usam `os.getcwd()`:
  - `1-`, `3-`, `ParsingIndexes`, `ParsingMovies`, `ProcessJSON_index*` procuram os `.txt`/`.json` numa subpasta **`Data/`** da pasta atual.
  - `2-` procura os `.json` na **própria pasta atual** (não em `Data/`).
  - `Gerar HTML final.py`, `Reagrupar…`, `Process Libs`, `Resolve…` trabalham na pasta atual (têm de ser corridos **dentro de `JSON Final/`**).
- **Windows + UTF-8:** a consola cp1252 rebenta com caracteres como `≥` e com o japonês. Correr com `$env:PYTHONUTF8=1` (PowerShell) antes de qualquer script.
- **Tudo é interativo** (`input()` por todo o lado, menus numerados para escolher ficheiros). Não dá para correr em automático sem os alterar.
- **Backups automáticos:** vários scripts copiam-se a si próprios para `Backup Scripts/` ou `Data/` no fim (`*_backup.py`). Não são código vivo.
- **Caminhos antigos** embutidos em alguns scripts, de máquinas que já não existem: `G:\O meu disco\SM\MusicSheets\…`, `C:\Users\Sammu\O meu disco\SM\MusicSheets\…`, `C:\Users\Sammu\Desktop\Cues\season1.txt`, `/mnt/chromeos/MyFiles/Scripts/Cues` (Chromebook). Ao reutilizar, ajustar à mão.

---

## 4. Passo a passo

### Parte A — Episódios de uma temporada (repetir para S01…S05)

**A0. Obter o texto (fora do projeto).** As imagens estão em `Data/ImagesS0X`. Foram passadas por OCR (ferramenta que não está documentada aqui) e o texto guardado em `Data/raw/Episodios_S0X.txt`. Os prompts que usei para pedir a um LLM que escrevesse o parser estão em `Data/Instruções GPT/Instrucoes_episodios.txt` e `Instrucoes_index.txt` (histórico, não executar). `Data/cheatsheet.gif` e `Data/kana chart.gif` foram material de apoio para ler/corrigir o japonês.

**A1. `1- ParsingEpisodes.py`** — texto OCR → JSON estruturado.
1. Pede o nome de saída (sem extensão) e escolhe um `.txt` de `Data/`.
2. Limpa linhas: troca `半` por `.5"`, `【第`/`「第` por `第`, `ライブラリー` por texto largo, `//` por `!!`, e põe espaços à volta de `+`.
3. Deteta episódios pelo padrão `第N話` e **avisa se faltar algum número na sequência** ("Nice! Every episode is here" quando está tudo).
4. Divide cada episódio em `TOP` / `A` / `B` (reconhece variações do OCR: `Aパ`, `A パ`, `Aバ`, `Aハ`…). **Aborta se faltar a parte A ou B.**
5. Parte cada secção em faixas com um "comparador": uma nova faixa começa quando uma linha começa por um número igual ou +1 ao anterior (e o item anterior já terminou num código `X-…`).
6. Completa campos em falta com `"—"`, corrige o código da cue (`1-`→`I-`, `l`→`1`, etc.) e normaliza o tempo.
- **Saída:** `<nome>_raw.json` e `<nome>_logs.txt`.
- **O que fazer a seguir:** abrir o `_logs.txt`. Cada linha `Episode N (A|B) - Array: [...]` é uma faixa que o parser não conseguiu arrumar (ex.: OCR juntou duas faixas, ou o título do episódio seguinte caiu dentro da lista — `第180 話` apareceu dentro do 179 em `S05_raw_logs.txt`). **Corrigir esses casos à mão no `_raw.json`** antes de avançar.

**A2. `2- ProcessJSON_of_episodes.py`** — tirar os textos para fora.
1. Escolhe o `_raw.json` da pasta atual.
2. Pergunta o **prefixo** (default `s`) e o **número inicial**. ⚠ O número inicial tem de continuar onde a temporada anterior acabou, para as chaves `s_N` não colidirem entre temporadas.
3. Para cada faixa substitui o nome (campo 1) por `s_N`, reaproveitando a mesma chave se o texto for igual. Normaliza o número da faixa (`3A`→`3a`, `3.`→`3'`) e valida-o com `^\d+['AaBbCc]?$`. **Se houver erros de validação, aborta e lista-os.**
4. Remove o campo `"—"` quando a linha ficou com 5 campos.
- **Saída:** `S0X_processed.json` (faixas com `s_N`) e `S0X_keys.json` (`{"s_N": "texto japonês"}`).
- Estado real: `S04_keys.json` existe; `S05_keys.json` tem 6 bytes (praticamente vazio) — as chaves da S05 acabaram noutro sítio **(inferido)**.

**A3. `3- ProcessJSON_of_strings.py`** — deduplicar o dicionário japonês.
1. Escolhe um `.json` de `Data/` (as chaves `s_N → texto`).
2. Se um texto já apareceu, a chave repetida passa a apontar para a primeira (`"s_40": "s_5"`).
- **Saída:** `Data/processed_<nome>.json`. O ficheiro de trabalho foi `Data/Keys_String_JP.json` → `Data/processed_Keys_String_JP.json`.

### Parte B — Índices dos CDs (listas de faixas por CD)

Além das folhas por episódio há "índices": para cada CD, as faixas com código `A-1`, duração e nome. Servem para descobrir de que CD vem cada cue (`1-57-1` = CD 1, disco 57, faixa 1).

**B1. `ParsingIndexes.py`** — texto OCR de `Data/raw/Index_S0X.txt` → `Index_S0X.json`.
- Secções começam em `【` ou `&` e o nome acaba na linha com `TIME`. Cada faixa são 4 linhas: `M-NO.`, `TIME`, `内容`, `収録CD`. Remove os cabeçalhos repetidos do OCR. Gera `<nome>_log.txt` com formatos inesperados.
- Prompt de origem: `Data/Instruções GPT/Instrucoes_index.txt`.

**B2. `ProcessJSON_indexSeasons.py`** — textos (campo 2) → chaves `Is_N`, normaliza tempos (`1min24"`→`1m24s`). Pergunta o número inicial. **Saída:** `Index_S0X_processed.json` + `Index_S0X_keys.json` (em `Data/`).

**B3. `JSON Final/Pythons/fazer lista de indexes dos Index_.py`** — passa os índices para o formato final. Pede o caminho do JSON e o número inicial de `string_N`; troca cabeçalhos, nomes de secção e textos japoneses por `string_N`, corrige `-s`/`…mm` nos tempos, valida cada faixa (4 campos, padrões de cue/CD) e escreve `<ficheiro>_references.json` (mapa `string_N → texto`) e `<ficheiro>_errors.log`. **Resultado final:** `JSON Final/Cues_Index_S0X.json`.

### Parte C — Filmes e especiais

- `ParsingMovies.py`: lê `Data/raw/Index_Movies.txt`. Um filme começa em `&`; as faixas são linhas com ≥5 campos separados por espaço; o resto vai para `log.txt`. ⚠ O nome de saída está **hardcoded**: `Movieeees_raw.json` (ignora o que se escreve ao início).
- `ProcessJSON_indexMovies.py`: chaves `Im_N` e normalização de tempos.
- **Resultado final:** `JSON Final/Cues_Index_MoviesSpecials.json`.
- ⚠ Provável bug: o parser escreve a chave `"list"` por filme, mas o `ProcessJSON_indexMovies.py` procura `"lists"` — por isso **não processaria nada**. Como existem `Index_Movies_raw.json` e `Index_Movies_keys.json` em `Data/raw/`, o passo foi concluído de outra forma ou com uma versão anterior do script (há versões em `Backup Scripts/`). Confirmar antes de reutilizar.

### Parte D — Dicionário multilingue

Aqui o histórico está menos documentado. Reconstrução:

**D1. Japonês → inglês.** Não há script no repo que o faça **(inferido: feito com um LLM/DeepL fora do projeto)**. O `TraduitorDeepL.py` espera um `Keys_String_EN.json` já pronto.

**D2. Inglês → português europeu:** `JSON Final/Pythons/TraduitorDeepL.py` — para cada `{chave: texto}` de `Keys_String_EN.json` traduz EN→`PT-PT` com DeepL e grava `Keys_String_PT.json`. Ignora valores que são referências (`s_`, `Im_`, `Is_`), usa cache para textos repetidos, mostra barra de progresso e **não exporta um idioma se houve algum erro**. Para outros idiomas, acrescentar entradas ao dicionário `languages` (códigos DeepL). A chave DeepL que está no ficheiro é antiga/inválida (o repo é privado).

**D3. Português → espanhol via catalão:** `JSON Final/Pythons/Tradutor Huggin.py` — modelos Helsinki-NLP (`pt→ca`, `ca→es`) a correr localmente; grava `Keys_String_CA.json` e `Keys_String_ES.json`. Foi uma experiência (o pivot por catalão é invulgar); FR/IT vieram de outra forma **(inferido)**.

**D4. Juntar tudo** num `Keys_String_Combined.json` com `[ja, en, pt, es, fr, it]` por chave (não está no repo; **inferido**).

**D5. Tapar buracos** (três utilitários em `JSON Final/Pythons/`, todos leem/escrevem na própria pasta):
- `EXTRACT FROM MAIN ENTRIES LESS THAN 5.py` → subconjunto das entradas com menos de 5 idiomas (`Keys_String_Extracted_Subset.json` + lista `.txt`).
- `EXTRACT FROM MAIN ENTRIES NO ENGLISH.py` → entradas com inglês vazio (`Keys_String_Extracted_English.json`).
- `Replace entries to main with translation from SUBSET.py` → depois de corrigir o subconjunto (à mão/outra tradução), reinsere-o no principal (`Keys_String_Combined_cleaned_replaced.json`).

**D6. `JSON Final/Reagrupar key strings.py`** — renomeação final das chaves.
1. Lê `Key_Episódios_novas.txt`, com linhas `string_N: [s_a, s_b, …]` (várias chaves provisórias → uma chave final).
2. Percorre **todos** os `.json` da pasta atual e troca, recursivamente, chaves **e** valores `s_x` por `string_N`.
3. Faz `.bak` de cada ficheiro alterado e imprime o resumo de substituições.
- ⚠ O caminho do ficheiro de mapeamento está **hardcoded** (`MAPPING_FILE = r"G:\O meu disco\SM\MusicSheets\JSON Final\Key_Episódios_novas.txt"`) — mudar para o caminho atual antes de correr.

**D7. Títulos dos episódios:** `JSON Final/Key_Episódios.json` (`id: "episodes-episodes"`) tem o título de cada episódio em 8 variantes (`ja, romanji, pt, pt-dub, en, es, fr, it`). Não há script que o gere; foi feito à mão/por tradução **(inferido)**. `pt-dub` = título da dobragem portuguesa.

### Parte E — Cues compostas e externas

**E1. `JSON Final/Pythons/Process Libs.py`** — olha para o campo 2 (código da cue) de cada faixa. Se bate com `^[A-Z]-\d+[a-zA-Z]?$` (ex. `A-2`, `I-3b`) fica; se tem `+` é uma **referência cruzada** (`crossref_N`); senão é uma **referência externa/biblioteca** (`lib_N`). Pergunta a chave a atribuir (Enter aceita o default). Atualiza o `S0X.json` no local e cria `S0X_crossreferences.json` / `S0X_library.json`.

**E2. `JSON Final/Pythons/Resolve References in Main JSON to the non duplicate.py`** — escolhe um ficheiro de referências e um principal e, para cada nome de faixa que é `s_/is_/im_N`, segue a cadeia de referências até à chave que tem de facto a lista de traduções. Grava `<principal>_resolved.json`.

**E3. `JSON Final/Pythons/Add cues to final HTML.py`** — método **antigo** de preencher o CD: cria `S0X_cues.json` inserindo o CD no índice 3 de cada faixa, e `missing_references.txt` com os códigos sem correspondência. O gerador de HTML novo já faz o preenchimento de CD ele próprio (ver §6).

### Parte F — Gerar o HTML

**`JSON Final/Gerar HTML final.py`** — correr **dentro de `JSON Final/`**:

```powershell
cd "JSON Final"
$env:PYTHONUTF8 = 1
python "Gerar HTML final.py" 2        # temporada 2; sem argumento pergunta o número
```

1. Lê `S02.json`; procura nos restantes `.json` **pelo campo `id`**: `episodes-episodes` (títulos) e `strings-dictionary` (textos). **Não mudar esses `id`.**
2. Os idiomas gerados são os de `strings-dictionary.languages` (ja, en, pt, es, fr, it). Os rótulos da tabela ("Parte A", "Nome da faixa"…) estão em `LABELS_BY_LANG` no topo do script; há também `pt-dub`.
3. Resolve cada `string_N` no idioma pedido (cai para inglês, depois para o índice 0, se faltar).
4. Normaliza e valida tempos; preenche a coluna CD a partir dos `Cues_Index_*.json`.
- **Saída:** `HTML/S02_<idioma>.html` ×6 e `HTML/S02.log` (log unificado por idioma).

---

## 5. Estado atual (verificado a correr o gerador numa cópia temporária)

| Temporada | JSON final | HTML no repo | Gerador corre? |
|---|---|---|---|
| S01 | ✅ `S01.json` | ✅ 6 idiomas | ✅ |
| S02 | ✅ | ❌ | ✅ (gera 6 HTML) |
| S03 | ✅ | ❌ | ✅ |
| S04 | ✅ | ❌ | ✅ |
| S05 | ✅ | ❌ | ✅ |
| Filmes/especiais | só índice (`Cues_Index_MoviesSpecials.json`) | ❌ | o gerador só trata `S01…S99` |

Ou seja: **o trabalho de dados está feito; falta correr o gerador para S02–S05 e publicar**. Ao correr as 5 temporadas gerou 30 HTML sem erro fatal, mas com os avisos abaixo.

---

## 6. Problemas conhecidos (a resolver quando retomar)

1. **Coluna CD fica vazia.** `build_cues_map` procura listas de listas diretamente nos valores de topo dos `Cues_Index_*.json`, mas esses ficheiros têm `{"string_S01": {"Headers":…, "Sections":{…}}}` (dicts). O mapa sai vazio e o log diz *"nenhum arquivo 'Cues' encontrado ou extraído"* em todas as temporadas. Solução: percorrer `Sections` e mapear `entrada[0] → entrada[-1]`.
2. **`HARDCODED_STRINGS` não está definido** em `Gerar HTML final.py` (linha ~180). Hoje não rebenta porque todas as referências existem; se aparecer uma `string_N` em falta, dá `NameError` em vez de a registar no log.
3. **Aviso "Segundos ≥ 61"** (99–175 linhas por idioma e temporada): as faixas com mais de 1 min estão guardadas como `109.5s`/`123s` e o validador espera `1m49.5s`. É só formatação — o HTML mostra `109.5s`. A função `normalize_time` devia converter para `m:ss`.
4. **Caminhos hardcoded** em `Reagrupar key strings.py`, `TraduitorDeepL.py`, `Tradutor Huggin.py` (§3).
5. **Bug provável** no pipeline de filmes (`list` vs `lists`, nome de saída fixo) (§4-C).
6. **`Cues_Index_S02.json.json`** — extensão duplicada no nome; é assim que está e é lido assim (o gerador só olha para o `id` interno).
7. **`S05_keys.json`** quase vazio (6 bytes) — as chaves da S05 não estão onde seria de esperar.
8. **Ficheiros intermédios em falta** no repo (`Keys_String_EN.json`, `Keys_String_PT.json`, `Keys_String_Combined.json`): existiam na máquina antiga (`G:\O meu disco`). O dicionário final está em `JSON Final/Key_Strings.json`.

---

## 7. Receitas

### Gerar o HTML das temporadas que faltam
```powershell
cd "JSON Final"; $env:PYTHONUTF8=1
foreach ($s in 2,3,4,5) { python "Gerar HTML final.py" $s }
```
(Os primeiros passos a corrigir antes: problema nº 1 acima, senão a coluna CD sai vazia.)

### Acrescentar uma nova temporada (S06…)
1. Pôr o texto OCR em `Data/raw/Episodios_S06.txt` e copiá-lo para `Data/`.
2. A1 → corrigir o `_logs.txt` à mão no `_raw.json`.
3. A2 com **número inicial maior que o último `s_N` usado** (olhar para o maior em `Data/Keys_String_JP.json`).
4. Juntar os novos textos ao dicionário japonês, A3, traduzir só o que for novo (D2–D5), `Reagrupar` (D6).
5. Índice de CDs: B1–B3. Cues compostas: E1–E2.
6. Gerar o HTML (F).

### Corrigir um título/tradução
Editar a entrada `string_N` em `JSON Final/Key_Strings.json` (ordem do array: `ja, en, pt, es, fr, it`) e regenerar o HTML da temporada. Não editar as folhas `S0X.json` para isto.

### Procurar de onde vem uma faixa
No `S0X.json`, o campo 2 (ex. `C-1B`) procura-se em `Cues_Index_S0X.json` → 4.º campo é o CD (`1-57-1`).

---

## 8. Mapa de ficheiros

```
README.md / AGENTS.md / CLAUDE.md      documentação
1- ParsingEpisodes.py, 2- …, 3- …      pipeline de episódios (A1–A3)
ParsingIndexes.py, ParsingMovies.py    pipeline de índices e filmes (B1, C)
ProcessJSON_indexSeasons.py, ProcessJSON_indexMovies.py   (B2, C)
S04_raw/keys.json, S05_raw/keys.json, S05_raw_logs.txt    intermédios das S04/S05
Backup Scripts/                        cópias automáticas de versões antigas (não editar)
Data/
  imagesS01, ImagesS02…05/                      digitalizações das folhas (fonte original)
  raw/                                 texto OCR (Episodios_S0X.txt, Index_*.txt), JSON intermédios, S02_raw.json
  Keys_String_JP.json, processed_Keys_String_JP.json   dicionário japonês (antes/depois de deduplicar)
  Instruções GPT/                      prompts usados para gerar os parsers
  Indexes.pdf, Index_*.png, *.gif      material de apoio (índices digitalizados, tabela de kana, cheatsheet)
JSON Final/
  S01.json … S05.json                  folhas finais por temporada
  Key_Strings.json                     dicionário final (6 idiomas)
  Key_Episódios.json                   títulos dos episódios (8 variantes)
  Key_Episódios_novas.txt              mapa s_N → string_N usado pelo Reagrupar
  Cues_Index_*.json                    índices de CD por temporada / filmes
  Gerar HTML final.py                  gerador de HTML (F)
  Reagrupar key strings.py             renomeação final de chaves (D6)
  HTML/                                saída (só S01 por agora)
  Pythons/                             utilitários e tradutores (D2–D5, E1–E3, B3)
```

## 9. Notas de repositório

O repositório é privado e é a única fonte de verdade; contém tudo (imagens, PDFs, o `.7z` de backup em `JSON Fina_backupl.7z`, ~40 MB). Não há cópias noutros locais.
