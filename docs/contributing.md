# Contributing

We welcome contributions! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/anunayandkumar/podifyr-ai.git
cd podifyr-ai
make dev
```

This installs the package in editable mode with all dev dependencies and configures pre-commit hooks.

## Development Workflow

```bash
# Run linter
make lint

# Auto-format
make format

# Type checking
make typecheck

# Run tests
make test

# Run fast unit tests only
make test-fast

# Full pre-release check
make release-check
```

## Code Standards

- **Type hints**: All functions must have PEP 484 type annotations
- **Docstrings**: Google style docstrings on all public functions
- **Testing**: Maintain >80% code coverage
- **Linting**: Must pass ruff and mypy strict mode
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes with tests
4. Run `make release-check`
5. Submit a PR against `main`

## Architecture Guidelines

- Keep modules focused (single responsibility)
- Use protocols for dependency inversion
- Handle errors at module boundaries, not internally
- Cache expensive operations by content hash
- Log structured events, not strings
