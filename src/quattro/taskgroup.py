#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2016-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import builtins


if "ExceptionGroup" not in dir(builtins):
    from exceptiongroup import ExceptionGroup
else:
    ExceptionGroup = ExceptionGroup

try:
    from asyncio.taskgroups import TaskGroup
except ImportError:
    import asyncio
    import types
    import weakref

    from asyncio import AbstractEventLoop, Future, Task
    from contextvars import Context
    from functools import partial
    from typing import Any, Coroutine, List, Optional, TypeVar

    R = TypeVar("R")

    class TaskGroup:  # type: ignore
        def __init__(self) -> None:
            self._exiting = False
            self._aborting = False
            self._loop: Optional[AbstractEventLoop] = None
            self._parent_task: Optional[Task] = None
            self._parent_cancel_requested = False
            self._tasks: weakref.WeakSet[Task] = weakref.WeakSet()
            self._unfinished_tasks = 0
            self._errors: List[Exception] = []
            self._base_error: Optional[BaseException] = None
            self._on_completed_fut: Optional[Future] = None

        def __repr__(self):
            msg = "<TaskGroup"
            if self._tasks:
                msg += f" tasks={len(self._tasks)}"
            if self._errors:
                msg += f" errors={len(self._errors)}"
            if self._aborting:
                msg += " cancelling"
            elif self._loop is not None:
                msg += " entered"
            msg += ">"
            return msg

        async def __aenter__(self) -> "TaskGroup":  # type: ignore
            if self._loop is not None:
                raise RuntimeError(f"TaskGroup {self!r} has been already entered")

            self._loop = asyncio.get_running_loop()

            self._parent_task = asyncio.current_task(self._loop)
            if self._parent_task is None:
                raise RuntimeError(
                    f"TaskGroup {self!r} cannot determine the parent task"
                )
            self._patch_task(self._parent_task)

            return self  # type: ignore

        async def __aexit__(self, et, exc, _) -> None:
            self._exiting = True
            loop = self._loop
            assert loop is not None
            self._loop = None
            propagate_cancellation_error = None

            if (
                exc is not None
                and self._is_base_error(exc)
                and self._base_error is None
            ):
                self._base_error = exc

            if et is asyncio.CancelledError:
                if self._parent_cancel_requested:
                    # Only if we did request task to cancel ourselves
                    # we mark it as no longer cancelled.
                    self._parent_task.__cancel_requested__ = False  # type: ignore
                else:
                    propagate_cancellation_error = et

            if et is not None and not self._aborting:
                # Our parent task is being cancelled:
                #
                #    async with TaskGroup() as g:
                #        g.create_task(...)
                #        await ...  # <- CancelledError
                #
                if et is asyncio.CancelledError:
                    propagate_cancellation_error = et

                # or there's an exception in "async with":
                #
                #    async with TaskGroup() as g:
                #        g.create_task(...)
                #        1 / 0
                #
                self._abort()

            # We use while-loop here because "self._on_completed_fut"
            # can be cancelled multiple times if our parent task
            # is being cancelled repeatedly (or even once, when
            # our own cancellation is already in progress)
            while self._unfinished_tasks:
                if self._on_completed_fut is None:
                    self._on_completed_fut = loop.create_future()

                try:
                    await self._on_completed_fut
                except asyncio.CancelledError as ex:
                    if not self._aborting:
                        # Our parent task is being cancelled:
                        #
                        #    async def wrapper():
                        #        async with TaskGroup() as g:
                        #            g.create_task(foo)
                        #
                        # "wrapper" is being cancelled while "foo" is
                        # still running.
                        propagate_cancellation_error = ex
                        self._abort()

                self._on_completed_fut = None

            assert self._unfinished_tasks == 0
            self._on_completed_fut = None  # no longer needed

            if self._base_error is not None:
                raise self._base_error

            if propagate_cancellation_error is not None and not self._errors:
                # The wrapping task was cancelled; since we're done with
                # closing all child tasks, just propagate the cancellation
                # request now.
                raise propagate_cancellation_error

            if et is not None and et is not asyncio.CancelledError:
                self._errors.append(exc)

            if self._errors:
                # Exceptions are heavy objects that can have object
                # cycles (bad for GC); let's not keep a reference to
                # a bunch of them.
                errors = self._errors
                self._errors = []

                me = ExceptionGroup("unhandled errors in a TaskGroup", errors)
                raise me from None

        def create_task(
            self, coro: Coroutine[Any, Any, R], *, context: Optional[Context] = None
        ) -> "Task[R]":
            if self._exiting:
                raise RuntimeError(f"TaskGroup {self!r} is awaiting in exit")
            if self._loop is None:
                raise RuntimeError(f"TaskGroup {self!r} has not been entered")
            assert self._parent_task
            if context is None:
                task = self._loop.create_task(coro)
            else:
                task = context.run(self._loop.create_task, coro)  # type: ignore
            task.add_done_callback(
                partial(
                    self._on_task_done, loop=self._loop, parent_task=self._parent_task
                )
            )
            self._unfinished_tasks += 1
            self._tasks.add(task)
            return task

        def _is_base_error(self, exc: BaseException) -> bool:
            assert isinstance(exc, BaseException)
            return isinstance(exc, (SystemExit, KeyboardInterrupt))

        def _patch_task(self, task):
            # In Python 3.8 we'll need proper API on asyncio.Task to
            # make TaskGroups possible. We need to be able to access
            # information about task cancellation, more specifically,
            # we need a flag to say if a task was cancelled or not.
            # We also need to be able to flip that flag.

            def _task_cancel(self, msg=None):
                self.__cancel_requested__ = True
                return asyncio.Task.cancel(self, msg)

            if hasattr(task, "__cancel_requested__"):
                return

            task.__cancel_requested__ = False
            # confirm that we were successful at adding the new attribute:
            assert not task.__cancel_requested__

            task.cancel = types.MethodType(_task_cancel, task)

        def _abort(self):
            self._aborting = True

            for t in self._tasks:
                if not t.done():
                    t.cancel()

        def _on_task_done(
            self, task: Task, loop: AbstractEventLoop, parent_task: Task
        ) -> None:
            self._unfinished_tasks -= 1
            assert self._unfinished_tasks >= 0

            if self._exiting and not self._unfinished_tasks:
                if (
                    self._on_completed_fut is not None
                    and not self._on_completed_fut.done()
                ):
                    self._on_completed_fut.set_result(True)

            if task.cancelled():
                return

            exc = task.exception()
            if exc is None:
                return

            self._errors.append(exc)  # type: ignore
            if self._is_base_error(exc) and self._base_error is None:
                self._base_error = exc

            if parent_task.done():
                # Not sure if this case is possible, but we want to handle
                # it anyways.
                loop.call_exception_handler(
                    {
                        "message": f"Task {task!r} has errored out but its parent "
                        f"task {self._parent_task} is already completed",
                        "exception": exc,
                        "task": task,
                    }
                )
                return

            self._abort()
            if not parent_task.__cancel_requested__:  # type: ignore
                # If parent task *is not* being cancelled, it means that we want
                # to manually cancel it to abort whatever is being run right now
                # in the TaskGroup.  But we want to mark parent task as
                # "not cancelled" later in __aexit__.  Example situation that
                # we need to handle:
                #
                #    async def foo():
                #        try:
                #            async with TaskGroup() as g:
                #                g.create_task(crash_soon())
                #                await something  # <- this needs to be canceled
                #                                 #    by the TaskGroup, e.g.
                #                                 #    foo() needs to be cancelled
                #        except Exception:
                #            # Ignore any exceptions raised in the TaskGroup
                #            pass
                #        await something_else     # this line has to be called
                #                                 # after TaskGroup is finished.
                self._parent_cancel_requested = True
                parent_task.cancel()
