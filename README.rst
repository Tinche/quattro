quattro: task control for asyncio
=================================

.. image:: https://img.shields.io/pypi/v/quattro.svg
        :target: https://pypi.python.org/pypi/quattro

.. image:: https://github.com/Tinche/quattro/workflows/CI/badge.svg
        :target: https://github.com/Tinche/quattro/actions?workflow=CI

.. image:: https://codecov.io/gh/Tinche/quattro/branch/main/graph/badge.svg?token=9IE6FHZV2K
       :target: https://codecov.io/gh/Tinche/quattro

.. image:: https://img.shields.io/pypi/pyversions/quattro.svg
        :target: https://github.com/Tinche/quattro
        :alt: Supported Python versions

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

----

**quattro** is an Apache 2 licensed library, written in Python, for task control
in asyncio applications. `quattro` is influenced by structured concurrency
concepts from the `Trio framework`_.

`quattro` supports Python versions 3.8 - 3.10, and the 3.8 PyPy beta.

.. _`Trio framework`: https://trio.readthedocs.io/en/stable/

Installation
------------

To install `quattro`, simply:

.. code-block:: bash

    $ pip install quattro

Task Groups
-----------

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
            tg.start_soon(task_1)
            tg.start_soon(task_2)

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

Cancel scopes are not supported on Python 3.8, since the necessary underlying
asyncio machinery is not present on that version.

`quattro` contains an asyncio implementation of `Trio CancelScopes`_.
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

* ``cancel()`` - a method through which the scope can be cancelled manually
* ``deadline`` - read/write, an optional deadline for the scope, at which the scope will be cancelled
* ``cancelled_caught`` - a readonly bool property, whether the scope finished via cancellation


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
`quattro` doesn't support ``current_effective_deadline`` yet.

.. _`Trio CancelScopes`: https://trio.readthedocs.io/en/stable/reference-core.html#cancellation-and-timeouts

Changelog
---------

0.1.0 (UNRELEASED)
~~~~~~~~~~~~~~~~~~
* Initial release, containing task groups and cancellation scopes.

Credits
-------

The initial TaskGroup implementation has been taken from the `EdgeDB`_ project.
The CancelScope implementation was heavily influenced by `Trio`_, and inspired by the `async_timeout`_ package.

.. _`EdgeDB`: https://github.com/edgedb/edgedb
.. _`Trio`: https://trio.readthedocs.io/en/stable/index.html
.. _`async_timeout`: https://github.com/aio-libs/async-timeout
