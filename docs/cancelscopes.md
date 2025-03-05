```{currentmodule} quattro
```
# Cancel scopes

_quattro_ contains an independent, asyncio implementation of [Trio cancel scopes](https://trio.readthedocs.io/en/stable/reference-core.html#cancellation-and-timeouts).

```python
from quattro import move_on_after

async def my_handler():
    with move_on_after(1.0) as cancel_scope:
        await long_query()

    # 1 second later, the function continues running
```

_quattro_ contains the following helpers:

- {meth}`fail_after`
- {meth}`fail_at`
- {meth}`move_on_after`
- {meth}`move_on_at`

```{admonition} When and where to use
* Use to make use of deadlines, which are more powerful than timeouts since they affect
groups of operations.
* Use to gain access to {meth}`get_current_effective_deadline`, which enables deadline propagation
between services.
```

All helpers produce instances of {class}`quattro.CancelScope`, which is largely similar to the Trio variant.

CancelScopes have the following attributes:

- {meth}`cancel() <CancelScope.cancel>` - a method through which the scope can be cancelled manually.
  `cancel()` can be called before the scope is entered; entering the scope will cancel it at the first opportunity
- {meth}`deadline <CancelScope.deadline>` - read/write, an optional deadline for the scope, at which the scope will be cancelled
- {meth}`cancelled_caught <CancelScope.cancelled_caught>` - a readonly bool property, whether the scope finished via cancellation

_quattro_ also supports retrieving the current effective deadline in a task using {meth}`quattro.get_current_effective_deadline`.
The current effective deadline is a float value, with `float('inf')` standing in for no deadline.

Python versions 3.11 and higher contain [similar helpers](https://docs.python.org/3/library/asyncio-task.html#timeouts), `asyncio.timeout` and `asyncio.timeout_at`.
The _quattro_ {meth}`fail_after` and {meth}`fail_at` helpers are effectively equivalent to the asyncio timeouts, and pass the test suite for them.

The differences are:

- The _quattro_ versions are normal context managers (used with just `with`), asyncio versions are async context managers (using `async with`).
  Neither version needs to be async since nothing is awaited; _quattro_ chooses to be non-async to signal there are no suspension points being hit, match Trio and be a little more readable.
- _quattro_ additionally contains the {meth}`move_on_at` and {meth}`move_on_after` helpers.
- The _quattro_ versions support getting the current effective deadline.
- The _quattro_ versions can be cancelled manually using {meth}`CancelScope.cancel()`, and precancelled before they are entered
- The _quattro_ versions are available on all supported Python versions, not just 3.11+.


## asyncio and Trio differences

{meth}`fail_after` and {meth}`fail_at` raise [`TimeoutError`](https://docs.python.org/3/library/exceptions.html#TimeoutError) instead of `trio.Cancelled` exceptions when they fail.

asyncio has edge-triggered cancellation semantics, while Trio has level-triggered cancellation semantics.
The following example will behave differently in _quattro_ and Trio:

```python
with trio.move_on_after(TIMEOUT):
    conn = make_connection()
    try:
        await conn.send_hello_msg()
    finally:
        await conn.send_goodbye_msg()
```

In Trio, if the `TIMEOUT` expires while awaiting `send_hello_msg()`, `send_goodbye_msg()` will also be cancelled.
In _quattro_, `send_goodbye_msg()` will run (and potentially block) anyway.
This is a limitation of the underlying framework.

In _quattro_, cancellation scopes cannot be shielded.
