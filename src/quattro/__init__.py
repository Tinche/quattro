"""Task control for asyncio."""
from __future__ import annotations

from ._gather import gather
from .cancelscope import (
    CancelScope,
    cancel_stack,
    fail_after,
    fail_at,
    move_on_after,
    move_on_at,
)
from .taskgroup import TaskGroup

__all__ = [
    "CancelScope",
    "fail_after",
    "fail_at",
    "gather",
    "get_current_effective_deadline",
    "move_on_after",
    "move_on_at",
    "TaskGroup",
    "TaskGroupError",
]


def get_current_effective_deadline() -> float:
    return min(
        [cs._deadline for cs in cancel_stack.get() if cs._deadline is not None],
        default=float("inf"),
    )
