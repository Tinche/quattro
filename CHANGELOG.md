```{currentmodule} quattro
```
# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [_Calendar Versioning_](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

<!-- changelog follows -->

## 25.2.0 (2025-03-06)

- Introduce {class}`Deferrer` and {meth}`defer`.
  ([#18](https://github.com/Tinche/quattro/pull/18))
- _quattro_ documentation is now handled by Sphinx and Read the Docs.
  ([#19](https://github.com/Tinche/quattro/pull/19))

## 25.1.1 (2025-02-24)

- Change a `sys.version_info` guard to work better with Pyright.
  ([#17](https://github.com/Tinche/quattro/pull/17))

## 25.1.0 (2025-02-21)

- TaskGroups now support background tasks via {meth}`TaskGroup.create_background_task`.
  ([#10](https://github.com/Tinche/quattro/pull/10))
- Add support for Python 3.13.
  ([#9](https://github.com/Tinche/quattro/pull/9))
- Depend on the [_taskgroup_ package](https://pypi.org/project/taskgroup/) on Python 3.9 and 3.10, instead of our own implementation.
  ([#11](https://github.com/Tinche/quattro/pull/11))
- Switch to [uv](https://github.com/astral-sh/uv).
  ([#14](https://github.com/Tinche/quattro/pull/14))
- Introduce [Zizmor](https://github.com/woodruffw/zizmor) for CI hardening.
  ([#12](https://github.com/Tinche/quattro/pull/12))
- _quattro_ now has 100% branch coverage.
  ([#16](https://github.com/Tinche/quattro/pull/16))

## 24.1.0 (2024-05-01)

- Add Trove classifiers.
- Add `name` keyword-only parameter to {meth}`TaskGroup.create_task`.
  ([#8](https://github.com/Tinche/quattro/pull/8))

## 23.1.0 (2023-11-29)

- Introduce {meth}`quattro.gather`.
  ([#5](https://github.com/Tinche/quattro/pull/5))
- Add support for Python 3.12.
- Switch to [PDM](https://pdm.fming.dev/latest/).

## 22.2.0 (2022-12-27)

- More robust nested cancellation on 3.11.
- Better typing support for {meth}`fail_after` and {meth}`fail_at`.
- Improve effective deadline handling for pre-cancelled scopes.
- TaskGroups now support custom ContextVar contexts when creating tasks, just like the standard library implementation.

## 22.1.0 (2022-12-19)

- Restore TaskGroup copyright notice.
- TaskGroups now raise ExceptionGroups (using the PyPI backport when necessary) on child errors.
- Add support for Python 3.11, drop 3.8.
- TaskGroups no longer have a `name` and the `repr` is slightly different, to harmonize with the Python 3.11 standard library implementation.
- TaskGroups no longer swallow child exceptions when aborting, to harmonize with the Python 3.11 standard library implementation.
- Switch to CalVer.

## 0.3.0 (2022-01-08)

- Add `py.typed` to enable typing information.
- Flesh out type annotations for TaskGroups.

## 0.2.0 (2021-12-27)

- Add {meth}`quattro.current_effective_deadline`.

## 0.1.0 (2021-12-08)

- Initial release, containing task groups and cancellation scopes.
