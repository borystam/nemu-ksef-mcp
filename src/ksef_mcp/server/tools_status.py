"""Bounded local operational status without credentials or registry requests."""

from ksef_mcp.clock import now_utc
from ksef_mcp.ksef_port.types import SubjectRole
from ksef_mcp.server.app import reported, server
from ksef_mcp.server.context import SubjectDependencies, configured_subject
from ksef_mcp.server.results import SubjectRoleStatus, SynchronisationStatus
from ksef_mcp.storage.audit import AuditedOperation, AuditEntry, Disclosure


@server.tool()
def synchronisation_status() -> SynchronisationStatus:
    """Inspect local sync state without authenticating or contacting KSeF.

    pending means call synchronise_invoices without initial_from to resume.
    idle means no export is queued, NOT that a month is complete or current.
    Cursors can coexist with unarchived pending work; never infer coverage from
    a cursor alone. Counts include deliberately purged identities, not just files.
    """
    with reported(AuditedOperation.STATUS) as journal:
        subject = SubjectDependencies(configuration=configured_subject())
        store = subject.sync_store
        with store.exclusively():
            state = store.load()
            identities = len(subject.archive.load_index().entries)
        observed = now_utc()
        status = "pending" if state.pending else "idle" if state.subject_roles else "not_started"
        rows = []
        for role in SubjectRole:
            position = state.subject_roles.get(role)
            rows.append(
                SubjectRoleStatus(
                    subject_role=str(role),
                    cursor=None if position is None else position.reached.isoformat(),
                    last_attempt_at=(
                        None
                        if position is None or position.attempted_at is None
                        else position.attempted_at.isoformat()
                    ),
                    pending=state.pending_for(role) is not None,
                )
            )
        journal.record(
            trail=subject.trail,
            entries=(
                AuditEntry(
                    recorded_at=observed,
                    operation=AuditedOperation.STATUS,
                    authorisation=subject.archive_authorisation(),
                    disclosure=Disclosure.MODEL_CONTEXT,
                    subject_role=None,
                    criteria="local sync status and aggregate counts",
                    document_count=0,
                    ksef_numbers=(),
                    output_path=None,
                    formats=(),
                ),
            ),
        )
        return SynchronisationStatus(
            nip=subject.nip,
            environment=str(subject.environment),
            message="Local operational snapshot; no KSeF request was made.",
            warnings=[
                "Idle state and cursor positions do not certify complete or fresh month coverage."
            ],
            state=status,
            observed_at=observed.isoformat(),
            archived_identity_count=identities,
            pending_export_count=len(state.pending),
            subject_roles=rows,
            state_file=str(store.path),
            next_action=(
                "Call synchronise_invoices; choose initial_from only for the first run."
                if status == "not_started"
                else "Call synchronise_invoices without initial_from to resume or refresh when due."
            ),
        )
