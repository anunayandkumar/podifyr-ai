# Architecture Overview

## System Design

Podifyr follows a pipeline architecture with clearly separated stages:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Parser  │───▶│  Graph   │───▶│  Agents  │───▶│  Audio   │
│  Engine  │    │  Builder │    │ Pipeline │    │  Synth   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     ▼               ▼               ▼               ▼
 ModuleMetadata  nx.DiGraph     Script Chunks    .mp3 Files
```

## Package Structure

```
src/podifyr/
├── core/           # Foundation layer (no internal deps)
│   ├── exceptions.py   # Custom exception hierarchy
│   ├── constants.py    # Application-wide constants
│   ├── protocols.py    # Interface definitions (Protocols)
│   └── types.py        # Shared TypedDict definitions
│
├── config/         # Configuration management
│   └── settings.py     # Pydantic settings with layered resolution
│
├── logging/        # Observability
│   └── setup.py        # Structured logging with structlog
│
├── utils/          # Shared utilities
│   ├── fs.py           # Filesystem operations
│   ├── retry.py        # Retry with exponential backoff
│   └── async_helpers.py # Concurrency patterns
│
├── cache/          # Performance optimization
│   └── manager.py      # Disk cache with content-hash invalidation
│
├── parsing/        # Stage 1: Code Analysis
│   ├── models.py       # Pydantic models for metadata
│   ├── visitors.py     # AST node visitors
│   ├── engine.py       # Orchestration + caching
│   └── filters.py      # File importance/filtering
│
├── graph/          # Stage 2: Dependency Mapping
│   ├── models.py       # Graph data models
│   ├── builder.py      # Graph construction
│   └── analyzer.py     # Topological sort + metrics
│
├── agents/         # Stage 3: Script Generation
│   ├── state.py        # LangGraph state definition
│   ├── prompts/        # LLM prompt templates
│   ├── nodes/          # Individual agent nodes
│   │   ├── analyzer.py     # Technical summary node
│   │   └── scriptwriter.py # Conversational rewrite node
│   └── orchestrator.py # Graph compilation + execution
│
├── audio/          # Stage 4: Audio Synthesis
│   ├── backends/       # Pluggable TTS providers
│   │   ├── edge_tts.py     # Edge TTS (free, default)
│   │   ├── openai_tts.py   # OpenAI implementation
│   │   ├── azure_tts.py    # Azure OpenAI TTS
│   │   └── elevenlabs.py   # ElevenLabs implementation
│   ├── synthesizer.py # Concurrent chunk generation
│   └── stitcher.py    # FFmpeg concatenation
│
└── cli/            # User Interface
    ├── app.py          # Typer app assembly
    ├── display.py      # Rich display utilities
    └── commands/       # Sub-commands
        ├── generate.py     # Main generate workflow
        ├── config_cmd.py   # Config management
        └── cache_cmd.py    # Cache management
```

## Design Principles

1. **Graceful Degradation**: Each stage handles failures independently. A single unparseable file doesn't crash the pipeline.

2. **Plugin Architecture**: TTS backends implement a Protocol, allowing new providers without modifying core code.

3. **Content-Hash Caching**: Expensive operations (parsing, LLM calls) are cached with content-based invalidation.

4. **Structured Observability**: All logging uses structlog with key-value pairs for machine-parseable output.

5. **Layered Configuration**: Settings resolve from env vars, .env files, and CLI flags with clear precedence.
