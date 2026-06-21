# Podifyr-AI

**AI-powered CLI that transforms Python codebases into true multi-speaker podcast walkthroughs using LangGraph agentic pipelines, AST analysis, dependency graph traversal, and neural text-to-speech synthesis**

[![CI](https://github.com/anunayandkumar/podifyr-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/anunayandkumar/podifyr-ai/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/podifyr-ai)](https://pypi.org/project/podifyr-ai/)
[![Python](https://img.shields.io/pypi/pyversions/podifyr-ai)](https://pypi.org/project/podifyr-ai/)
[![License](https://img.shields.io/github/license/anunayandkumar/podifyr-ai)](LICENSE)
[![codecov](https://codecov.io/gh/anunayandkumar/podifyr-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/anunayandkumar/podifyr-ai)

---

## What is Podifyr-AI?

Podifyr-AI is a CLI tool that analyzes a Python repository's architecture and generates a conversational, podcast-style audio walkthrough. It's designed to accelerate developer onboarding by letting new team members listen to an AI-generated explanation of the system architecture — like having a senior engineer give them a KT session on day one.

## How It Works

```
Repository → AST Parsing → Dependency Graph → Host ↔ Expert Dialogue → Multi-Voice TTS → 🎧
```

1. **Parse**: Traverses the repo and extracts structural metadata (classes, functions, imports) using Python's AST module
2. **Graph**: Builds a directed dependency graph to understand module relationships and reading order
3. **Script**: Runs a multi-agent LangGraph pipeline — the **Analyzer** produces a technical summary, then the **Dialogue Writer** rewrites it as a Host/Expert conversation (JSON turns)
4. **Audio**: Synthesizes each turn with a distinct TTS voice (free Edge TTS by default), then FFmpeg-stitches the full episode

> Prefer a single-narrator walkthrough? Pass `--style monologue` to switch back to the classic single-voice mode.

## Quick Start

### Installation

```bash
pip install podifyr-ai
```

Podifyr-AI is now more user friendly. Pick a provider (`openai`, `azure`, or `ollama`) and pass the relevant flags.

### OpenAI

```bash
podifyr-ai generate ./my-project \
  --provider openai \
  --api-key sk-your-key-here
```

### Azure OpenAI

```bash
podifyr-ai generate ./my-project \
  --provider azure \
  --api-key <your-azure-key> \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini
```

### Ollama (local, no API key)

Make sure Ollama is running locally (`ollama serve`) and the model is pulled (`ollama pull llama3`):

```bash
podifyr-ai generate ./my-project \
  --provider ollama \
  --model llama3
```

By default audio is synthesized with the free **Edge TTS** backend — no API key required.

### Dialogue voices (default mode)

Dialogue mode uses two distinct voices. Defaults work for the OpenAI TTS backend; for **Edge TTS** override them with Microsoft Neural voice ids:

```bash
podifyr-ai generate ./my-project \
  --provider ollama --model llama3 \
  --host-voice en-US-AriaNeural \
  --expert-voice en-US-GuyNeural
```

To get a classic single-voice walkthrough instead:

```bash
podifyr-ai generate ./my-project --style monologue --voice nova
```

## CLI Reference

```
podifyr-ai generate <REPO_PATH>     Generate a podcast walkthrough

Provider options:
  --provider, -p TEXT             LLM provider: openai (default), azure, ollama
  --model, -m TEXT                LLM model name (e.g. gpt-4o-mini, llama3)
  --api-key TEXT                  API key for the LLM provider (openai/azure)
  --azure-endpoint TEXT           Azure OpenAI endpoint URL
  --azure-deployment TEXT         Azure chat model deployment name
  --azure-api-version TEXT        Azure OpenAI API version
  --ollama-base-url TEXT          Ollama server URL [default: http://localhost:11434]

Output and audio options:
  --output, -o PATH               Output directory [default: ./podifyr_output]
  --style TEXT                    Podcast style: 'dialogue' (default, two speakers) or 'monologue'
  --tts-backend TEXT              TTS: 'edge' (free, default), 'openai', 'elevenlabs'
  --voice TEXT                    Voice for monologue style (e.g. alloy, echo, fable, onyx, nova)
  --host-voice TEXT               Voice id for the Host speaker (dialogue mode)
  --expert-voice TEXT             Voice id for the Expert speaker (dialogue mode)
  --tts-api-key TEXT              API key for the TTS backend (falls back to --api-key)
  --skip-audio                    Generate script only, skip audio
  --no-cache                      Disable caching for this run
  --concurrency, -c INT           Max concurrent TTS requests [1-20]
  --graph-details                 Show dependency graph metrics
  --verbose, -V                   Enable debug logging

podifyr-ai cache clear              Clear cached data
podifyr-ai cache stats              Show cache statistics
podifyr-ai --version                Show version
```

## TTS Backends

| Backend | Cost | API Key Required | Quality | Setup |
|---------|------|-----------------|---------|-------|
| **Edge** (default) | Free | No | Good (Microsoft Neural) | None |
| **OpenAI** | ~$0.015/1K chars | Yes (`--tts-api-key` or `--api-key`) | Good | API key |
| **ElevenLabs** | Varies | Yes (`--tts-api-key`) | Excellent | `pip install podifyr-ai[elevenlabs]` |

## Configuration

Podifyr-AI is purely CLI-driven — there is **no `.env` file, no `PODIFYR_*` env vars, no `config` sub-command**. Every run is fully described by the flags you pass to `podifyr-ai generate`.

## Features

- **True two-speaker dialogue** — Host ↔ Expert conversation with distinct TTS voices (default), or single-narrator monologue mode (`--style monologue`)
- **AST-based analysis** — Extracts architecture without executing code
- **Dependency graphing** — Cycle-aware topological sorting with NetworkX
- **Multi-agent pipeline** — LangGraph orchestration with Analyzer + (Scriptwriter │ Dialogue) nodes
- **Unified LLM interface** — One CLI, three providers: OpenAI, Azure OpenAI, Ollama
- **Free TTS included** — Edge TTS (Microsoft Neural voices) works out of the box
- **Plugin backends** — Swappable TTS providers (Edge, OpenAI, ElevenLabs)
- **Smart caching** — Content-hash invalidation avoids redundant API calls
- **Rich CLI** — Beautiful progress bars, graph metrics, and colored output
- **Docker support** — Reproducible builds with multi-stage Dockerfile
- **Production-grade** — Strict typing, structured logging, comprehensive test suite

## Architecture

```
src/podifyr/
├── core/          # Exceptions, constants, protocols, types
├── config/        # Plain pydantic models for runtime settings (CLI-driven)
├── logging/       # Structured logging with structlog
├── utils/         # Filesystem helpers, retry logic, async patterns
├── cache/         # Disk-based caching with content-hash invalidation
├── parsing/       # AST visitor, models, filtering engine
├── graph/         # NetworkX graph builder and analyzer
├── llm/           # Unified provider factory (OpenAI, Azure, Ollama)
├── agents/        # LangGraph nodes, prompts, orchestrator
├── audio/         # TTS backends (Edge, OpenAI, ElevenLabs, Azure), stitcher
└── cli/           # Typer commands with rich display
```

## Requirements

- Python 3.10+
- FFmpeg (for audio stitching)
- One of: an OpenAI API key, an Azure OpenAI deployment, or a local Ollama server
- TTS: Edge TTS works free with no key; OpenAI/ElevenLabs require API keys

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
winget install ffmpeg
```

## Development

```bash
# Clone and install in dev mode
git clone https://github.com/anunayandkumar/podifyr-ai.git
cd podifyr-ai
pip install -e ".[dev,docs,all]"

# Run tests
pytest

# Run linter and type checker
ruff check src/ tests/
mypy src/
```

## License

MIT — see [LICENSE](LICENSE) for details.
