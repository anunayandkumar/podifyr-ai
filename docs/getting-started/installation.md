# Installation

## Requirements

- Python 3.10 or later
- FFmpeg (for audio stitching)
- An LLM API key (OpenAI or Azure OpenAI) for script generation
- TTS: Edge TTS (default) is free and requires no API key

## Install from PyPI

```bash
pip install podifyr-ai
```

This includes the free Edge TTS backend out of the box.

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

## Verify Installation

```bash
podifyr-ai --version
podifyr generate --help
```

## Minimal Usage (after install)

```bash
# Generate walkthrough with free Edge TTS
podifyr generate ./your-python-project --api-key sk-your-openai-key

# Or with Azure OpenAI
podifyr generate ./your-python-project \
  --api-key your-azure-key \
  --azure-endpoint https://your-resource.openai.azure.com \
  --azure-deployment gpt-4o-mini
```
