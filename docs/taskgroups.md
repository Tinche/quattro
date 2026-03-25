# TaskGroups

_quattro_ contains a [TaskGroup](https://docs.python.org/3/library/asyncio-task.html#task-groups) subclass with support for background tasks.
TaskGroups are inspired by [Trio nurseries](https://trio.readthedocs.io/en/stable/reference-core.html#nurseries-and-spawning).

```{admonition} When and where to use
Use to avoid tedious, manual handling and cancellation of backgroup tasks if you have them.
Use to avoid manual handling of semaphores when tasks need to run with limited parallelism.
```

```python
from quattro import TaskGroup

async def my_handler():
    # We want to spawn some tasks, and ensure they are all handled before we return.
    async def task_1():
        ...

    async def task_2():
        ...

    async def background_task():
        ...

    async with TaskGroup() as tg:
        t1 = tg.create_task(task_1)
        t2 = tg.create_task(task_2)
        tg.create_background_task(background_task)

    # The end of the `async with` block awaits the non-background tasks, ensuring they are handled.
    # The background task gets cancelled instead.
```

TaskGroups are essential building blocks for achieving the concept of [structured concurrency](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/).
In simple terms, structured concurrency means your code does not leak tasks - when a coroutine
finishes, all tasks spawned by that coroutine and all its children are also finished.
(In fancy terms, the execution flow becomes a directed acyclic graph.)

Structured concurrency can be achieved by using TaskGroups instead of `asyncio.create_task` to start background tasks.
TaskGroups essentially do two things:

- when exiting from a TaskGroup `async with` block, the TaskGroup awaits all of its children, ensuring they are finished when it exits
- when a TaskGroup child task raises an exception, all other children and the task inside the context manager are cancelled

You can also pass `concurrency_limit` to cap how many non-background tasks from the group can execute simultaneously.
Background tasks created with `create_background_task()` are not counted against that limit.

```python
async with TaskGroup(concurrency_limit=10) as tg:
    for item in items:
        tg.create_task(process(item))
```

## Background Tasks

_quattro_ TaskGroups can be used to start _background tasks_.
Background tasks are different than normal tasks in that they do not block an exit from the TaskGroup if they aren't finished.
Instead, any running background tasks are cancelled at the time of exit.
Background tasks are useful for auxiliary tasks that support a main task, for example pumping events between queues.
An unhandled error in a background task will still abort the entire TaskGroup.
