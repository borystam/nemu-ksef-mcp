# Why this collector exists

Comparison date: **7 October 2026**. Findings below concern the linked revisions
and their reviewed retrieval paths. Maintainers may have fixed them since. This
is a focused explanation of our design choices, not an exhaustive product ranking
or a comparative performance benchmark.

Nemu is an AGPL-3.0-only derivative of **Dev10x-Guru/ksef-mcp**, not an independent
replacement for all of its engineering. Its collection engine, SDK adapter,
original XML archive, rate budgets, Decimal amounts, currency grouping and much
of the test suite are inherited. Our contribution is bounded reliability fixes
and a simpler synchronization response for an agent consuming invoice evidence.

## Retrieval that the service owns

In [Ksefnik at `801bfd8`](https://github.com/CodeFormers-it/ksefnik/blob/801bfd8ee1ff8f046342e1becce5fc8f07c01bb9/packages/http/src/invoices.ts#L155-L177),
the next metadata offset advances by page size. KSeF defines `pageOffset` as a
[zero-based page index](https://github.com/CIRFMF/ksef-api/blob/c50f855ef3ae550396c6a272594047506e220498/open-api.json#L5591-L5614).
A synthetic 150-record source-level reproduction returned 100 records, requesting
offsets 0 and 100 instead of 0 and 1. The same behavior reproduced in npm 0.5.0.

In [mcp-ksef-pl at `c89cf73`](https://github.com/cmendezs/mcp-ksef-pl/blob/c89cf735c4f7fa2b4897c8184c73b975571abe27/src/mcp_ksef_pl/lifecycle.py#L397-L422),
search makes one query and returns its invoices without continuation information.
A synthetic 15-record reproduction returned the first 10. This retrieval path
also matched the published 0.10.1 wheel.

Nemu inherits service-managed metadata pagination and export continuation from
Dev10x. The agent does not implement those loops. Our
[metadata tests](../tests/storage/test_period_cache.py) check offsets `[0, 1]`,
continuation, budget interruption and refusal to cache partial windows;
[synchronization tests](../tests/invoices/test_synchronisation.py) exercise
truncated-export continuation. These are selected synthetic contracts, not proof
that every live boundary or taxpayer month is complete.

Ksefnik also offers bank parsers, matching and optional SQLite storage;
mcp-ksef-pl offers invoice-generation and validation workflows. Nemu does not
replace those capabilities. Their different product scope is not itself a defect.

## Recovery after an accepted export

[Dev10x at `d47766b`](https://github.com/Dev10x-Guru/ksef-mcp/blob/d47766b0ab533cc23cb0cbe141a82b5c6774e7e8/src/ksef_mcp/invoices/synchronisation.py#L476-L503)
constructed the pending export in memory, then polled before the next durable
save. A polling exception could lose the accepted reference and encryption key,
causing a later run to start another export. This establishes lost resumability
and extra API work, not permanent invoice loss.

**Nemu adds persistence before polling.** The regression
`test_poll_failure_keeps_accepted_export_and_restart_resumes_it_exactly_once`
in [the synchronization suite](../tests/invoices/test_synchronisation.py) reopens
the state store after failure and verifies reuse for all four subject roles.
The guarantee concerns an acceptance response we received and saved. It does not
solve the ambiguity of a network failure that hides the initial acceptance reply.

## Monthly results that can become fresh again

The reviewed Dev10x [cache and reader](https://github.com/Dev10x-Guru/ksef-mcp/blob/d47766b0ab533cc23cb0cbe141a82b5c6774e7e8/src/ksef_mcp/storage/period_cache.py#L305-L402)
had no expiry for remembered complete monthly results. `queried_at` and
`from_cache` were present, but a late invoice could remain absent on repeat reads.

**Nemu adds a 15-minute default expiry.** The
[cache regressions](../tests/storage/test_period_cache.py) check late arrivals and
rate-limited refresh without an expired fallback. Expiry triggers a fresh query
when the tool is next called; it is not a background scheduler. `complete` still
means complete for that query at its timestamp, not permanently closed books.

## An archive checked against retained bytes

The reviewed Dev10x [archive writer](https://github.com/Dev10x-Guru/ksef-mcp/blob/d47766b0ab533cc23cb0cbe141a82b5c6774e7e8/src/ksef_mcp/storage/archive.py#L530-L566)
could skip an existing file without verifying its contents. A synthetic damaged
file stayed damaged even when verified replacement bytes were available.

**Nemu verifies existing retained bodies during replay**, repairs them using
verified export content and records intentional removals separately. The
[archive regressions](../tests/storage/test_archive.py) cover corrupt/missing
bodies, conflicts, duplicate replay and retention. This is repair on verified
replay, not continuous disk scrubbing or an automatic backup service. Ambiguous
missing legacy bodies require explicit operator resolution.

## Compact replies without discarding collected evidence

The [p-zmud 0.1.0 bundle at `3749f42`](https://github.com/p-zmud/mcp-and-skills/blob/3749f42fddc8fc872d1ba9da3a9eae6d3a01dd01/mcp/ksef/ksef-mcp-0.1.0.mcpb)
clips query output to 50 rows while accepting a 100-row page. The relevant
delivered JavaScript is `core/output.js:99–103` and
`core/tools/pobieranie.js:27–54`. Our synthetic reproduction showed an explicit
omission notice, but following the next-page instruction skipped the other 50.
Requesting at most 50 rows is a workaround. The bundle also has useful read-only
scope enforcement and an HTTP/OAuth option that Nemu does not offer.

**Nemu's synchronization limit is a preview limit.** Exact counts accompany up
to 50 identifiers per list/role; the archive and audit trail retain the collected
evidence. The [MCP integration test](../tests/server/test_nemu_collection.py) uses 160
synthetic invoices with overlapping role delivery and checks original bytes,
digests, counts, bounded previews and duplicate replay. This tests our collection
workflow, not a head-to-head run of identical APIs across both products.

## What we can claim today

The [release validation record](VALIDATION.md) reports 1,494 passing tests,
installed-wheel stdio checks and Linux CI. Most of the suite is inherited;
test count and coverage are not comparative quality scores. The comparator
observations above used synthetic source/bundle probes rather than live accounts;
the original audit harnesses are not shipped in this repository.

Nemu is a useful alpha for evaluating recoverable local collection. Live KSeF
authentication, an independently reconciled account month, Hermes deployment,
smaller-model usability and production performance still need validation.
Read-only stdio keeps this product's authority narrow; it does not establish
greater overall security than every alternative. Tax/VAT entitlement, payment
matching and savings policy belong in the finance application above it.
