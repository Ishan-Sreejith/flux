# Animal1010101 (Base+Bit Lexical Engine)

This is a standalone project implementing the **BaseWord + BitString** architecture.

## What it does
- Decomposes words into a **Semantic Prime** (BaseWord).
- Traverses a **binary flowchart** (taxonomy tree).
- Produces **Prefix + BitString** (e.g., `Animal101`).
- Extracts **context parameters** as the word traverses the tree.

## Quick start

Encode a word:

```bash
python3 -m animal1010101.cli encode dog
```

Compare two words:

```bash
python3 -m animal1010101.cli compare dog "golden retriever"
```

Show parameters for a word:

```bash
python3 -m animal1010101.cli params dog
```

Similarity scoring:

```bash
python3 -m animal1010101.cli similarity dog "golden retriever"
```

Internet lookup + auto-lexicon (Wikidata, writes to `lexicon_auto.json`):

```bash
python3 -m animal1010101.cli lookup "red panda"
```

Train a massive category from Wikidata (writes a JSON lexicon mapping):

```bash
python3 -m animal1010101.cli train-category Q7377 --limit 100 --out mammals.json
```

Import a lexicon into the auto store:

```bash
python3 -m animal1010101.cli import-lexicon mammals.json
```

Train from a plain text list (one word or phrase per line):

```bash
python3 -m animal1010101.cli train-list top_10k.txt --limit 10000 --sleep-ms 120 --out top10k.json --import
```

Teach a specific word directly from Wikidata:

```bash
python3 -m animal1010101.cli learn mouse giraffe elephant
```

Create a snapshot or rollback:

```bash
python3 -m animal1010101.cli snapshot --reason "before training"
python3 -m animal1010101.cli snapshots
python3 -m animal1010101.cli rollback --to /absolute/path/to/lexicon_snapshots/lexicon_auto_YYYYMMDD_HHMMSS.json
```

Run the evaluation suite:

```bash
python3 -m animal1010101.cli eval
```

Evaluate with auto-learning (writes to lexicon_auto.json):

```bash
python3 -m animal1010101.cli eval --auto-learn
```

Train parameter weights (gradient training):

```bash
python3 -m animal1010101.cli train-weights
```

Train disambiguation weights (word sense selection):

```bash
python3 -m animal1010101.cli train-disambig
```

Auto-expand lexicon from Wikidata categories:

```bash
python3 -m animal1010101.cli auto-expand --limit 120
```

CLI wrappers:

```bash
# Add bin/ to PATH once:
export PATH=\"/Users/ishan/flux/bin:$PATH\"

# With internet (Wikidata + optional live Wikipedia):
flux ask \"Explain dogs in simple terms\"
flux chat --live

# Offline (no web):
noux ask \"Explain dogs in simple terms\"
noux chat

# Add a training example:
noux train \"Explain gravity\" --prime Object --traits \"intelligent,artificial\"
python3 -m animal1010101.cli train-weights
```

## Files
- `taxonomy.json`: defines primes, binary branches, and parameter updates.
- `lexicon.json`: maps known words to taxonomy paths.
- `lexicon_auto.json`: auto-populated by internet lookup.
- `engine.py`: core traversal and parameter extraction.
- `cli.py`: command-line interface.
- `wikidata_lookup.py`: Wikidata search + category fetch.
- `schema_data.json`: built-in schemas (object/person/self/social/event).
- `schema_engine.py`: schema assimilation/accommodation engine.

## Schema System (Human Tree)

Interpret a sentence and retrieve active schemas:

```bash
python3 -m animal1010101.cli schema "dog teacher restaurant"
```

Get a script for an event schema:

```bash
python3 -m animal1010101.cli script restaurant
```

## Simple Q&A (Algorithm)

Use the simplified algorithm to extract params, search, and answer:

```bash
python3 -m animal1010101.simple_qa "Explain dogs in simple terms"
```

## Extending the system
Add new branches to `taxonomy.json` and add word mappings in `lexicon.json`.
