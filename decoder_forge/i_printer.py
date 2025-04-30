from typing import Protocol


class IPrinter(Protocol):
    def print(self, out: str) -> None: ...
