import socket

import pytest


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
@pytest.mark.parametrize("family", [socket.AF_INET, socket.AF_INET6])
def test_default_suite_refuses_network_before_connecting(method: str, family: int) -> None:
    with socket.socket(family, socket.SOCK_STREAM) as sock:
        with pytest.raises(AssertionError, match="Network is disabled"):
            getattr(sock, method)(("::1" if family == socket.AF_INET6 else "127.0.0.1", 443))
