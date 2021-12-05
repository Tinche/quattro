from asyncio import (
    CancelledError,
    Handle,
    Task,
    TimeoutError,
    TimerHandle,
    current_task,
    get_running_loop,
)
from contextlib import contextmanager
from typing import ContextManager, Iterator, Optional, Union

from attr import define, field


@define
class CancelScope:
    _deadline: Optional[float] = None
    cancelled_caught: bool = field(default=False, init=False)
    _current_task: Optional[Task] = field(default=None, init=False)
    _timeout_handler: Union[TimerHandle, Handle, None] = field(default=None, init=False)
    _cancel_called: bool = field(default=False, init=False)

    def cancel(self) -> None:
        """Request cancellation of this scope."""
        self._cancel_called = True
        if self._current_task is not None:
            self._current_task.cancel(str(id(self)))

    @property
    def deadline(self):
        return self._deadline

    @deadline.setter
    def deadline(self, value: Optional[float]):
        if self._deadline == value:
            return
        self._deadline = value
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
        if value is not None:
            self._timeout_handler = get_running_loop().call_at(value, self.__timeout_cb)

    def __enter__(self) -> "CancelScope":
        self._current_task = current_task()
        if self._cancel_called:
            # The scope was cancelled before entering.
            self._timeout_handler = get_running_loop().call_soon(self.__timeout_cb)
        elif self._deadline is not None:
            self._timeout_handler = get_running_loop().call_at(
                self._deadline, self.__timeout_cb
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Optional[bool]:
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

        self._current_task = None

        if exc_type is CancelledError and exc_val.args and exc_val.args[0] == id(self):
            self.cancelled_caught = True
            return True
        return None

    def __timeout_cb(self):
        if self._current_task is not None:
            self._current_task.cancel(id(self))


def move_on_after(seconds: float) -> CancelScope:
    """
    Use as a context manager to create a cancel scope whose deadline is set to
    now + seconds.
    """
    return move_on_at(get_running_loop().time() + seconds)


def move_on_at(deadline: float) -> CancelScope:
    """
    Use as a context manager to create a cancel scope with the given absolute deadline.
    """
    return CancelScope(deadline)


def fail_after(seconds: float) -> ContextManager[CancelScope]:
    """
    Create a cancel scope with the given timeout, and raises an error if it is actually
    cancelled.

    This function and move_on_after() are similar in that both create a cancel scope
    with a given timeout, and if the timeout expires then both will cause CancelledError
    to be raised within the scope. The difference is that when the CancelledError
    exception reaches move_on_after(), it’s caught and discarded. When it reaches
    fail_after(), then it’s caught and TimeoutError is raised in its place.
    """
    return fail_at(get_running_loop().time() + seconds)


@contextmanager
def fail_at(deadline: float) -> Iterator[CancelScope]:
    """
    Create a cancel scope with the given deadline, and raises an error if it is
    actually cancelled.

    This function and move_on_at() are similar in that both create a cancel scope with
    a given absolute deadline, and if the deadline expires then both will cause
    CancelledError to be raised within the scope. The difference is that when the
    CancelledError exception reaches move_on_at(), it’s caught and discarded. When it
    reaches fail_at(), then it’s caught and TimeoutError is raised in its place.
    """
    with move_on_at(deadline) as scope:
        yield scope
    if scope.cancelled_caught:
        raise TimeoutError()
