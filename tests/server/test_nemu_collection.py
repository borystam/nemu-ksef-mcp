"""A synthetic month through the MCP boundary, with real collection and storage.

The archive treats XML as original evidence; this test does not claim FA(3)
schema validation. Only KSeF and the machine's configuration, token and clock
are substituted. Socket connections are denied throughout the test.
"""

import hashlib
import json
import socket
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from io import BytesIO
from pathlib import Path
from typing import ClassVar

import pytest
from mcp import Client

from ksef_mcp import clock
from ksef_mcp.invoices.package import METADATA_ENTRY
from ksef_mcp.ksef_port import (
    ExportEncryption,
    ExportHandle,
    ExportPart,
    ExportState,
    ExportStatus,
    KsefEnvironment,
    Period,
    SubjectRole,
)
from ksef_mcp.ksef_port import adapter as port_adapter
from ksef_mcp.ksef_port.types import MAX_QUERY_WINDOW, SYNCHRONISED_SUBJECT_ROLES
from ksef_mcp.server import server
from ksef_mcp.storage.archive import InvoiceArchive
from ksef_mcp.storage.audit import AuditTrail, Disclosure
from ksef_mcp.storage.sync_store import MINIMUM_INTERVAL, SyncStore
from tests.invoices.test_synchronisation import ScriptedPort, ScriptedSession, allowances
from tests.server.conftest import NIP
from tests.support.synthetic import aes_encrypted, base64_digest

MONTH_START = datetime(2026, 9, 1, tzinfo=UTC)
MONTH_END = datetime(2026, 10, 1, tzinfo=UTC)
KEY = b"m" * 32
IV = b"synthetic-vector"


def month_number(ordinal: int) -> str:
    day = (ordinal - 1) % 30 + 1
    return f"{NIP}-202609{day:02d}-{ordinal:012X}-56"


def month_body(ordinal: int) -> bytes:
    currency = "EUR" if ordinal % 7 == 0 else "PLN"
    corrective = ordinal % 10 == 0
    kind = "KOR" if corrective else "VAT"
    amount = "-12.30" if corrective else "123.45"
    correction = (
        f"<NrKSeFFaKorygowanej>{month_number(ordinal - 1)}</NrKSeFFaKorygowanej>"
        if corrective
        else ""
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<Faktura><Podmiot1>Sprzedawca próbny {ordinal}</Podmiot1>"
        "<Podmiot2>Nabywca próbny</Podmiot2>"
        f"<Fa><P_2>TEST/09/{ordinal}</P_2><KodWaluty>{currency}</KodWaluty>"
        f"<P_15>{amount}</P_15><RodzajFaktury>{kind}</RodzajFaktury>"
        f"{correction}</Fa></Faktura>\n"
    ).encode()


@dataclass(frozen=True)
class MonthPackage:
    part: ExportPart
    encrypted: bytes
    count: int


def packaged_month(ordinals: range, originals: dict[str, bytes]) -> MonthPackage:
    buffer = BytesIO()
    manifest: list[dict[str, str]] = []
    with zipfile.ZipFile(buffer, mode="w") as package:
        for ordinal in reversed(ordinals):
            number = month_number(ordinal)
            body = originals[number]
            # Neither lexical order nor the package name identifies an invoice.
            package.writestr(f"document-{1000 - ordinal}.xml", body)
            manifest.append({"ksefNumber": number, "invoiceHash": base64_digest(body)})
        package.writestr(METADATA_ENTRY, json.dumps({"invoices": manifest}).encode())
    raw = buffer.getvalue()
    encrypted = aes_encrypted(raw, key=KEY, initialisation_vector=IV)
    return MonthPackage(
        part=ExportPart(
            ordinal=1,
            name="month.zip.aes",
            method="GET",
            url="https://synthetic.invalid/month.zip.aes",
            size_bytes=len(raw),
            content_hash=base64_digest(raw),
            encrypted_size_bytes=len(encrypted),
            encrypted_content_hash=base64_digest(encrypted),
        ),
        encrypted=encrypted,
        count=len(ordinals),
    )


@dataclass
class MonthSession(ScriptedSession):
    packages: dict[SubjectRole, MonthPackage] = field(default_factory=dict)

    def start_export(self, *, period: Period, subject_role: SubjectRole) -> ExportHandle:
        self.started.append((subject_role, period))
        return ExportHandle(
            reference=f"MONTH-{len(self.started)}",
            encryption=ExportEncryption(key=KEY, initialisation_vector=IV),
        )

    def _package(self, reference: str) -> MonthPackage | None:
        role, _ = self.started[int(reference.removeprefix("MONTH-")) - 1]
        return self.packages.get(role)

    def check_export(self, *, handle: ExportHandle) -> ExportStatus:
        self.polled.append(handle.reference)
        package = self._package(handle.reference)
        return ExportStatus(
            state=ExportState.EMPTY if package is None else ExportState.READY,
            parts=() if package is None else (package.part,),
            truncated=False,
            hwm_date=None if package is None else MONTH_END,
            last_permanent_storage_date=None,
            invoice_count=0 if package is None else package.count,
        )

    def fetch_part(self, *, handle: ExportHandle, part: ExportPart) -> bytes:
        self.fetched.append(handle.reference)
        package = self._package(handle.reference)
        assert package is not None and part == package.part
        return package.encrypted


class MonthClock(datetime):
    moment: ClassVar[datetime] = MONTH_END + timedelta(hours=2)

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> datetime:
        return cls.moment.astimezone(tz)


def deny_network(*args: object, **kwargs: object) -> None:
    raise AssertionError("This synthetic collection test must not connect to a network.")


@pytest.mark.anyio
async def test_mcp_collects_a_month_preserves_every_byte_and_bounds_repeat_results(
    monkeypatch: pytest.MonkeyPatch, with_a_token: None, subject_data_root: Path
) -> None:
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket.socket, "connect_ex", deny_network)
    monkeypatch.setattr(socket, "getaddrinfo", deny_network)
    monkeypatch.setattr(clock, "datetime", MonthClock)
    monkeypatch.setattr(MonthClock, "moment", MONTH_END + timedelta(hours=2))
    # Independent expected corpus: 160 identities, including 16 corrections,
    # both currencies and ten invoices delivered in both frequent roles.
    originals = {month_number(ordinal): month_body(ordinal) for ordinal in range(1, 161)}
    session = MonthSession(
        statuses=[],
        limits=allowances(),
        packages={
            SubjectRole.SELLER: packaged_month(range(1, 81), originals),
            SubjectRole.BUYER: packaged_month(range(71, 161), originals),
        },
    )
    monkeypatch.setattr(
        port_adapter,
        "Ksef2Port",
        lambda *, environment: ScriptedPort(session_double=session, environment=environment),
    )
    archive = InvoiceArchive(nip=NIP, environment=KsefEnvironment.TEST)
    store = SyncStore(nip=NIP, environment=KsefEnvironment.TEST)
    trail = AuditTrail(nip=NIP, environment=KsefEnvironment.TEST)

    async with Client(server, raise_exceptions=True) as client:
        first = await client.call_tool(
            "synchronise_invoices", {"initial_from": MONTH_START.isoformat()}
        )

    result = first.structured_content
    assert result is not None
    by_role = {role["subject_role"]: role for role in result["subject_roles"]}
    assert set(by_role) == {str(role) for role in SYNCHRONISED_SUBJECT_ROLES}
    assert by_role["seller"]["archived_count"] == 80
    assert by_role["buyer"]["archived_count"] == 80
    assert by_role["buyer"]["already_held_count"] == 10
    for role in ("seller", "buyer"):
        assert by_role[role]["identifiers_truncated"] is True
        assert len(by_role[role]["archived"]) == 50
    assert {period.date_from for _, period in session.started} == {MONTH_START}
    assert all(
        period.date_to - period.date_from <= MAX_QUERY_WINDOW for _, period in session.started
    )
    assert len(session.started) == 4
    assert result["pending_exports"] == []

    files = {path.stem: path for path in archive.invoice_directory.glob("*.xml")}
    assert set(files) == set(originals)
    assert {number: path.read_bytes() for number, path in files.items()} == originals
    index = archive.load_index()
    assert len(index.entries) == 160
    assert {entry.ksef_number: entry.content_hash for entry in index.entries} == {
        number: hashlib.sha256(body).hexdigest() for number, body in originals.items()
    }
    writes = [entry for entry in trail.entries() if entry.disclosure is Disclosure.DISK]
    assert sum(entry.document_count for entry in writes) == 160
    assert {number for entry in writes for number in entry.ksef_numbers} == set(originals)
    assert store.load().pending == ()
    before = {number: path.stat().st_mtime_ns for number, path in files.items()}

    # A fresh client creates fresh services and stores. The durable scheduling
    # floor blocks immediate repeat exports, even across that boundary.
    async with Client(server, raise_exceptions=True) as client:
        immediate = await client.call_tool("synchronise_invoices")
    assert len(session.started) == 4
    assert immediate.structured_content is not None
    assert all(
        role["outcome"] == "not_due" for role in immediate.structured_content["subject_roles"]
    )

    # Deliberately redeliver the same packages after the permitted interval.
    # Duplicate delivery must preserve evidence without rewriting files.
    MonthClock.moment += MINIMUM_INTERVAL
    async with Client(server, raise_exceptions=True) as client:
        replay = await client.call_tool("synchronise_invoices")
    assert replay.structured_content is not None
    repeated = {role["subject_role"]: role for role in replay.structured_content["subject_roles"]}
    assert repeated["seller"]["already_held_count"] == 80
    assert repeated["buyer"]["already_held_count"] == 90
    assert sum(role["archived_count"] for role in repeated.values()) == 0
    for role in ("seller", "buyer"):
        assert repeated[role]["identifiers_truncated"] is True
        assert len(repeated[role]["already_held"]) == 50
    assert [role for role, _ in session.started[4:]] == [SubjectRole.SELLER, SubjectRole.BUYER]
    assert {period.date_from for _, period in session.started[4:]} == {MONTH_END}
    assert {number: path.stat().st_mtime_ns for number, path in files.items()} == before
    assert {number: path.read_bytes() for number, path in files.items()} == originals
    assert archive.load_index() == index
    assert store.load().pending == ()
    assert "<Faktura>" not in json.dumps(replay.structured_content)
