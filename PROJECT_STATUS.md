# Nemu KSeF MCP status

Started 2026-10-07 10:57 UTC. First council due around 11:27 UTC.

Goal: publish a usable, clearly attributed read-only KSeF MCP on the owner's
personal GitHub. Harden the audited upstream collector and keep financial policy
outside the connector. No real credentials or invoice data enter this repository.

Current acceptance outcome: installed MCP starts and lists tools; synthetic
collection preserves original evidence and exact identities, resumes an accepted
export after polling failure, refreshes late invoices, repairs damaged retained
files, and returns bounded sync results. Run the upstream suite plus regressions,
lint, build and clean-install checks before publishing.

Live KSeF authentication and account completeness are not yet validated. Publishing
software does not activate a connection to a taxpayer account.

## Independent council — 2026-10-07 11:22 UTC

Three fresh advisors reviewed actual source, diffs, documentation and saved test
results independently; they did not rerun the full suite.

- Product owner: useful alpha is ready after installed-package verification; stop
  expanding features. Ensure the validation document and exact release tag exist.
- Reliability engineer: inspected recovery/archive/status changes support the
  bounded claims. Clarify that initial_from protects saved sync state, not all
  possible archive directories. Preserve live-validation limits.
- First-time operator: found headless onboarding contradicted the environment-token
  instructions and registration could falsely report success. Fix both before
  publishing. The generic stdio definition is not a tested Hermes integration.

Accepted: the two setup fixes, precise state wording, completed validation record,
exact public tag, and separate installed-wheel protocol check. Deferred: broader
translation, architecture expansion and inherited documentation cleanup, because
none improves the initial collection outcome enough to delay this release.

Next testable outcome: headless setup with a synthetic environment token succeeds
without keyring access or a secret prompt; the final public pinned checkout
installs and lists its seven tools, with Linux CI checked.

## Release candidate — 2026-10-07 11:28 UTC

Both operator blockers are fixed and regression-tested. Final local validation:
1,494 tests passed, 14 live tests deselected, 100% statement/branch coverage under
OS network denial with cached build dependencies and uv offline mode. Ruff,
formatting and three import contracts pass. Locked dependency audit reports no
known vulnerabilities. Rebuilt wheel installed separately; real stdio discovery
and server_info pass for seven tools. No account credentials or documents used.

Public fork: https://github.com/borystam/nemu-ksef-mcp. The implementation is
pushed. Linux CI passed tests, lint, dependency audit, build and installed-wheel
stdio on implementation commit 5e189af13bcce563ae7be333a5df44d1c19fa27c:
https://github.com/borystam/nemu-ksef-mcp/actions/runs/37614401617

Release packaging: nemu-v0.1.0, AGPL-3.0-only, source and wheel. This final status
update changes documentation only. The next product milestone is an explicitly
bounded TEST/account pilot; no service connection or financial close was performed.
