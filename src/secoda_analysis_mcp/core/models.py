from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field

# --------------------------------
# Filter and Sort Models for list_resources
# --------------------------------


class FieldFilterOperand(BaseModel):
    """Field-level filter operand for filtering resources by specific field values.

    Examples:
        - Exact match: {"operator": "exact", "field": "native_type", "value": "table"}
        - Contains: {"operator": "contains", "field": "title", "value": "customer"}
        - In list: {"operator": "in", "field": "schema", "value": ["dbt_finance", "dbt_ops"]}
        - Is set: {"operator": "is_set", "field": "description", "value": None}

    """

    operator: Literal["exact", "contains", "in", "is_set"] = Field(
        ..., description="Field operator type"
    )
    field: str = Field(..., description="Field name to filter on")
    value: Any = Field(..., description="Value to filter by (None for is_set)")


class LogicalFilterOperand(BaseModel):
    """Logical filter operand for combining multiple filters with AND/OR/NOT logic.

    Examples:
        - AND: {"operator": "and", "operands": [operand1, operand2]}
        - OR: {"operator": "or", "operands": [operand1, operand2]}
        - NOT: {"operator": "not", "operands": [operand1]}

    """

    operator: Literal["and", "or", "not"] = Field(..., description="Logical operator type")
    operands: List["FilterOperand"] = Field(..., description="List of filter operands to combine")


# Union type for filter operands (can be field or logical)
FilterOperand = Union[FieldFilterOperand, LogicalFilterOperand]

# Rebuild model to resolve forward references
LogicalFilterOperand.model_rebuild()


class SortTieBreaker(BaseModel):
    """Tie breaker configuration for sorting when primary sort field has equal values.

    Example:
        {"field": "created_at", "order": "desc"}

    """

    field: str = Field(..., description="Field name to use for tie breaking")
    order: Literal["asc", "desc"] = Field(..., description="Sort order (ascending or descending)")


class SortConfig(BaseModel):
    """Sort configuration for ordering results.

    Examples:
        - Simple: {"field": "title", "order": "asc"}
        - With tie breaker: {
            "field": "updated_at",
            "order": "desc",
            "tie_breaker": {"field": "created_at", "order": "desc"}
          }

    """

    field: str = Field(..., description="Field name to sort by")
    order: Literal["asc", "desc"] = Field(..., description="Sort order (ascending or descending)")
    tie_breaker: Optional[SortTieBreaker] = Field(
        None, description="Optional tie breaker for equal values"
    )
