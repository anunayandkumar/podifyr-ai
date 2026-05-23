# Configuration

Podifyr uses a layered configuration system. Settings are resolved in this priority order:

1. CLI flags (highest priority)
2. Environment variables
3. `.env` file
4. Built-in defaults (lowest priority)

## Initialize Configuration

```bash
podifyr-ai config init
```

This creates a `.env` file with all available settings and documentation.

## CLI Flags (Highest Priority)

All key settings can be passed directly on the command line:

```bash
podifyr-ai generate ./my-repo \
  --api-key sk-your-key \
  --tts-backend edge \
  --voice nova \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini \
  --output ./output \
  --concurrency 5
```

## Providers

### LLM (Script Generation)

- **OpenAI** (default) — uses the public OpenAI API
- **Azure OpenAI** — uses your Azure OpenAI resource deployments

### TTS (Audio Synthesis)

| Backend | Key | Cost | Quality |
|---------|-----|------|---------|
| `edge` (default) | None needed | **Free** | Good (Microsoft Neural) |
| `openai` | `OPENAI_API_KEY` | ~$0.015/1K chars | Good |
| `elevenlabs` | `ELEVENLABS_API_KEY` | Varies | Excellent |

## Environment Variables

### Required (Public OpenAI)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM script generation |

### Azure OpenAI Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PODIFYR_AZURE_ENABLED` | `false` | Enable Azure OpenAI provider |
| `PODIFYR_AZURE_ENDPOINT` | | Azure resource endpoint URL |
| `PODIFYR_AZURE_API_KEY` | | Azure OpenAI API key |
| `PODIFYR_AZURE_API_VERSION` | `2024-12-01-preview` | Azure API version |
| `PODIFYR_AZURE_CHAT_DEPLOYMENT` | | Deployment name for chat model |

### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PODIFYR_LLM_MODEL` | `gpt-4o-mini` | LLM model to use |
| `PODIFYR_LLM_TEMPERATURE` | `0.3` | Sampling temperature |
| `PODIFYR_LLM_MAX_TOKENS` | `2048` | Max response tokens |

### TTS Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PODIFYR_TTS_BACKEND` | `edge` | Backend: `edge`, `openai`, or `elevenlabs` |
| `PODIFYR_TTS_VOICE` | `alloy` | Voice identifier |
| `PODIFYR_TTS_MODEL` | `tts-1` | TTS model (OpenAI backend only) |
| `PODIFYR_MAX_CONCURRENT_REQUESTS` | `5` | Parallel TTS requests |

### Cache Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PODIFYR_CACHE_ENABLED` | `true` | Enable/disable caching |
| `PODIFYR_CACHE_TTL_SECONDS` | `86400` | Cache expiry (24h) |

### Logging Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PODIFYR_LOG_LEVEL` | `INFO` | Log level |
| `PODIFYR_LOG_FORMAT` | `console` | Output format: `console` or `json` |

## Azure OpenAI Quick Start

### Option 1: CLI flags (simplest)

```bash
podifyr generate ./src \
  --api-key your-azure-key \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini \
  --tts-backend edge
```

### Option 2: .env file

```dotenv
PODIFYR_AZURE_ENABLED=true
PODIFYR_AZURE_ENDPOINT=https://your-resource.openai.azure.com
PODIFYR_AZURE_API_KEY=your-azure-key
PODIFYR_AZURE_CHAT_DEPLOYMENT=gpt-4o-mini
PODIFYR_TTS_BACKEND=edge
```

Then run:

```bash
podifyr generate ./src
```
