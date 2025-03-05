"""Task control for asyncio."""

from __future__ import annotations

from typing import Final

from ._cancelscope import (
    CancelScope,
    cancel_stack,
    fail_after,
    fail_at,
    move_on_after,
    move_on_at,
)
from ._defer import Deferrer, _defer
from ._gather import gather
from ._taskgroup import TaskGroup

__all__ = [
    "CancelScope",
    "Deferrer",
    "TaskGroup",
    "defer",
    "fail_after",
    "fail_at",
    "gather",
    "get_current_effective_deadline",
    "move_on_after",
    "move_on_at",
]


def get_current_effective_deadline() -> float:
    return min(
        [cs._deadline for cs in cancel_stack.get() if cs._deadline is not None],
        default=float("inf"),
    )


# This needs to be here for Sphinx.
defer: Final = _defer()
"""First wrap your coroutine function with `defer.enable`, then call me inside."""
