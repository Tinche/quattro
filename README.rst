quattro: task control for asyncio
=================================

.. image:: https://img.shields.io/pypi/v/quattro.svg
        :target: https://pypi.python.org/pypi/quattro

.. image:: https://github.com/Tinche/quattro/workflows/CI/badge.svg
        :target: https://github.com/Tinche/quattro/actions?workflow=CI

.. image:: https://codecov.io/gh/Tinche/quattro/branch/main/graph/badge.svg?token=9IE6FHZV2K
       :target: https://codecov.io/gh/Tinche/quattro

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

----

**quattro** is an Apache 2 licensed library, written in Python, for task control
in asyncio applications. `quattro` is influenced by structured concurrency
concepts from the `Trio framework`_.

`quattro` supports Python versions 3.9 - 3.11, including PyPy.

.. _`Trio framework`: https://trio.readthedocs.io/en/stable/

Installation
------------

To install `quattro`, simply:

.. code-block:: bash

    $ pip install quattro

Task Groups
-----------

.. note:: On Python 3.11 and later, the `standard library TaskGroup`_ implementation is used instead.
    The TaskGroup implementation here can be considered a backport for older Python versions.

.. _`standard library TaskGroup`: https://docs.python.org/3/library/asyncio-task.html#task-groups

`quattro` contains a TaskGroup implementation. TaskGroups are inspired by `Trio nurseries`_.

.. code-block:: python

    from quattro import TaskGroup

    async def my_handler():
        # We want to spawn some tasks, and ensure they are all handled before we return.
        async def task_1():
            ...

        async def task_2():
            ...

        async with TaskGroup() as tg:
            t1 = tg.create_task(task_1)
            t2 = tg.create_task(task_2)

        # The end of the `async with` block awaits the tasks, ensuring they are handled.

TaskGroups are essential building blocks for achieving the concept of `structured concurrency`_.
In simple terms, structured concurrency means your code does not leak tasks - when a coroutine
finishes, all tasks spawned by that coroutine and all its children are also finished.
(In fancy terms, the execution flow becomes a directed acyclic graph.)

Structured concurrency can be achieved by using TaskGroups instead of ``asyncio.create_task``
to start background tasks. TaskGroups essentially do two things:

* when exiting from a TaskGroup ``async with`` block, the TaskGroup awaits all of its children, ensuring they are finished when it exits
* when a TaskGroup child task raises an exception, all other children and the task inside the context manager are cancelled

The implementation has been borrowed from the EdgeDB project.

.. _`Trio nurseries`: https://trio.readthedocs.io/en/stable/reference-core.html#nurseries-and-spawning
.. _`structured concurrency`: https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/

Cancel Scopes
-------------

`quattro` contains an independent, asyncio implementation of `Trio CancelScopes`_.
Due to fundamental differences between asyncio and Trio the actual runtime behavior isn't
exactly the same, but close.

.. code-block:: python

    from quattro import move_on_after

    async def my_handler():
        with move_on_after(1.0) as cancel_scope:
            await long_query()

        # 1 second later, the function continues running

`quattro` contains the following helpers:

* ``move_on_after``
* ``move_on_at``
* ``fail_after``
* ``fail_at``

All helpers produce instances of ``quattro.CancelScope``, which is largely similar to the Trio variant.

``CancelScopes`` have the following attributes:

* ``cancel()`` - a method through which the scope can be cancelled manually.
  ``cancel()`` can be called before the scope is entered; entering the scope will cancel it at the first opportunity
* ``deadline`` - read/write, an optional deadline for the scope, at which the scope will be cancelled
* ``cancelled_caught`` - a readonly bool property, whether the scope finished via cancellation

`quattro` also supports retrieving the current effective deadline in a task using ``quattro.current_effective_deadline``.
The current effective deadline is a float value, with ``float('inf')`` standing in for no deadline.

Python versions 3.11 and higher contain `similar helpers`_, ``asyncio.timeout`` and ``asyncio.timeout_at``.
The `quattro` ``fail_after`` and ``fail_at`` helpers are effectively equivalent to the asyncio timeouts, and pass the test suite for them.

The differences are:

* The `quattro` versions are normal context managers (used with just ``with``), asyncio versions are async context managers (using ``async with``).
  Neither version needs to be async since nothing is awaited; `quattro` chooses to be non-async to signal there are no suspension points being hit, match Trio and be a little more readable.
* `quattro` additionally contains the ``move_on_at`` and ``move_on_after`` helpers.
* The `quattro` versions support getting the current effective deadline.
* The `quattro` versions can be cancelled manually using ``scope.cancel()``, and precancelled before they are entered
* The `quattro` versions are available on all supported Python versions, not just 3.11+.

.. _`similar helpers`: https://docs.python.org/3/library/asyncio-task.html#timeouts

asyncio and Trio differences
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``fail_after`` and ``fail_at`` raise ``asyncio.Timeout`` instead of ``trio.Cancelled`` exceptions when they fail.

asyncio has edge-triggered cancellation semantics, while Trio has level-triggered cancellation semantics.
The following example will behave differently in `quattro` and Trio:

.. code-block:: python

    with trio.move_on_after(TIMEOUT):
        conn = make_connection()
        try:
            await conn.send_hello_msg()
        finally:
            await conn.send_goodbye_msg()

In Trio, if the ``TIMEOUT`` expires while awaiting ``send_hello_msg()``, ``send_goodbye_msg()`` will
also be cancelled. In `quattro`, ``send_goodbye_msg()`` will run (and potentially block) anyway.
This is a limitation of the underlying framework.

In `quattro`, cancellation scopes cannot be shielded.

.. _`Trio CancelScopes`: https://trio.readthedocs.io/en/stable/reference-core.html#cancellation-and-timeouts

Changelog
---------

22.2.0 (2022-12-27)
~~~~~~~~~~~~~~~~~~~
* More robust nested cancellation on 3.11.
* Better typing support for ``fail_after`` and ``fail_at``.
* Improve effective deadline handling for pre-cancelled scopes.
* TaskGroups now support custom ContextVar contexts when creating tasks, just like the standard library implementation.

22.1.0 (2022-12-19)
~~~~~~~~~~~~~~~~~~~
* Restore TaskGroup copyright notice.
* TaskGroups now raise ExceptionGroups (using the PyPI backport when necessary) on child errors.
* Add support for Python 3.11, drop 3.8.
* TaskGroups no longer have a `name` and the `repr` is slightly different, to harmonize with the Python 3.11 standard library implementation.
* TaskGroups no longer swallow child exceptions when aborting, to harmonize with the Python 3.11 standard library implementation.
* Switch to CalVer.

0.3.0 (2022-01-08)
~~~~~~~~~~~~~~~~~~
* Add `py.typed` to enable typing information.
* Flesh out type annotations for TaskGroups.

0.2.0 (2021-12-27)
~~~~~~~~~~~~~~~~~~
* Add ``quattro.current_effective_deadline``.

0.1.0 (2021-12-08)
~~~~~~~~~~~~~~~~~~
* Initial release, containing task groups and cancellation scopes.

Credits
-------

The initial TaskGroup implementation has been taken from the `EdgeDB`_ project.
The CancelScope implementation was heavily influenced by `Trio`_, and inspired by the `async_timeout`_ package.

.. _`EdgeDB`: https://github.com/edgedb/edgedb
.. _`Trio`: https://trio.readthedocs.io/en/stable/index.html
.. _`async_timeout`: https://github.com/aio-libs/async-timeout
