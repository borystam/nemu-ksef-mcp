# Initial release validation

Validation on 7 October 2026. This record describes executed synthetic checks,
not a live KSeF account certification.

## Behavior checked

- Real MCP client calls into the collection service with only the KSeF port
  scripted: 160 independently enumerated synthetic XML identities, overlapping
  seller/buyer delivery, original-byte/digest checks, exact counts, full audit
  records, bounded 50-ID previews and duplicate delivery without file rewrites.
- Accepted export followed by polling failure, then a new synchronizer/store:
  durable reference/key reuse for all four roles, without a second export.
- Selected historical start, bounded windows, night scheduling and rejection of
  invalid dates or attempts to reset established synchronization state.
- Late-arriving metadata after cache expiry, explicit refresh, and failure without
  a stale fallback when the refresh is rate limited.
- Corrupt indexed/unindexed evidence, missing retained bodies, intentional purge,
  interrupted purge, identity conflicts, duplicate entries and legacy ambiguity.
- Headless onboarding/doctor with a synthetic environment token and no keyring
  access, TEST defaults, explicit optional connection checks and truthful failed
  client registration.
- Signed-URL errors, formula-leading CSV text, offline status and expected tool
  surface. Taxpayer/environment isolation and existing rate-limit checks remain
  covered by the retained upstream suite.

The final local suite passed **1,494 tests**, with **14 live tests deselected**,
and 100% statement and branch coverage (3,939 statements, 508 branches).
The full default suite ran locally with macOS `sandbox-exec` denying network
access and uv offline mode after build dependencies were cached. A preceding
packaging-fixture run needed its build cache refreshed; no KSeF request occurred.
The suite also rejects Python IPv4/IPv6 TCP connections by default.
Explicitly marked live tests are excluded. Required statement/branch coverage
remains 100%; it is a regression gate, not a claim of overall correctness.

## Distribution and protocol

Both sdist and wheel built successfully. The wheel was installed in a new virtual
environment, separate from the editable development installation. The following
check ran under OS-level network denial, with no token and temporary diagnostic
output, using the installed executable:

```sh
uv build
uv venv .tmp/installed
uv pip install --python .tmp/installed/bin/python dist/*.whl
uv run python bin/smoke_stdio.py --server .tmp/installed/bin/nemu-ksef-mcp
```

The child process answered `server_info` with name `nemu-ksef-mcp`, version
`0.1.0`, and listed exactly seven expected tools. The installed `--help` command
also succeeded. These checks exercise real stdio startup/discovery, not a fake
MCP transport. They do not authenticate, call invoice tools or validate Hermes's
configuration interface.

Ruff lint/format and all three import-layer contracts pass. `pip-audit` found no
known vulnerabilities in the locked dependency set after PyJWT was updated to
2.15.1. This is a dated advisory check, not a general security guarantee. A fresh
wheel installation can resolve newer compatible transitive dependencies than
the development lock; its smoke test has a narrower scope than the locked suite.

GitHub CI repeats tests, checks, dependency auditing, build and installed-wheel
stdio on Linux. Consult the release commit's Actions result for remote status.

## Not established

No live KSeF authentication, complete taxpayer month, production performance,
Hermes deployment or smaller-model evaluation was performed for this release.
There is no comparative performance claim. The next milestone is an explicitly
bounded TEST flow followed by a read-only month checked against an independent
invoice inventory.
