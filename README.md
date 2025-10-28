# Translation Quality Toolkit

This repository provides utilities for monitoring the quality of Chinese-to-English novel translations. The toolkit covers four key workflows:

1. **Automated checks** for encoding errors, missing paragraphs, and untranslated text.
2. **Glossary validation** to ensure consistent terminology based on bilingual dictionaries.
3. **Sampling tools** to queue chapters for manual review.
4. **Quality estimation metrics** (currently BLEU) when reference translations are available.

## Data format

Commands expect JSON Lines (JSONL) input where each object contains at least the following fields:

- `chapter`: Chapter identifier.
- `paragraph_index`: Zero-based paragraph index.
- `source`: Source language paragraph.
- `translation`: Machine translation output.

For metric computation, a companion JSONL file with `reference` text is required.

A sample dataset is provided under [`examples/`](examples/) to demonstrate the workflow.

## Command line usage

Install dependencies (standard library only) and run the CLI with Python:

```bash
python -m translation_quality.cli run-checks --input examples/sample_translations.jsonl
```

### Automated checks

```bash
python -m translation_quality.cli run-checks \
  --input examples/sample_translations.jsonl \
  --output reports/checks.json
```

### Glossary validation

```bash
python -m translation_quality.cli glossary \
  --input examples/sample_translations.jsonl \
  --glossary examples/glossary.csv
```

### Sampling for manual review

```bash
python -m translation_quality.cli sample \
  --input examples/sample_translations.jsonl \
  --sample-size 3 \
  --seed 42
```

### BLEU metric

```bash
python -m translation_quality.cli metrics \
  --translations examples/sample_translations.jsonl \
  --references examples/sample_references.jsonl
```

Each command optionally accepts `--output` to write results to a file rather than printing to stdout.
