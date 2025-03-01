# Cancel Scopes

_quattro_ contains an independent, asyncio implementation of [Trio CancelScopes](https://trio.readthedocs.io/en/stable/reference-core.html#cancellation-and-timeouts).
Due to fundamental differences between asyncio and Trio the actual runtime behavior isn't exactly the same, but close.

```python
from quattro import move_on_after

async def my_handler():
    with move_on_after(1.0) as cancel_scope:
        await long_query()

    # 1 second later, the function continues running
```

_quattro_ contains the following helpers:

- `move_on_after`
- `move_on_at`
- `fail_after`
- `fail_at`

All helpers produce instances of `quattro.CancelScope`, which is largely similar to the Trio variant.

`CancelScopes` have the following attributes:

- `cancel()` - a method through which the scope can be cancelled manually.
  `cancel()` can be called before the scope is entered; entering the scope will cancel it at the first opportunity
- `deadline` - read/write, an optional deadline for the scope, at which the scope will be cancelled
- `cancelled_caught` - a readonly bool property, whether the scope finished via cancellation

_quattro_ also supports retrieving the current effective deadline in a task using `quattro.current_effective_deadline`.
The current effective deadline is a float value, with `float('inf')` standing in for no deadline.

Python versions 3.11 and higher contain [similar helpers](https://docs.python.org/3/library/asyncio-task.html#timeouts), `asyncio.timeout` and `asyncio.timeout_at`.
The _quattro_ `fail_after` and `fail_at` helpers are effectively equivalent to the asyncio timeouts, and pass the test suite for them.

The differences are:

- The _quattro_ versions are normal context managers (used with just `with`), asyncio versions are async context managers (using `async with`).
  Neither version needs to be async since nothing is awaited; _quattro_ chooses to be non-async to signal there are no suspension points being hit, match Trio and be a little more readable.
- _quattro_ additionally contains the `move_on_at` and `move_on_after` helpers.
- The _quattro_ versions support getting the current effective deadline.
- The _quattro_ versions can be cancelled manually using `scope.cancel()`, and precancelled before they are entered
- The _quattro_ versions are available on all supported Python versions, not just 3.11+.


## asyncio and Trio differences

`fail_after` and `fail_at` raise `asyncio.Timeout` instead of `trio.Cancelled` exceptions when they fail.

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
