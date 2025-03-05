```{currentmodule} quattro
```
# Deferring code

_quattro_ allows you to defer runing async or sync functions until the end of a coroutine's execution.
This keeps code indentation reasonable (and hence more readable) when using context managers, which are a staple of robust resource management.

This functionality is loosely inspired by the [`defer` statement in the Go programming language](https://go.dev/tour/flowcontrol/12).


```{admonition} When and where to use
* Use with context managers (sync and async) that roughly match the coroutine scope, and don't
require error handling on this layer (but, for example, on higher layers).
* Use combined with [`contextlib.aclosing()`](https://docs.python.org/3/library/contextlib.html#contextlib.aclosing) to ensure any async generators are properly closed.
```

## `quattro.Deferrer`

{class}`Deferrer` is a helper class for deferring functions and coroutines.

{class}`Deferrer` can be applied to a coroutine function in the following way:

0. Let's start with a simple coroutine function:

```python
async def my_coroutine_function(a: int) -> str:
    await sleep(1)
    return str(a)
```

1. Add a parameter to your coroutine function.
It should be the first parameter, and not keyword-only.
It can be named whatever you like, but we recommend `defer` for consistency.
The type hint is completely optional.

{emphasize-lines="1,3"}
```python
from quattro import Deferrer

async def my_coroutine_function(defer: Deferrer, a: int) -> str:
    await sleep(1)
    return str(a)
```

2. Apply the {meth}`Deferrer.enable` decorator to the coroutine function.
The decorator is implemented as a class method on the Deferrer class to minimize the number of names you need to import.

{emphasize-lines="3"}
```python
from quattro import Deferrer

@Deferrer.enable
async def my_coroutine_function(defer: Deferrer, a: int) -> str:
    await sleep(1)
    return str(a)
```

3. You're done!
You can use the `defer` parameter in the coroutine body.
Since {class}`Deferrer` implements `__call__`, you can call it directly:

{emphasize-lines="5"}
```python
from quattro import Deferrer

@Deferrer.enable
async def my_coroutine_function(defer: Deferrer, a: int) -> str:
    taskgroup = defer(TaskGroup())
    taskgroup.create_task(some_other_coroutine())
    await sleep(1)
    return str(a)
```

`Deferrer` is a subclass of Python's [`AsyncExitStack`](https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack),
and so supports all of its methods.

{emphasize-lines="5"}
```python
from quattro import Deferrer

@Deferrer.enable
async def my_coroutine_function(defer: Deferrer, a: int) -> str:
    defer.push_async_callback(some_other_coroutine, a)
    return str(a)
```

## `quattro.defer`

{meth}`quattro.defer` is a more magical and more succint version of {class}`quattro.Deferrer`.

```{admonition} When and where to use
When you want to defer with a little less typing, more readability and less type-safety.
```

Apply the {meth}`defer.enable <quattro.defer.enable>` decorator to a coroutine function, and then call {meth}`defer` inside.

```python
from quattro import defer

@defer.enable
async def my_coroutine_function(a: int) -> str:
    defer(TaskGroup())
    await sleep(1)
    return str(a)
```

```{warning}
Do not mix {meth}`defer` and {class}`Deferrer` in the same coroutine function; pick one or the other.
```
