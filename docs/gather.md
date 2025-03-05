```{currentmodule} quattro
```
# `quattro.gather`

_quattro_ comes with an independent, simple implementation of [`asyncio.gather()`](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather) based on Task Groups.
The _quattro_ version is safer, and uses a task group under the hood to not leak tasks in cases of errors in child tasks.

```{admonition} When and where to use
Since it's almost a drop-in replacement for [`asyncio.gather()`](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather),
use everywhere for more predicable handling of failed tasks.
```

```python
from quattro import gather

async def my_handler():
    res_1, res_2 = await gather(long_query_1(), long_query_2())
```

The `return_exceptions` argument can be used to make {meth}`gather()` catch and return exceptions as responses instead of letting them bubble out.

```python
from quattro import gather

async def my_handler():
    res_1, res_2 = await gather(
        long_query_1(),
        long_query_2(),
        return_exceptions=True,
    )

    # res_1 and res_2 may be instances of exceptions.
```

The differences to `asyncio.gather()` are:
- If a child task fails other unfinished tasks will be cancelled, just like in a TaskGroup.
- {meth}`quattro.gather()` only accepts coroutines and not futures and generators, just like a TaskGroup.
- When `return_exceptions` is false (the default), an exception in a child task will cause an ExceptionGroup to bubble out of the top-level {meth}`gather()` call, just like in a TaskGroup.
- Results are returned as a tuple, not a list.
