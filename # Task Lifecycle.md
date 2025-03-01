# Task Lifecycle

Task states may be:
* PENDING - the default, on the class
* FINISHED - set in `set_result` and `set_exception`

When a Task's `.cancel` gets called, the state is still PENDING.

Task calls Future's `set_result` on the step it returns. This changes the state
and _schedules_ callbacks to run on the next loop iteration.

* CANCELLED - only on Future, not on Tasks. When someone calls .cancel() on a _Future_.
