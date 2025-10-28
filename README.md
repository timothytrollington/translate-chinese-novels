# Translation Pipeline for Chinese Novels

This repository provides a modular toolkit for translating raw Chinese novel chapters into English while preserving context, cultural nuances, and paragraph structure.

## Features

- **Segmenter** that splits large chapters into manageable paragraph and sentence-based segments.
- **Prompt templates** tuned for fidelity to cultivation terminology, respectful forms of address, and dialogue formatting.
- **Batch translation pipeline** that assembles prompts, calls the configured model or API, and recombines responses into a coherent chapter while keeping paragraph breaks.
- **Metadata logging** capturing model name, timestamp, estimated cost, and other run details for future auditing.

## Usage

1. Ensure you have a translation model client that implements `TranslationModel`. A `MockTranslationModel` is provided for local testing.
2. Run the command-line interface:

```bash
python -m translation path/to/chapter.txt output_directory --log logs/metadata.jsonl
```

The translated file will be written beside the original with headers separating the source and English text. Metadata entries are appended to the JSONL log when `--log` is provided.

## Examples

Sample input text is available under [`examples/sample_chapter.txt`](examples/sample_chapter.txt).
