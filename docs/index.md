```{currentmodule} quattro
```
# Welcome to quattro!

*Four-wheel drive for asyncio.*

Release **{sub-ref}`release`**  ([What's new?](https://github.com/Tinche/quattro/blob/main/CHANGELOG.md))

---

```{toctree}
:maxdepth: 1
:caption: "Contents"
:hidden:

self
cancelscopes.md
defer.md
taskgroups.md
gather.md
```

```{toctree}
---
maxdepth: 2
hidden: true
caption: Reference
---

API <modules>
modindex
genindex
```

```{toctree}
---
caption: Meta
hidden: true
maxdepth: 1
---

changelog.md
PyPI <https://pypi.org/project/quattro/>
GitHub <https://github.com/Tinche/quattro>
```

**quattro** is a collection of small and powerful components for advanced task control in _asyncio_ applications.

Using _quattro_ gives you:

- [elegant context managers](cancelscopes.md) for **deadlines and cancellation**: {meth}`fail_after`, {meth}`fail_at`, {meth}`move_on_after` and {meth}`move_on_at`.
- a [`Deferrer` class](defer.md#quattrodeferrer) and [`defer()`](defer.md#quattrodefer) function to help with **indentation and resource cleanup**, like in Go.
- a [TaskGroup subclass](taskgroups.md) with support for **background tasks**.
- a **safer** [`gather()` implementation](gather.md).

_quattro_ is influenced by structured concurrency concepts from the [Trio framework](https://trio.readthedocs.io/en/stable/).
