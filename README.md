# **quattro**: Four-wheel drive for asyncio.

[![Documentation](https://img.shields.io/badge/Docs-Read%20The%20Docs-black)](https://quattro.threeofwands.com)
[![License: Apache2](https://img.shields.io/badge/license-Apache2-C06524)](https://github.com/Tinche/uapi/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/quattro.svg)](https://pypi.python.org/pypi/quattro)
[![Build](https://github.com/Tinche/quattro/workflows/CI/badge.svg?branch=main)](https://github.com/Tinche/quattro/actions?workflow=CI)
[![Supported Python versions](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FTinche%2Fquattro%2Fmain%2Fpyproject.toml)](https://github.com/Tinche/quattro)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-green)](https://github.com/Tinche/quattro/actions/workflows/ci.yml)

______________________________________________________________________

**quattro** is a collection of small and powerful components for advanced task control in _asyncio_ applications.

Using _quattro_ gives you:

- elegant context managers for **deadlines and cancellation**: `fail_after`, `fail_at`, `move_on_after` and `move_on_at`.
- a `Deferrer` class and `defer` function to help with **indentation and resource cleanup**, like in Go.
- a TaskGroup subclass with support for **background tasks**.
- a **safer** `gather` implementation.

_quattro_ is influenced by structured concurrency concepts from the [Trio framework](https://trio.readthedocs.io/en/stable/).

## Project Information

- [**PyPI**](https://pypi.org/project/quattro/)
- [**Source Code**](https://github.com/Tinche/quattro)
- [**Documentation**](https://quattro.threeofwands.com)
- [**Changelog**](https://quattro.threeofwands.com/en/latest/changelog.html)

## License

_quattro_ is written by [Tin Tvrtković](https://threeofwands.com/) and distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
