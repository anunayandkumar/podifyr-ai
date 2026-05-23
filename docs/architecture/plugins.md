# Plugin System

Podifyr supports pluggable TTS backends via Python entry points.

## Built-in Backends

| Backend | Key | Cost | Quality | Speed | API Key |
|---------|-----|------|---------|-------|---------|
| Edge TTS | `edge` | **Free** | Good | Fast | None |
| OpenAI TTS | `openai` | Low | Good | Fast | Required |
| Azure TTS | `azure` | Low | Good | Fast | Required |
| ElevenLabs | `elevenlabs` | Higher | Excellent | Medium | Required |

### Edge TTS (Default)

Uses Microsoft's free Edge neural voices. No API key required. Voice names (alloy, nova, etc.) are automatically mapped to Microsoft neural voices:

- `alloy` → en-US-AndrewMultilingualNeural
- `nova` → en-US-AvaMultilingualNeural
- `echo` → en-US-BrianMultilingualNeural
- `fable` → en-GB-RyanNeural
- `onyx` → en-US-SteffanNeural
- `shimmer` → en-US-EmmaMultilingualNeural

### OpenAI TTS

Uses the OpenAI TTS API. Requires `OPENAI_API_KEY`.

### Azure TTS

Uses Azure OpenAI TTS deployment. Requires Azure credentials.

### ElevenLabs

Premium quality voices. Install with: `pip install podifyr-ai[elevenlabs]`

## Creating a Custom Backend

### 1. Implement the Backend

```python
from pathlib import Path
from podifyr.audio.backends import BaseTTSBackend

class MyCustomBackend(BaseTTSBackend):
    """Custom TTS backend implementation."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "My Custom TTS"

    async def synthesize(self, text: str, output_path: Path, *, voice: str) -> bool:
        # Your implementation here
        ...

    async def close(self) -> None:
        # Cleanup
        ...
```

### 2. Register via Entry Point

In your package's `pyproject.toml`:

```toml
[project.entry-points."podifyr.audio_backends"]
custom = "my_package.backend:MyCustomBackend"
```

### 3. Use It

```bash
export PODIFYR_TTS_BACKEND=custom
podifyr-ai generate ./my-repo
```

## Protocol Definition

All backends must satisfy the `TTSBackend` protocol defined in `podifyr.core.protocols`:

```python
@runtime_checkable
class TTSBackend(Protocol):
    @property
    def name(self) -> str: ...
    async def synthesize(self, text: str, output_path: Path, *, voice: str) -> bool: ...
    async def close(self) -> None: ...
```
