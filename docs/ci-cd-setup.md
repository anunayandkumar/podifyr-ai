# CI/CD Setup Guide

This document is a one-time checklist for wiring the repository to the
enterprise-grade pipeline that lives under `.github/`.

> Do this **once** as a repository admin. After it's done, day-to-day releases
> are: merge to `main` → push a `vYYYY.MM.DD` tag → done.

## 1. Branch protection (`main`)

`Settings → Branches → Add rule` for `main`:

- ✅ Require a pull request before merging
- ✅ Require approvals: **1** (or more)
- ✅ Dismiss stale approvals on new commits
- ✅ Require review from Code Owners
- ✅ Require status checks to pass before merging
  - **Required check:** `CI success` (the aggregate job in `ci.yml`)
  - Recommended additional checks: `Analyze (python)`, `Analyze (actions)`
- ✅ Require branches to be up to date before merging
- ✅ Require signed commits (optional but recommended)
- ✅ Require linear history
- ✅ Do not allow bypassing the above
- ✅ Restrict pushes that create matching branches

## 2. GitHub Environments

`Settings → Environments` — create two environments. Both are referenced by
`release.yml`.

### `testpypi`
- No required reviewers (auto-promote)
- Deployment branches: `Selected branches → main` and tag pattern `v*`

### `pypi`
- ✅ **Required reviewers:** at least one maintainer
- ✅ Wait timer: 0 (or a small delay if you want a cooling-off period)
- Deployment branches: tag pattern `v*` only

## 3. PyPI Trusted Publishing (OIDC — no tokens!)

This is the modern, secure way to publish. **No API tokens are stored anywhere.**

### TestPyPI
1. Create an account / project owner role at https://test.pypi.org/
2. Reserve the project name `podifyr-ai` (publish a `0.0.0.dev0` placeholder once if needed)
3. Project page → `Publishing` → `Add a new pending publisher`:
   - **PyPI Project Name:** `podifyr-ai`
   - **Owner:** `anunayandkumar`
   - **Repository name:** `podifyr-ai`
   - **Workflow name:** `release.yml`
   - **Environment name:** `testpypi`

### PyPI
Repeat the same steps at https://pypi.org/ with:
- **Environment name:** `pypi`

After this is configured, the release workflow can authenticate via OIDC and
needs **no `PYPI_API_TOKEN` secret**.

## 4. GitHub Pages (docs site)

`Settings → Pages`:
- **Source:** GitHub Actions

The `docs.yml` workflow will publish on every push to `main` that touches docs.

## 5. Optional secrets

Add under `Settings → Secrets and variables → Actions`:

| Secret           | Required? | Used by      | Purpose                              |
| ---------------- | --------- | ------------ | ------------------------------------ |
| `CODECOV_TOKEN`  | optional  | `ci.yml`     | Private repos need this; public repos work without it. |

That's the only optional secret — everything else uses OIDC.

## 6. Enable Dependabot security updates

`Settings → Code security and analysis`:
- ✅ Dependabot alerts
- ✅ Dependabot security updates
- ✅ Dependabot version updates (already configured via `.github/dependabot.yml`)
- ✅ CodeQL analysis (already configured via `.github/workflows/codeql.yml`)
- ✅ Secret scanning + push protection

## 7. (Optional) OSSF Scorecard public badge

After the first `scorecard.yml` run, your score appears at:
https://securityscorecards.dev/viewer/?uri=github.com/anunayandkumar/podifyr-ai

Add the badge to your `README.md` if you like.

---

## How to cut a release

After the one-time setup above:

```bash
# 1. Make sure main is green and CHANGELOG.md has an Unreleased section.
git switch main && git pull

# 2. Tag with today's CalVer.
TAG="v$(date -u +%Y.%m.%d)"
git tag -s "$TAG" -m "Release $TAG"
git push origin "$TAG"
```

That tag push triggers `release.yml`, which:
1. Re-runs the full quality gate.
2. Builds wheel + sdist.
3. Publishes to **TestPyPI** (OIDC).
4. Installs from TestPyPI on a clean runner and runs `podifyr-ai --version` / `--help`.
5. Publishes to **PyPI** (OIDC, requires environment approval).
6. Signs the artifacts with Sigstore and attaches them to a GitHub Release.

Need to ship something urgent without TestPyPI staging? Use **Actions →
Release → Run workflow** with `skip-testpypi: true`. The `pypi` environment's
required reviewer will still gate the push.
