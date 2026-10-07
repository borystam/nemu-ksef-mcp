# Working on Nemu KSeF MCP

This is an explicitly attributed AGPL-3.0-only derivative of
Dev10x-Guru/ksef-mcp at d47766b0ab533cc23cb0cbe141a82b5c6774e7e8.
Preserve upstream copyright, license and third-party notices.

For this fork, English is the primary language for new documentation,
communication and code. Existing Polish user messages may remain. The upstream
CLAUDE.md describes the original project's conventions; this file supersedes its
branding, publishing, issue-link and language conventions for this fork.

Deliver a working read-only collector. Keep invoice issuance, payments, tax
decisions and household finance outside its scope. Never publish real credentials,
invoices, taxpayer details or private research. Tests use synthetic fixtures and
must not reach KSeF. Do not run live tests without a separately bounded request.

Keep deterministic collection and recovery inside the service, not in agent
prompts. Preserve exact amounts, currencies, original evidence and explicit
coverage/freshness. Do not claim live validation from mocked tests.

Run applicable tests, lint and packaging checks. Preserve existing test coverage;
add meaningful regression tests for changed reliability behavior. Use codex/
branches. Do not open upstream issues or send messages without user authorization.

Every 30 minutes of active work, obtain three fresh independent reviews from a
pragmatic product owner, skeptical reliability engineer and first-time operator.
Record their evidence-based verdicts, accepted/deferred advice and next testable
outcome in PROJECT_STATUS.md. Stop expanding scope when the agreed release works.
