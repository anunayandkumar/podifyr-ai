# Contributing to Podifyr-AI

Thanks for your interest in contributing! This document covers the quickest
path from a fresh clone to a green PR. For deeper architecture notes see
[`docs/contributing.md`](docs/contributing.md) and the [architecture docs](docs/architecture/overview.md).

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
By participating you agree to uphold it — be respectful, be inclusive, assume
good faith.

## Getting set up

```bash
git clone https://github.com/anunayandkumar/podifyr-ai.git
cd podifyr-ai

# Editable install with everything you need to develop
pip install -e ".[dev,docs,all]"

# Install pre-commit hooks
pre-commit install --install-hooks
```

You will also need **FFmpeg** on your `PATH` for audio stitching tests.

## Day-to-day commands

All standard tasks are wrapped in the `Makefile`:

```bash
make lint        # ruff check
make format      # ruff format + auto-fix
make typecheck   # mypy --strict
make test        # full test suite
make test-fast   # unit tests only
make test-cov    # coverage report
make docs-serve  # preview docs locally
```

Before opening a PR, run:

```bash
make release-check   # lint + typecheck + test
```

## Branching & commits

- Branch from `main`; name branches `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- Commits should follow [Conventional Commits](https://www.conventionalcommits.org/)
  (e.g. `feat(audio): add piper TTS backend`). The release notes are generated
  from these.
- Keep PRs focused — one logical change per PR.

## Pull-request expectations

Every PR must:

1. Pass **all** required CI checks (lint, type check, tests, build).
2. Include tests for new behavior or regressions.
3. Update documentation when user-visible behavior changes.
4. Update `CHANGELOG.md` under an `## [Unreleased]` heading.
5. Be reviewed by a code owner (see `.github/CODEOWNERS`).

The PR template walks you through this checklist.

## Releasing (maintainers only)

1. Ensure `main` is green and the `Unreleased` section of `CHANGELOG.md` is up to date.
2. Tag the release: `git tag -s vYYYY.MM.DD -m "Release vYYYY.MM.DD" && git push origin vYYYY.MM.DD`
3. The `release.yml` workflow will:
   - Re-run the full quality gate
   - Build sdist + wheel
   - Publish to **TestPyPI** (OIDC, no tokens)
   - Smoke-test the install
   - Publish to **PyPI**
   - Sign artifacts with Sigstore and create the GitHub Release
4. Confirm the new version is live at https://pypi.org/project/podifyr-ai/

Need to push a hotfix without staging through TestPyPI? Use **Run workflow**
on the Release action with `skip-testpypi: true` (requires approval on the
`pypi` environment).

## Reporting security issues

See [`SECURITY.md`](SECURITY.md). Please do not file public issues for
vulnerabilities.

## License

By contributing you agree that your contributions will be licensed under the
[MIT License](LICENSE).
