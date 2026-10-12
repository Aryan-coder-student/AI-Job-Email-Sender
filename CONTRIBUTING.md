# Contributing to Job Send Crawl

Thanks for your interest in contributing to Job Send Crawl.

The project welcomes bug fixes, documentation improvements, tests, frontend work, backend improvements, and focused enhancements to the matching and outreach workflow.

## Before you start

1. Check existing issues and pull requests to avoid duplicate work.
2. For non-trivial changes, comment on the issue before implementation so scope and approach can be aligned.
3. Keep pull requests focused. Avoid combining unrelated refactors, formatting changes, and features.
4. Never commit API keys, credentials, resumes, personal data, generated outreach data, or other secrets.

If you find a security vulnerability, follow [SECURITY.md](SECURITY.md) instead of opening a normal public issue.

## Development setup

The recommended development path is Docker Compose:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
```

The portal is available at `http://localhost:8080` and the FastAPI backend at `http://localhost:8000`.

For local backend/frontend development, follow the setup instructions in [README.md](README.md).

## Branches

Create a descriptive branch from the latest `main`, for example:

```text
fix/optional-max-rows
feat/low-fit-suppression
docs/contributor-guide
test/matching-regression
```

Do not work directly on `main`.

## Tests

Run the checks relevant to your change before opening a pull request.

### Backend

```bash
python -m pytest tests -q --import-mode=importlib
```

### Frontend

```bash
cd frontend
npm ci
npm test
npm run build
npm run lint
```

### Docker

For changes that affect runtime packaging or service configuration:

```bash
docker compose config --quiet
docker compose build
```

Use dry-run mode when testing email workflows. Do not send generated email to real recipients while validating a contribution.

## Pull request expectations

A good pull request should:

- solve one clear problem;
- link the related issue when one exists;
- explain the behavior before and after the change;
- include tests for bug fixes and behavior changes where practical;
- include screenshots for meaningful UI changes;
- update documentation when configuration or user-facing behavior changes;
- keep secrets, personal data, and generated user artifacts out of the repository.

If the PR fully resolves an issue, use GitHub closing syntax such as `Closes #123`.

## Code style

Follow the patterns already used in the surrounding code.

For Python changes, keep implementation readable and testable and avoid unnecessary abstraction.

For React/TypeScript changes, keep API types and validation consistent with the existing frontend structure. Prefer accessible controls and preserve the current run-based workflow.

## Commit messages

Use short, descriptive commit messages. Conventional prefixes are encouraged:

```text
fix: allow empty optional row limit
feat: suppress low-confidence matches
docs: improve Docker setup
test: cover draft queue behavior
chore: update contributor tooling
```

## Reporting bugs

Use the bug report form and include:

- exact reproduction steps;
- expected and actual behavior;
- relevant logs with secrets removed;
- environment details;
- screenshots when they clarify a UI problem.

Please reduce examples to the minimum data needed to reproduce the issue.

## Proposing features

Use the feature request form and explain the problem first. Include the proposed behavior, alternatives considered, and which part of the system is affected.

## Review

Maintainers may request changes before merging. Keep review discussions focused on the contribution and resolve requested changes with follow-up commits.

By submitting a contribution, you agree that your contribution is licensed under the repository's Apache License 2.0.
