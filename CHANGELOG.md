# Changelog

All notable changes to Job Send Crawl are documented here.

## [0.1.0] - 2026-10-12

### Initial open-source release

Job Send Crawl is an AI-assisted job outreach pipeline that connects a candidate's resume and GitHub projects with company/job data before generating personalized application emails.

### Added

- End-to-end pipeline for resume parsing, GitHub project analysis, company import, matching, draft generation, and mail processing.
- React + TypeScript portal for creating runs and reviewing pipeline output.
- FastAPI backend with run, artifact, company preview, draft, mail, and system-status APIs.
- Neo4j knowledge graph for candidate, project, technology, capability, company, role, and job relationships.
- Qdrant vector search for project/job similarity.
- Hybrid project-company ranking using graph, embedding, and LLM scores.
- Provider-aware LLM routing across configured Groq, OpenAI, and Gemini providers.
- Redis-backed mail queue and rate limiting.
- CSV, JSON, Excel, and Google Sheets company import preview workflow.
- Draft review and safe dry-run mail processing from the portal.
- Docker Compose setup for frontend, backend, Redis, Neo4j, and Qdrant.
- Local service documentation and step-by-step portal usage guide.
- Backend and frontend automated test coverage and Docker image CI.

### Known limitations

- The portal workflow is still being refined and has open issues for UX and flow edge cases.
- Low-fit project-company matches need stronger automatic suppression before draft generation.
- Draft editing and some advanced configuration options still need richer frontend support.
- Real email delivery should only be enabled after validating provider credentials, recipients, and generated drafts.

### Release status

This is the first public development release. Use dry-run mode while evaluating the project and report reproducible problems through GitHub Issues.
