# Quick Start

## 1. Install

```bash
pip install podifyr-ai
```

## 2. Generate a walkthrough

The simplest way — pass your API key directly:

```bash
podifyr-ai generate ./path/to/python/project --api-key sk-your-key
```

Or set it as an environment variable:

```bash
export OPENAI_API_KEY="sk-your-key-here"
podifyr-ai generate ./path/to/python/project
```

This will:
1. Parse all Python files and extract architecture metadata
2. Build a dependency graph and determine reading order
3. Generate a conversational script using AI (OpenAI/Azure)
4. Synthesize audio narration (free Edge TTS by default)
5. Output `walkthrough.mp3` and `walkthrough_script.md`

## 3. Use Azure OpenAI

```bash
podifyr-ai generate ./project \
  --api-key your-azure-key \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini
```

## 4. Script-only mode

If you just want the script without audio:

```bash
podifyr-ai generate ./project --skip-audio
```

## 5. Customize output

```bash
podifyr-ai generate ./project \
  --output ./my-walkthrough \
  --voice nova \
  --tts-backend edge \
  --concurrency 3 \
  --graph-details
```

## 6. Configuration file (optional)

For repeated use, create a `.env` file:

```bash
podifyr-ai config init
# Edit .env with your settings
```

## CLI Reference

```
podifyr-ai generate <REPO_PATH>     Generate a walkthrough
podifyr-ai config init              Create .env configuration
podifyr-ai config show              Display current settings
podifyr-ai cache clear              Clear cached data
podifyr-ai cache stats              Show cache statistics
podifyr-ai --version                Show version
```
