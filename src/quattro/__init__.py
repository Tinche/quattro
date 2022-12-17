"""Task control for asyncio."""
from .cancelscope import (
    CancelScope,
    cancel_stack,
    fail_after,
    fail_at,
    move_on_after,
    move_on_at,
)
from .taskgroup import TaskGroup


def get_current_effective_deadline() -> float:
    return min(
        [cs._deadline for cs in cancel_stack.get() if cs._deadline is not None],
        default=float("inf"),
    )


__all__ = [
    "TaskGroup",
    "TaskGroupError",
    "fail_after",
    "fail_at",
    "move_on_after",
    "move_on_at",
    "CancelScope",
    "get_current_effective_deadline",
]
