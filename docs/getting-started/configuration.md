# Configuration

Podifyr-AI is **100% CLI-driven**. There are no `.env` files, no `PODIFYR_*` environment variables, and no config sub-command. Every run is fully described by the flags passed to `podifyr-ai generate`.

## Picking an LLM Provider

The `--provider` (or `-p`) flag selects the LLM backend. Three providers are supported:

| Provider | Flag | Notes |
|----------|------|-------|
| OpenAI    | `--provider openai` (default) | Needs `--api-key` |
| Azure OpenAI | `--provider azure` | Needs `--api-key`, `--azure-endpoint`, `--azure-deployment` |
| Ollama (local) | `--provider ollama` | No API key, expects a running local server |

### OpenAI

```bash
podifyr-ai generate ./my-repo \
  --provider openai \
  --api-key sk-... \
  --model gpt-4o-mini
```

### Azure OpenAI

```bash
podifyr-ai generate ./my-repo \
  --provider azure \
  --api-key <azure-key> \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini \
  --azure-api-version 2024-12-01-preview
```

### Ollama

Run Ollama locally and pull a model first:

```bash
ollama serve
ollama pull llama3
```

Then:

```bash
podifyr-ai generate ./my-repo \
  --provider ollama \
  --model llama3 \
  --ollama-base-url http://localhost:11434
```

## TTS Configuration

The TTS backend is independent of the LLM provider.

| Flag | Choices | Default |
|------|---------|---------|
| `--tts-backend` | `edge`, `openai`, `elevenlabs` | `edge` |
| `--voice` | Backend-specific voice identifier | `alloy` |
| `--tts-api-key` | API key for `openai` / `elevenlabs` backends | Falls back to `--api-key` |
| `--concurrency` / `-c` | Max parallel TTS requests (1–20) | `5` |

When `--provider azure` is combined with `--tts-backend openai`, the Azure TTS deployment is used automatically (it reuses the Azure endpoint and API key).

## Other Flags

| Flag | Description |
|------|-------------|
| `--output` / `-o` | Output directory (default: `./podifyr_output`) |
| `--skip-audio` | Generate the script only — no audio |
| `--no-cache` | Disable disk caching for this run |
| `--graph-details` | Print detailed dependency-graph metrics |
| `--verbose` / `-V` | Verbose debug logging |

## Cache

The disk cache lives in the OS-standard cache directory. Manage it with the `cache` sub-command:

```bash
podifyr-ai cache stats
podifyr-ai cache clear
```
