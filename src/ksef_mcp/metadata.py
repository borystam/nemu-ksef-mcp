import sys
from importlib.metadata import version
from typing import Final

# The MCP server name is protocol identity that clients key on; the
# distribution name is packaging. importlib.metadata resolves the latter,
# so conflating them breaks the version lookup whenever either is renamed.
SERVER_NAME: Final[str] = "nemu-ksef-mcp"

DISTRIBUTION_NAME: Final[str] = "nemu-ksef-mcp"

VERSION: Final[str] = version(DISTRIBUTION_NAME)

SERVER_COMMAND: Final[tuple[str, ...]] = (
    sys.executable,
    "-c",
    "from ksef_mcp.cli import main; raise SystemExit(main())",
)
