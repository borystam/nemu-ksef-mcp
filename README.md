# Nemu KSeF MCP

Read-only access to Poland's KSeF for local agents. Collect issued and received
invoices, preserve original XML, resume interrupted exports, and return compact
results without making an agent implement pagination or recovery.

**Alpha software.** Synthetic integration tests exercise collection and recovery;
this fork has not yet been validated against a real taxpayer account. An idle
queue does not certify that a financial month is complete. It never issues
invoices, initiates payments or calculates tax/VAT entitlement.

This is an **AGPL-3.0-only fork** of
[Dev10x-Guru/ksef-mcp](https://github.com/Dev10x-Guru/ksef-mcp), based on commit
`d47766b0ab533cc23cb0cbe141a82b5c6774e7e8`. The upstream project supplies the
collection engine, SDK adapter, archive, rate budgets, renderer and much of the
test suite. [Attribution and changes](NOTICE.md).

## What this fork changes

- Accepted export references and encryption keys are saved **before** polling.
  Restart resumes the same export after a polling failure.
- First-run historical backfill accepts an explicit start timestamp; individual
  export windows and request budgets remain controlled by the service.
- Monthly metadata caches expire after 15 minutes. An expired query that cannot
  refresh fails visibly instead of silently reusing a stale complete result.
- Archive replay verifies retained bytes and repairs damage from verified export
  content. Explicit deletion records preserve intentional retention decisions.
- Sync replies contain exact counts and at most 50 identifiers per list/role.
  Full evidence remains in the local archive and audit trail.
- Local `synchronisation_status` works without a token or registry request.
- Spreadsheet exports neutralize formula-leading counterparty text; package
  errors omit signed download URLs; the locked PyJWT dependency is updated.

## Install

Use macOS or Linux, Git and a current [uv](https://docs.astral.sh/uv/) release.
`uv` installs the pinned Python runtime. Native Windows is not supported; use WSL.
Node is needed only for optional PDF rendering (the repository pins its version).

```sh
git clone https://github.com/borystam/nemu-ksef-mcp.git
cd nemu-ksef-mcp
git checkout nemu-v0.1.0
uv sync --frozen --no-dev
uv run --frozen --no-dev nemu-ksef-mcp --help
uv run --frozen --no-dev nemu-ksef-mcp onboarding
uv run --frozen --no-dev nemu-ksef-mcp doctor
```

Onboarding asks for the taxpayer, environment, credential store and output
directory. TEST is the default. Select production deliberately only when ready.
Use a dedicated KSeF token with invoice-read permission. Never put a token in an
agent prompt or committed config. Desktop setups use the OS keyring; headless
setups can inject `KSEF_TOKEN` from their protected service environment. The
onboarding flow recognizes this fallback. The taxpayer/environment still come
from the configuration file, not a guessed environment variable.

`doctor` checks local setup. `verify` and invoice retrieval tools contact KSeF
and consume its request budget. Optional client registration during onboarding
points to this installed Python environment; keep that environment in place.
Many inherited prompts remain Polish. `ksef-mcp` remains a compatibility alias.

## Connect an MCP client, including Hermes

Start this server over **stdio**, using the installed checkout's absolute path:

```json
{
  "mcpServers": {
    "nemu-ksef": {
      "command": "/absolute/path/to/nemu-ksef-mcp/.venv/bin/nemu-ksef-mcp",
      "args": []
    }
  }
}
```

Supply secrets through the process environment or keyring, outside this JSON.
This is the server definition; the location of the enclosing MCP configuration
depends on the client. No HTTP listener or public proxy is provided.

| Tool | Purpose | Contacts KSeF? |
|---|---|---|
| `server_info` | Installed identity/version | No |
| `synchronisation_status` | Cursors, queue state, counts and next action | No |
| `synchronise_invoices` | Resume or collect encrypted export packages | Yes |
| `list_recent_invoices` | Metadata from the recent 30-day period | On refresh/cache miss; authentication may also contact KSeF |
| `export_period_statement` | Purchase-invoice CSV for `period: "YYYY-MM"` | On refresh/cache miss; authentication may also contact KSeF |
| `review_new_invoices` | Review newly observed invoice metadata | On refresh/cache miss; authentication may also contact KSeF |
| `render_invoice_pdf` | Render an archived invoice with the bundled MF renderer | No |

For an initial backfill, call:

```json
{"initial_from": "2026-01-01T00:00:00Z"}
```

on `synchronise_invoices`. **Omit `initial_from` on every subsequent call.** It
cannot rewind saved synchronisation state. Without it, first-run history begins 89 days
back. Seller/buyer roles run when due; less common third/authorized-party roles
have a night schedule. A pending export or budget refusal requires a later
resume, not rapid repeated calls. No scheduler is installed automatically.

Read `pending_exports`, each role's outcome and synchronization position. A
cursor may advance while recoverable archive work is still pending. An `idle`
status means the queue is empty, not that all dates were reconciled. Metadata
`complete` describes the query at `queried_at`; it is not a permanent statement
that no late invoice can arrive. Verify IDs and original evidence against an
independent complete month before using this for financial close.

## Local data and upgrades

State uses platform data/cache directories under **`nemu-ksef-mcp`**, separated
by taxpayer and environment. It does not automatically read upstream
`ksef-mcp` data. Keep these directories private. Pending sync state contains
export decryption keys; backups need the same protection as the archive.

Index schema 2 distinguishes retained and intentionally removed documents.
Upstream schema-1 entries with existing bodies can be verified and upgraded on
replay. An indexed but missing legacy body is ambiguous: restore verified backup
evidence or resolve its deletion history before continuing. Do not delete state
to silence an error or copy production state into TEST. See [security](SECURITY.md).

## Develop and verify

```sh
uv sync --frozen --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run lint-imports
uv build
```

The default suite blocks external TCP connections and excludes live KSeF tests.
It includes a 160-invoice synthetic collection/replay through the MCP interface,
plus late-arrival, restart, integrity and authority-boundary regressions. Do not
confuse mocked KSeF responses with live API validation. Full process installation
and protocol checks are described in [release validation](docs/VALIDATION.md).

The retained `docs/adr`, `references`, `site`, release tooling and upstream
README/development copies document the original project. Some describe earlier
behavior or upstream publishing. **This README and current source define this
fork.** Its CI does not run the inherited publishing or agent workflows.

The next integration milestone is a bounded TEST round trip and an independently
reconciled read-only account month. Bank matching, tax/ZUS/VAT rules and savings
goals belong in a separate finance application consuming this evidence.
