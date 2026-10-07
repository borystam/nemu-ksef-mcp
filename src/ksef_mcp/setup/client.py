"""Registering this server with the MCP client that will drive it.

None of this reaches KSeF. Every call here talks to the local `claude` CLI
and touches nothing but a client-side config file, so onboarding can offer
it without spending a minute of the hourly allowance.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Final

from ksef_mcp.metadata import SERVER_COMMAND

# Long enough for a cold CLI start, short enough that a hung binary does not
# strand somebody halfway through onboarding.
CLIENT_TIMEOUT_SECONDS: Final[float] = 20.0

CLIENT_EXECUTABLE: Final[str] = "claude"


def command_available() -> bool:
    return shutil.which(CLIENT_EXECUTABLE) is not None


def _run(arguments: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            [CLIENT_EXECUTABLE, *arguments],
            capture_output=True,
            text=True,
            timeout=CLIENT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def already_registered(name: str) -> bool:
    """Ask the client rather than parsing its config ourselves.

    Where that config lives differs per client and per platform, and a second
    entry under the same name is exactly the mess re-running onboarding must
    not create.
    """
    completed = _run(["mcp", "get", name])
    return completed is not None and completed.returncode == 0


def register(name: str) -> bool:
    # Use the installed environment, not an unrelated package with the same
    # executable name on PyPI. GitHub installs work before a PyPI release.
    completed = _run(["mcp", "add", name, "--", *SERVER_COMMAND])
    return completed is not None and completed.returncode == 0
