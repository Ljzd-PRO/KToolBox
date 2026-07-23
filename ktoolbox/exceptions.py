from __future__ import annotations


class KToolBoxUserError(Exception):
    """An expected refusal that should be shown without a traceback."""

    def __init__(self, message: str, *, label: str = "Error", exit_code: int = 2) -> None:
        self.label = label
        self.exit_code = exit_code
        super().__init__(message)


__all__ = ["KToolBoxUserError"]
