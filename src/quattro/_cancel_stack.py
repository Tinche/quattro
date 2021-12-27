from contextvars import ContextVar
from typing import Tuple


cancel_stack: ContextVar[Tuple[float, ...]] = ContextVar("_cancel_stack", default=())
