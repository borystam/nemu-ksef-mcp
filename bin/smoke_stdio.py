"""Check a separately installed server over real stdio without KSeF credentials."""

import argparse
import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from mcp import Client, StdioServerParameters

EXPECTED_TOOLS = {
    "server_info",
    "synchronisation_status",
    "synchronise_invoices",
    "list_recent_invoices",
    "export_period_statement",
    "review_new_invoices",
    "render_invoice_pdf",
}


async def check(server: Path) -> None:
    with TemporaryDirectory(prefix="nemu-ksef-smoke-") as temporary:
        transport = StdioServerParameters(
            command=str(server.resolve()),
            env={"KSEF_DIAGNOSTIC_DIRECTORY": temporary},
            cwd=temporary,
        )
        async with Client(transport, raise_exceptions=True, read_timeout_seconds=20) as client:
            listed = await client.list_tools()
            names = {tool.name for tool in listed.tools}
            if names != EXPECTED_TOOLS:
                raise RuntimeError(f"Unexpected tool surface: {sorted(names)}")
            result = await client.call_tool("server_info")
            identity = result.structured_content
            if result.is_error or identity is None or identity["name"] != "nemu-ksef-mcp":
                raise RuntimeError("Installed server identity check failed")
            print(json.dumps({"identity": identity, "tools": sorted(names), "transport": "stdio"}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", type=Path, required=True, help="Installed executable path")
    args = parser.parse_args()
    asyncio.run(check(args.server))


if __name__ == "__main__":
    main()
