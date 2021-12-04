quattro: task control for asyncio
=================================

.. image:: https://img.shields.io/pypi/v/quattro.svg
        :target: https://pypi.python.org/pypi/quattro

.. image:: https://github.com/Tinche/quattro/workflows/CI/badge.svg
        :target: https://github.com/Tinche/quattro/actions?workflow=CI

.. image:: https://codecov.io/gh/Tinche/quattro/branch/master/graph/badge.svg
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

The implementation has been borrowed from the `EdgeDB project`.

.. _`Trio nurseries`: https://trio.readthedocs.io/en/stable/reference-core.html#nurseries-and-spawning
.. _`EdgeDB project`: https://github.com/edgedb/edgedb

Changelog
---------

0.1.0 (UNRELEASED)
~~~~~~~~~~~~~~~~~~
* Initial release, containing task groups.

Credits
-------

The initial TaskGroup implementation has been taken from the `EdgeDB`_ project.

.. _`EdgeDB`: https://github.com/edgedb/edgedb
