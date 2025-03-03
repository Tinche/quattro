# Welcome to quattro!

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

_quattro_ is a powerful toolkit for writing robust and readable asyncio code on Python 3.9 and later.

_quattro_ is a collection of mostly independent building blocks:

* [Cancel scopes](cancelscopes.md), for easy and robust deadlines and timeouts.
* [Defer tools](defer.md), for robust and readable handling of resources.
* [TaskGroups](taskgroups.md), for structured concurrency.
* A safer [`gather` implementation](gather.md), for concurrent requests.
