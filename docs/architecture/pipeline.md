# Pipeline Architecture

The podifyr pipeline executes in four sequential stages, each with independent error handling.

## Stage 1: AST Parsing

```mermaid
flowchart LR
    A[Target Directory] --> B[File Collection]
    B --> C[AST Parsing]
    C --> D[Visitor Pattern]
    D --> E[ModuleMetadata]

    C -.->|SyntaxError| F[Log & Skip]
```

**Key decisions:**
- Uses Python's native `ast` module for zero-dependency parsing
- Custom `ModuleVisitor` extracts only structural metadata
- Gracefully skips unparseable files with logged warnings
- Cache layer avoids re-parsing unchanged files

## Stage 2: Dependency Graph

```mermaid
flowchart LR
    A[ModuleMetadata list] --> B[Build DiGraph]
    B --> C{Has Cycles?}
    C -->|No| D[Topological Sort]
    C -->|Yes| E[SCC Condensation]
    E --> F[Approximate Order]
```

**Key decisions:**
- NetworkX DiGraph maps importer → imported relationships
- Only internal imports become edges (external deps ignored)
- Cycle-aware sorting via Strongly Connected Component condensation
- Graph metrics (density, centrality) inform the script generation

## Stage 3: Script Generation

```mermaid
flowchart LR
    A[Module + Context] --> B[Analyzer Node]
    B --> C[Technical Summary]
    C --> D[Scriptwriter Node]
    D --> E[Podcast Segment]

    B -.->|LLM Failure| F[Fallback Summary]
    D -.->|LLM Failure| G[Use Tech Summary]
```

**Key decisions:**
- LangGraph state machine with two nodes
- Each node has independent fallback logic
- Compiled once, invoked per-module
- Results cached by content hash

## Stage 4: Audio Synthesis

```mermaid
flowchart LR
    A[Script Chunks] --> B[Semaphore-bounded Tasks]
    B --> C[TTS Backend]
    C --> D[.mp3 Chunks]
    D --> E[FFmpeg Concat]
    E --> F[walkthrough.mp3]

    C -.->|Rate Limit| G[Exponential Backoff]
    C -.->|Failure| H[Log & Skip Chunk]
```

**Key decisions:**
- asyncio with semaphore for bounded concurrency
- Exponential backoff with jitter for rate limit handling
- Pluggable backends via abstract base class
- FFmpeg concat demuxer for lossless stitching
