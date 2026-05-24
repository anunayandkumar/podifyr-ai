# Changelog

All notable changes to this project will be documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[CalVer](https://calver.org/) (`YYYY.M.D[.N]`).

## [Unreleased]

### Added
- **True multi-speaker podcast dialogue.** New `Dialogue` LangGraph node generates a Host ↔ Expert conversation as a JSON turn list, replacing the previous single-narrator monologue as the default style.
- Per-turn TTS synthesis with distinct voices for the Host and Expert (`--host-voice`, `--expert-voice`).
- New `--style {dialogue|monologue}` CLI flag (defaults to `dialogue`); `--style monologue` preserves the original single-voice behavior.
- `TTSConfig.style`, `TTSConfig.host_voice`, `TTSConfig.expert_voice` settings.
- `podifyr.agents.generate_dialogue_for_module()` and `podifyr.audio.generate_dialogue_audio_chunks()` public APIs.
- `DialogueTurn` type and `DIALOGUE_SYSTEM_PROMPT`.
- 6 new unit tests covering JSON parsing, code-fence stripping, speaker normalization, and fallback paths.

### Changed
- `ScriptState` is now `total=False` and includes a `dialogue` field alongside the legacy `conversational_script`.
- Saved `script.md` for dialogue runs is rendered as a speaker-tagged transcript (`**Host:** ...` / `**Expert:** ...`).
- README and CLI help text updated to document the new dialogue-first behavior.

## [2026.5.24.1] - 2026-05-24

Removed `.env` / `pydantic-settings` / `python-dotenv`. Unified LLM provider interface with `--provider {openai|azure|ollama}`. Added Ollama support via `langchain-ollama`.
