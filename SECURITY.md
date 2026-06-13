# Security Policy

## Supported versions

We support the **latest released minor version** of `podifyr-ai` on PyPI.
Security fixes are released as patch versions on top of the latest minor.

| Version              | Supported |
| -------------------- | --------- |
| Latest release       | ✅        |
| Previous minor       | ✅ (critical fixes only) |
| Older versions       | ❌        |

## Reporting a vulnerability

**Please do not open a public issue, discussion, or PR for security problems.**

Instead, report vulnerabilities privately via GitHub's coordinated disclosure
channel:

👉 https://github.com/anunayandkumar/podifyr-ai/security/advisories/new

When reporting, please include:

- A clear description of the issue and its potential impact
- A minimal reproducer (code, command, repo snippet, payload, etc.)
- The version of `podifyr-ai`, Python, and OS you used
- Any suggested mitigation, if you have one

### What to expect

- **Acknowledgement:** within 3 business days
- **Initial assessment:** within 7 business days
- **Fix or mitigation plan:** communicated as soon as triage completes
- **Coordinated disclosure:** we will agree on a disclosure timeline with you
  and credit you in the release notes and CVE (if applicable) unless you
  prefer to remain anonymous.

## Supply-chain security

Releases of `podifyr-ai` are:

- Built in clean GitHub Actions runners from a pinned `release.yml` workflow
- Published to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC, no long-lived tokens)
- Signed with [Sigstore](https://www.sigstore.dev/) and attached to the GitHub Release
- Accompanied by a CycloneDX SBOM
- Container images are published to GHCR, signed with `cosign`, and scanned with Trivy
- Continuously scored by the [OpenSSF Scorecard](https://securityscorecards.dev/)

## Out of scope

- Vulnerabilities in third-party dependencies (please report upstream and let us know)
- Issues that require physical access to a user's machine
- Social engineering of project maintainers
