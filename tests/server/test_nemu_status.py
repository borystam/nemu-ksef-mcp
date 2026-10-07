from datetime import UTC, datetime

import pytest
from mcp import Client

from ksef_mcp.config import Configuration
from ksef_mcp.ksef_port.types import ExportState, SubjectRole
from ksef_mcp.server import server
from ksef_mcp.server.context import SubjectDependencies
from ksef_mcp.storage import token_store
from ksef_mcp.storage.sync_store import PendingExport, SubjectRoleState, SyncState


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["not_started", "idle", "pending"])
async def test_status_is_local_bounded_and_does_not_claim_month_coverage(
    configured: Configuration, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Status must not authenticate or construct a remote port")

    monkeypatch.setattr(token_store, "read_token", forbidden)
    monkeypatch.setattr(SubjectDependencies, "port", property(forbidden))
    subject = SubjectDependencies(configuration=configured)
    moment = datetime(2026, 9, 1, tzinfo=UTC)
    if mode != "not_started":
        pending = PendingExport(
            reference="SYNTHETIC-EXPORT",
            subject_role=SubjectRole.BUYER,
            started_at=moment,
            encryption=None,
            state=ExportState.READY,
        )
        subject.sync_store.save(
            SyncState(
                subject_roles={
                    SubjectRole.BUYER: SubjectRoleState(reached=moment, attempted_at=moment),
                    SubjectRole.SELLER: SubjectRoleState(reached=moment),
                },
                pending=(pending,) if mode == "pending" else (),
            )
        )
    async with Client(server, raise_exceptions=True) as client:
        answer = await client.call_tool("synchronisation_status")
    result = answer.structured_content
    assert result["state"] == mode
    assert result["pending_export_count"] == (1 if mode == "pending" else 0)
    assert result["archived_identity_count"] == 0
    assert len(result["subject_roles"]) == 4
    assert "do not certify" in result["warnings"][0]
    assert "synchronise_invoices" in result["next_action"]
    assert "SYNTHETIC-EXPORT" not in str(result)
    assert subject.trail.entries()[-1].operation == "synchronisation_status"
