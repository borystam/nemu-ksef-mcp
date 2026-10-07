# Security and operating boundary

This release is a local stdio MCP. Its registered tools provide invoice reads,
export retrieval, local reports and local review state. It exposes no invoice
issuance, payment, permission-management or arbitrary HTTP-request tool. A local
process running as the same OS user can access that user's files; stdio is not
multi-user authorization or a substitute for host isolation.

Use a dedicated KSeF invoice-read credential. Keep it in the OS keyring or inject
KSEF_TOKEN from a protected service environment. Never place it in a repository,
tool argument, issue, chat, log or example. InvoiceRead itself is not a guarantee
of zero side-effect capability in the remote API; this service's narrow method
surface supplies the additional boundary. Exports and authentication do create
operational state in KSeF, but do not issue invoices.

Configuration, taxpayer-scoped state and archive data belong in protected local
directories. Sync state contains export encryption keys while work is pending.
Protect backups, logs and generated CSV/PDF files too. MCP metadata becomes
visible to the selected model provider; running a collector locally alone does
not make a cloud model private. Counterparty text remains untrusted input.

Default tests use synthetic records and reject external TCP connections. Live
tests require explicit selection and their own TEST credentials. Never test a
write restriction by attempting to issue a production invoice.

The fork has not yet completed a live account pilot. An empty queue, complete
cached metadata query or passing coverage threshold does not establish an
accounting close. Inspect timestamps, pending work and source completeness.

For a potential vulnerability, use GitHub private vulnerability reporting if
enabled. Do not include real credentials or documents in public issues. Describe
the affected revision and a synthetic reproduction. There is no promised support
SLA for this alpha.
