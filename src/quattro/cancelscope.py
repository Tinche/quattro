import sys

from asyncio import (
    CancelledError,
    Handle,
    Task,
    TimeoutError,
    TimerHandle,
    current_task,
    get_running_loop,
)
from contextvars import ContextVar
from typing import Final, Literal, Optional, Tuple, Union

from attr import define, field


_is_311_or_later: Final = sys.version_info >= (3, 11)


@define
class CancelScope:
    _deadline: Optional[float] = None
    cancelled_caught: bool = field(default=False, init=False)
    _current_task: Union[Task, None, Literal["done"]] = field(default=None, init=False)
    _timeout_handler: Union[TimerHandle, Handle, None] = field(default=None, init=False)
    _cancel_status: Literal["prequeued", "none", "called"] = field(
        default="none", init=False
    )
    _raise_on_cancel: bool = field(default=False, init=False)

    def cancel(self) -> None:
        """Request cancellation of this scope."""
        if self._current_task is None:
            # We haven't entered yet.
            # Queue up the cancel to be called on entering.
            self._cancel_status = "prequeued"
            return

        if self._cancel_status == "called" or self._current_task == "done":
            # Already called, maybe by the timeout handler?
            return
        self._cancel_status = "called"
        self._current_task.cancel(id(self))
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

    @property
    def deadline(self) -> Optional[float]:
        return self._deadline

    @deadline.setter
    def deadline(self, value: Optional[float]) -> None:
        if self._deadline == value:
            return
        self._deadline = value
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None
        if value is not None:
            self._timeout_handler = get_running_loop().call_at(value, self.__timeout_cb)

    if _is_311_or_later:

        def __enter__(self) -> "CancelScope":
            if self._current_task is not None:
                raise RuntimeError("Scope already entered")

            self._current_task = current_task()
            cancel_stack.set((self,) + cancel_stack.get())
            if self._cancel_status == "prequeued":
                if self._timeout_handler is not None:
                    self._timeout_handler.cancel()
                self._timeout_handler = get_running_loop().call_soon(self.__timeout_cb)
                self._deadline = get_running_loop().time()
            elif self._deadline is not None:
                loop = get_running_loop()
                if self._deadline <= loop.time():
                    # This is mostly a fix for sleep(0) :/
                    self._timeout_handler = loop.call_soon(self.__timeout_cb)
                else:
                    self._timeout_handler = loop.call_at(
                        self._deadline, self.__timeout_cb
                    )
            return self

        def __exit__(
            self, exc_type: type[BaseException] | None, exc_val, _
        ) -> bool | None:
            handler_done = True
            if self._timeout_handler is not None:
                # Means the timeout handler hasn't run yet.
                handler_done = False
                self._timeout_handler.cancel()
                self._timeout_handler = None

            assert self._current_task is not None
            assert self._current_task != "done"
            cancel_stack.set(cancel_stack.get()[1:])

            ct = self._current_task
            self._current_task = "done"
            if (
                exc_type is CancelledError
                and handler_done
                and self._cancel_status == "called"
                and ct.uncancel() == 0
            ):
                self.cancelled_caught = True
                if self._raise_on_cancel:
                    raise TimeoutError()
                return True
            return None

    else:

        def __enter__(self) -> "CancelScope":
            if self._current_task is not None:
                raise RuntimeError("Scope already entered")

            self._current_task = current_task()
            cancel_stack.set((self,) + cancel_stack.get())
            if self._cancel_status == "prequeued":
                # The scope was cancelled before entering.
                if self._timeout_handler is not None:
                    self._timeout_handler.cancel()
                self._timeout_handler = get_running_loop().call_soon(self.__timeout_cb)
                self._deadline = get_running_loop().time()
            elif self._deadline is not None:
                loop = get_running_loop()
                if self._deadline <= loop.time():
                    # This is mostly a fix for sleep(0) :/
                    self._timeout_handler = loop.call_soon(self.__timeout_cb)
                else:
                    self._timeout_handler = loop.call_at(
                        self._deadline, self.__timeout_cb
                    )
            return self

        def __exit__(
            self, exc_type: Optional[type[BaseException]], exc_val, _
        ) -> Optional[bool]:
            if self._timeout_handler is not None:
                self._timeout_handler.cancel()
                self._timeout_handler = None

            self._current_task = "done"
            cancel_stack.set(cancel_stack.get()[1:])

            if (
                exc_type is CancelledError
                and exc_val.args
                and exc_val.args[0] == id(self)
            ):
                self.cancelled_caught = True
                if self._raise_on_cancel:
                    raise TimeoutError()
                return True
            return None

    def __timeout_cb(self) -> None:
        if self._current_task not in (None, "done"):
            self.cancel()


cancel_stack = ContextVar[Tuple[CancelScope, ...]]("cancel_stack", default=())


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


def fail_after(seconds: float) -> CancelScope:
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


def fail_at(deadline: float) -> CancelScope:
    """
    Create a cancel scope with the given deadline, and raises an error if it is
    actually cancelled.

    This function and move_on_at() are similar in that both create a cancel scope with
    a given absolute deadline, and if the deadline expires then both will cause
    CancelledError to be raised within the scope. The difference is that when the
    CancelledError exception reaches move_on_at(), it’s caught and discarded. When it
    reaches fail_at(), then it’s caught and TimeoutError is raised in its place.
    """
    scope = CancelScope(deadline)
    scope._raise_on_cancel = True
    return scope
