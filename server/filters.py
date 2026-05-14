from typing import Any, Literal
from dataclasses import dataclass


@dataclass
class Filter:
    field: str
    operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "contains"]
    value: Any
