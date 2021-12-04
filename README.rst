quattro: task control for asyncio
=================================

*quattro** is an Apache 2 licensed library, written in Python, for task control
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

The implementation has been borrowed from the `EdgeDB project`.

.. _`Trio nurseries`: https://trio.readthedocs.io/en/stable/reference-core.html#nurseries-and-spawning
.. _`EdgeDB`: https://github.com/edgedb/edgedb
