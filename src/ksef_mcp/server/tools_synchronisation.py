"""Fetching, decrypting and archiving whatever KSeF finished since the last pass."""

from datetime import datetime

from ksef_mcp.diagnostics import correlation
from ksef_mcp.invoices.synchronisation import (
    SynchronisationReport,
    Synchroniser,
    synchronisation_entries,
)
from ksef_mcp.ksef_port.types import KsefEnvironment
from ksef_mcp.server.app import Journal, reported, server
from ksef_mcp.server.context import authenticated_dependencies
from ksef_mcp.server.results import (
    SessionCeilingsResult,
    SubjectRoleResult,
    SynchronisationResult,
)
from ksef_mcp.storage.audit import AuditedOperation

IDENTIFIER_LIMIT = 50


def describe_synchronisation(report: SynchronisationReport) -> str:
    """One sentence over all subject types, so the whole pass reads at a glance.

    Counts only — the numbers themselves are already per subject type below, and
    repeating them here would put a counterparty's NIP in the answer twice
    (D-011, D-038).
    """
    archived = sum(len(reported.archived) for reported in report.subject_roles)
    already_held = sum(len(reported.already_held) for reported in report.subject_roles)
    return (
        f"Zarchiwizowane faktury: {archived}. Już na dysku: {already_held}. "
        f"Co zrobiła każda rola podmiotu z osobna — w `subject_roles`."
    )


def describe(
    report: SynchronisationReport,
    *,
    nip: str,
    environment: KsefEnvironment,
) -> SynchronisationResult:
    return SynchronisationResult(
        nip=nip,
        environment=str(environment),
        message=describe_synchronisation(report),
        subject_roles=[
            SubjectRoleResult(
                subject_role=str(reported.subject_role),
                outcome=str(reported.outcome),
                message=reported.message,
                invoice_count=reported.invoice_count,
                part_count=reported.part_count,
                synchronised_up_to=(
                    None if reported.reached is None else reported.reached.isoformat()
                ),
                archived=list(reported.archived[:IDENTIFIER_LIMIT]),
                already_held=list(reported.already_held[:IDENTIFIER_LIMIT]),
                archive_directory=reported.archive_directory,
                archived_count=len(reported.archived),
                already_held_count=len(reported.already_held),
                identifiers_truncated=(
                    len(reported.archived) > IDENTIFIER_LIMIT
                    or len(reported.already_held) > IDENTIFIER_LIMIT
                ),
            )
            for reported in report.subject_roles
        ],
        pending_exports=list(report.pending_exports),
        state_file=report.state_path,
        session_ceilings=SessionCeilingsResult(
            assumed=report.ceilings.assumed,
            message=report.ceilings.message,
            max_invoice_megabytes=report.ceilings.max_invoice_megabytes,
            max_invoice_with_attachment_megabytes=(
                report.ceilings.max_invoice_with_attachment_megabytes
            ),
            max_invoices_per_session=report.ceilings.max_invoices_per_session,
        ),
        correlation=correlation(),
    )


def synchronise(*, journal: Journal, initial_from: datetime | None = None) -> SynchronisationResult:
    subject, stored = authenticated_dependencies()
    synchroniser = Synchroniser(
        port=subject.port,
        store=subject.sync_store,
        allowance=subject.allowance,
        initial_from=initial_from,
    )
    report = synchroniser.run(nip=subject.nip, token=stored)
    trail = subject.trail
    journal.record(
        trail=trail,
        entries=synchronisation_entries(
            report,
            authorisation=subject.authorisation(stored),
            moment=trail.clock(),
        ),
    )
    return describe(report, nip=subject.nip, environment=subject.environment)


@server.tool()
def synchronise_invoices(initial_from: datetime | None = None) -> SynchronisationResult:
    """Fetch, decrypt and archive every invoice package KSeF finished since the last run.

    On the FIRST run only, initial_from selects an earlier history start as an
    ISO timestamp with timezone, for example 2026-01-01T00:00:00Z. Omit it on
    every later call to resume existing state. It cannot rewind saved synchronisation state.
    Export windows, package sizes and rate budgets remain service-controlled.

    Safe to call again. A package still being built, or one fetched but not yet
    stored, stays recorded on disk with its key, so a second call continues it
    instead of asking for it twice. An invoice already in the archive is
    reported under `already_held` rather than downloaded again.

    Reports exact counts and up to 50 archived/already-held identifiers per role.
    identifiers_truncated explicitly marks shortened previews; all documents
    remain in the archive and full identifiers in its index/audit. It never
    returns invoice content: an FA(2)/FA(3) document holds a counterparty's
    personal data, and reading one means opening the file this tool names.

    `session_ceilings` says how much one session may carry and, in `assumed`,
    whether KSeF granted those figures or the conservative fallback is in force
    because the registry answered about limits in a shape that could not be
    read. An assumed ceiling is a different event from a granted one, and the
    message says so in as many words.

    `correlation` names this call in the technical journal on stderr. Quote it
    when reporting a failure: it is what lets the whole pass be reconstructed
    without running the synchronisation again out of twenty exports an hour.
    """
    with reported(AuditedOperation.SYNCHRONISATION) as journal:
        return synchronise(journal=journal, initial_from=initial_from)
