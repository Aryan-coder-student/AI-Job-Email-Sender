# Security Policy

## Supported versions

Job Send Crawl is currently in pre-1.0 development. Security fixes are applied to the latest code on the default branch and, when appropriate, the latest published release.

| Version | Supported |
| --- | --- |
| latest `main` | Yes |
| latest release | Yes |
| older releases | No guarantee |

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a vulnerability that could expose credentials, personal data, email accounts, third-party services, or system access.

Use GitHub's private vulnerability reporting flow from the repository's **Security** tab when it is available.

If private vulnerability reporting is not available, open a minimal public issue stating only that you need a private security contact. Do not include exploit details, secrets, personal data, tokens, or reproduction material in that issue.

When reporting privately, include:

- the affected component;
- impact and attack scenario;
- reproduction steps or proof of concept;
- affected configuration or version;
- suggested mitigation, if known.

Please allow the maintainer a reasonable opportunity to investigate and fix the issue before public disclosure.

## Sensitive data

Never include real API keys, GitHub tokens, SMTP credentials, resumes, recipient lists, generated email artifacts, or other personal data in bug reports, pull requests, screenshots, or test fixtures.

Use synthetic data and redact secrets from logs.

## Scope

Security reports may include issues involving:

- authentication or authorization;
- secret exposure;
- unsafe handling of uploaded resumes or company files;
- email-sending abuse or recipient leakage;
- SSRF, injection, path traversal, or unsafe file handling;
- vulnerable dependency or container configurations;
- exposure of Redis, Neo4j, Qdrant, FastAPI, or other services;
- prompt/tool behavior that can cause unintended privileged actions or data disclosure.

General bugs and feature requests should use the normal issue templates.
