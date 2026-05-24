# Installation

## Requirements

- Python 3.10 or later
- FFmpeg (for audio stitching)
- One of:
  - An OpenAI API key, or
  - An Azure OpenAI deployment + API key, or
  - A local Ollama server (no key required)
- TTS: Edge TTS (default) is free and requires no API key

## Install from PyPI

```bash
pip install podifyr-ai
```

This includes the free Edge TTS backend and the OpenAI/Azure/Ollama LLM bindings out of the box.

## Install with optional backends

```bash
# Include ElevenLabs TTS support
pip install podifyr-ai[elevenlabs]

# Install everything
pip install podifyr-ai[all]
```

## Install from source (development)

```bash
git clone https://github.com/anunayandkumar/podifyr-ai.git
cd podifyr-ai
pip install -e ".[dev,docs,all]"
```

## Install FFmpeg

FFmpeg is required for stitching audio chunks into a final MP3 file.

### macOS
```bash
brew install ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt-get install ffmpeg
```

### Windows
```bash
winget install ffmpeg
```

Or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Install Ollama (optional — local LLM)

If you want to use the `ollama` provider, install Ollama from [ollama.com](https://ollama.com), then pull a model:

```bash
ollama serve            # starts the local server
ollama pull llama3      # download a model
```

## Verify Installation

```bash
podifyr-ai --version
podifyr-ai generate --help
```

## Minimal Usage (after install)

```bash
# OpenAI with the free Edge TTS backend
podifyr-ai generate ./your-python-project --provider openai --api-key sk-...

# Azure OpenAI
podifyr-ai generate ./your-python-project \
  --provider azure \
  --api-key <azure-key> \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini

# Ollama (no API key)
podifyr-ai generate ./your-python-project --provider ollama --model llama3
```
