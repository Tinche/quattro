```{currentmodule} quattro
```
# Deferring code

_quattro_ allows you to defer runing async or sync functions until the end of a coroutine's execution.
This keeps code indentation reasonable (and hence more readable) when using context managers, which are a staple of robust resource management.

This functionality is loosely inspired by the [`defer` statement in the Go programming language](https://go.dev/tour/flowcontrol/12).


```{admonition} When and where to use
* Use with context managers (sync and async) that roughly match the coroutine scope, and don't
require error handling on this layer (but, for example, on higher layers).
* Use combined with [`contextlib.aclosing`](https://docs.python.org/3/library/contextlib.html#contextlib.aclosing) to ensure any async generators are properly closed.
```

# `quattro.Defer`

{class}`Defer` is a helper class for deferring functions and coroutines.

`Defer` can be applied to a coroutine function in the following way:

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

```python
from quattro import Defer

async def my_coroutine_function(defer: Defer, a: int) -> str:
    await sleep(1)
    return str(a)
```

2. Apply the {meth}`Defer.enable` decorator to the coroutine function.
The decorator is implemented as a class method on the Defer class to minimize the number of names you need to import.

```python
from quattro import Defer

@Defer.enable
async def my_coroutine_function(defer: Defer, a: int) -> str:
    await sleep(1)
    return str(a)
```

3. You're done!
You can use the `defer` parameter in the coroutine body.
Since {class}`Defer` implements `__call__`, you can call it directly:

```python
from quattro import Defer

@Defer.defer
async def my_coroutine_function(defer: Defer, a: int) -> str:
    taskgroup = defer(TaskGroup())
    taskgroup.create_task(some_other_coroutine())
    await sleep(1)
    return str(a)
```

`Defer` is a subclass of Python's [`AsyncExitStack`](https://docs.python.org/3/library/contextlib.html#contextlib.AsyncExitStack),
and so supports all of its methods.

```python
from quattro import Defer

@Defer.defer
async def my_coroutine_function(defer: Defer, a: int) -> str:
    defer.push_async_callback(some_other_coroutine, a)
    return str(a)
```
