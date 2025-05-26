# sm-cue-sheets
Code to generate html tables and json files from the SM cue sheets of the 90

This Python program automates the parsing, correction, and multilingual translation of musical cue sheet data from the *Sailor Moon* anime franchise. It processes raw text or JSON inputs and generates clean, structured data with support for Japanese, English, Portuguese (EU), Spanish, French, and Italian.

## Features

- **Cue sheet parsing** from OCR-extracted or hand-edited text/JSON
- **Automatic time correction** (handles formats like `1'02"半`)
- **Duplicate and circular reference detection**
- **Flexible JSON structure recognition**
- **Dynamic language mapping** based on internal metadata
- **Multilingual translation pipeline**
- **Support for special terms like character names and attack names**
- **HTML generation** for publishing indexes or cue lists
- **Batch processing** with logging and error reports

## Supported Input Types

- `S0X.json` – Season cue data files
- `Key_Strings.json` – String dictionary with translations
- `Key_Episodes.json` – Episode titles in multiple languages
- `Metadata.json` – General metadata and cue mapping logic

## Output

- Cleaned and corrected JSON files
- HTML pages in `/HTML` subfolder for web use
- Log files with:
  - Time corrections
  - Missing or circular string references

## Example Use Case

You have a text file or JSON file containing musical cues from episode 163. The program:
1. Parses each entry.
2. Fixes malformed time strings like `1'02"半` → `1min02.5`.
3. Detects invalid or circular string references (`string_1160 → string_1160`).
4. Translates valid entries into all target languages.
5. Exports clean JSON and HTML indexes for integration on a fan site or documentation.

## Usage

### Basic usage
```bash
python process_cues.py

