# Public API typing

## gather preserves tuple element types

```python
from quattro import gather


async def f() -> int:
    return 1


async def g() -> str:
    return "x"


async def main() -> None:
    result = await gather(f(), g())
    reveal_type(result)  # revealed: tuple[builtins.int, builtins.str]
```

## defer.enable preserves the wrapped coroutine signature

```python
from quattro import defer


@defer.enable
async def run(value: int, name: str) -> str:
    return name * value


reveal_type(run)  # revealed: def (value: builtins.int, name: builtins.str) -> typing.Coroutine[Any, Any, builtins.str]


async def main() -> None:
    await run(2, "a")
    await run("bad", "a")  # error: [arg-type]
```
