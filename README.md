# 🎙️ Podifyr

**Automated developer onboarding via podcast-style audio walkthroughs of Python codebases.**

[![CI](https://github.com/podifyr/podifyr/actions/workflows/ci.yml/badge.svg)](https://github.com/podifyr/podifyr/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/podifyr)](https://pypi.org/project/podifyr/)
[![Python](https://img.shields.io/pypi/pyversions/podifyr)](https://pypi.org/project/podifyr/)
[![License](https://img.shields.io/github/license/podifyr/podifyr)](LICENSE)
[![codecov](https://codecov.io/gh/podifyr/podifyr/branch/main/graph/badge.svg)](https://codecov.io/gh/podifyr/podifyr)

---

## What is Podifyr?

Podifyr is a CLI tool that analyzes a Python repository's architecture and generates a conversational, podcast-style audio walkthrough. It's designed to accelerate developer onboarding by letting new team members listen to an AI-generated explanation of the system architecture — like having a senior engineer give them a KT session on day one.

## How It Works

```
Repository → AST Parsing → Dependency Graph → AI Script → TTS Audio → 🎧 Walkthrough
```

1. **Parse**: Traverses the repo and extracts structural metadata (classes, functions, imports) using Python's AST module
2. **Graph**: Builds a directed dependency graph to understand module relationships and reading order
3. **Script**: Uses a multi-agent LangGraph pipeline (Analyzer → Scriptwriter) to generate conversational explanations
4. **Audio**: Synthesizes speech via Edge TTS (free) or OpenAI TTS with concurrent chunk generation and FFmpeg stitching

## Quick Start

### Installation

```bash
pip install podifyr
```

### Generate a Walkthrough (Free — No API key for TTS)

```bash
# Set your OpenAI API key (needed for script generation)
export OPENAI_API_KEY="sk-..."

# Generate a walkthrough — uses free Edge TTS by default
podifyr generate ./path/to/your/repo
```

### Or pass everything via CLI (no env setup needed)

```bash
podifyr generate ./my-project \
  --api-key sk-your-key-here \
  --tts-backend edge \
  --output ./walkthrough
```

### Azure OpenAI

```bash
podifyr generate ./my-project \
  --api-key your-azure-key \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini \
  --tts-backend edge
```

## CLI Reference

```
podifyr generate <REPO_PATH>     Generate a podcast walkthrough

Options:
  --output, -o PATH              Output directory [default: ./podifyr_output]
  --api-key TEXT                  OpenAI/Azure API key (or set OPENAI_API_KEY)
  --tts-backend TEXT              TTS: 'edge' (free), 'openai', 'elevenlabs'
  --voice TEXT                    Voice: alloy, echo, fable, onyx, nova, shimmer
  --azure-endpoint TEXT           Azure OpenAI endpoint (enables Azure mode)
  --azure-deployment TEXT         Azure chat model deployment name
  --skip-audio                    Generate script only, skip audio
  --no-cache                      Disable caching for this run
  --concurrency, -c INT           Max concurrent TTS requests [1-20]
  --graph-details                 Show dependency graph metrics
  --verbose, -V                   Enable debug logging

podifyr config init              Create .env configuration file
podifyr config show              Display current resolved settings
podifyr cache clear              Clear cached data
podifyr cache stats              Show cache statistics
podifyr --version                Show version
```

## TTS Backends

| Backend | Cost | API Key Required | Quality | Setup |
|---------|------|-----------------|---------|-------|
| **Edge** (default) | Free | No | Good (Microsoft Neural) | None |
| **OpenAI** | ~$0.015/1K chars | Yes (`OPENAI_API_KEY`) | Good | API key |
| **ElevenLabs** | Varies | Yes (`ELEVENLABS_API_KEY`) | Excellent | `pip install podifyr[elevenlabs]` |

## Configuration

Settings are resolved in priority order: **CLI flags > Environment variables > `.env` file > Defaults**

```bash
# Generate a template .env file
podifyr config init

# View resolved configuration
podifyr config show
```

### Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (for LLM script generation) |
| `PODIFYR_TTS_BACKEND` | `edge` | TTS backend: `edge`, `openai`, `elevenlabs` |
| `PODIFYR_TTS_VOICE` | `alloy` | Voice identifier |
| `PODIFYR_AZURE_ENABLED` | `false` | Use Azure OpenAI for LLM |
| `PODIFYR_AZURE_ENDPOINT` | — | Azure OpenAI resource URL |
| `PODIFYR_AZURE_API_KEY` | — | Azure API key |
| `PODIFYR_AZURE_CHAT_DEPLOYMENT` | — | Azure model deployment name |

See [docs/getting-started/configuration.md](docs/getting-started/configuration.md) for the full reference.

## Features

- 🧠 **AST-based analysis** — Extracts architecture without executing code
- 🔗 **Dependency graphing** — Cycle-aware topological sorting with NetworkX
- 🤖 **Multi-agent pipeline** — LangGraph orchestration with analyzer + scriptwriter nodes
- 🔊 **Free TTS included** — Edge TTS (Microsoft Neural voices) works out of the box
- 🔌 **Plugin backends** — Swappable TTS providers (Edge, OpenAI, ElevenLabs)
- ☁️ **Azure OpenAI** — Full support for Azure OpenAI deployments
- 💾 **Smart caching** — Content-hash invalidation avoids redundant API calls
- 📊 **Rich CLI** — Beautiful progress bars, graph metrics, and colored output
- 🐳 **Docker support** — Reproducible builds with multi-stage Dockerfile
- ✅ **Production-grade** — Strict typing, structured logging, comprehensive test suite

## Architecture

```
src/podifyr/
├── core/          # Exceptions, constants, protocols, types
├── config/        # Pydantic settings with layered resolution
├── logging/       # Structured logging with structlog
├── utils/         # Filesystem helpers, retry logic, async patterns
├── cache/         # Disk-based caching with content-hash invalidation
├── parsing/       # AST visitor, models, filtering engine
├── graph/         # NetworkX graph builder and analyzer
├── agents/        # LangGraph nodes, prompts, orchestrator
├── audio/         # TTS backends (Edge, OpenAI, ElevenLabs, Azure), stitcher
└── cli/           # Typer commands with rich display
```

## Requirements

- Python 3.10+
- FFmpeg (for audio stitching)
- An LLM API key (OpenAI or Azure OpenAI) for script generation
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
git clone https://github.com/podifyr/podifyr.git
cd podifyr
pip install -e ".[dev,docs,all]"

# Run tests
pytest

# Run linter and type checker
ruff check src/ tests/
mypy src/
```

## License

MIT — see [LICENSE](LICENSE) for details.
