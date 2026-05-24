# Quick Start

## 1. Install

```bash
pip install podifyr-ai
```

Podifyr-AI is **fully CLI-driven** — there is no `.env` file or environment-variable configuration. Pick a provider and pass the relevant flags.

## 2. Generate a walkthrough

### OpenAI

```bash
podifyr-ai generate ./path/to/python/project \
  --provider openai \
  --api-key sk-your-key
```

### Azure OpenAI

```bash
podifyr-ai generate ./path/to/python/project \
  --provider azure \
  --api-key <your-azure-key> \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini
```

### Ollama (local)

Start Ollama and pull a model first:

```bash
ollama serve
ollama pull llama3
```

Then generate:

```bash
podifyr-ai generate ./path/to/python/project \
  --provider ollama \
  --model llama3
```

Each run will:

1. Parse all Python files and extract architecture metadata
2. Build a dependency graph and determine reading order
3. Generate a conversational script using the chosen LLM
4. Synthesize audio narration (free Edge TTS by default)
5. Output `walkthrough.mp3` and `walkthrough_script.md`

## 3. Script-only mode

If you just want the script without audio:

```bash
podifyr-ai generate ./project --provider openai --api-key sk-... --skip-audio
```

## 4. Customize output

```bash
podifyr-ai generate ./project \
  --provider openai --api-key sk-... \
  --output ./my-walkthrough \
  --voice nova \
  --tts-backend edge \
  --concurrency 3 \
  --graph-details
```

## CLI Reference

```
podifyr-ai generate <REPO_PATH>     Generate a walkthrough
podifyr-ai cache clear              Clear cached data
podifyr-ai cache stats              Show cache statistics
podifyr-ai --version                Show version
```
