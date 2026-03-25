"""Unit tests for Pydantic models in core.models."""

import pytest
from pydantic import ValidationError

from secoda_analysis_mcp.core.models import (
    FieldFilterOperand,
    LogicalFilterOperand,
    SortConfig,
    SortTieBreaker,
)


class TestFieldFilterOperand:
    def test_exact_operator(self):
        f = FieldFilterOperand(operator="exact", field="native_type", value="table")
        assert f.operator == "exact"
        assert f.field == "native_type"
        assert f.value == "table"

    def test_contains_operator(self):
        f = FieldFilterOperand(operator="contains", field="title", value="order")
        assert f.operator == "contains"

    def test_in_operator_with_list(self):
        f = FieldFilterOperand(operator="in", field="schema", value=["finance", "ops"])
        assert f.value == ["finance", "ops"]

    def test_is_set_operator_with_none_value(self):
        f = FieldFilterOperand(operator="is_set", field="description", value=None)
        assert f.value is None

    def test_invalid_operator_raises(self):
        with pytest.raises(ValidationError):
            FieldFilterOperand(operator="unknown", field="title", value="x")

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            FieldFilterOperand(operator="exact", value="table")  # type: ignore[call-arg]


class TestLogicalFilterOperand:
    def test_and_operator(self):
        op1 = FieldFilterOperand(operator="exact", field="native_type", value="table")
        op2 = FieldFilterOperand(operator="contains", field="title", value="order")
        logical = LogicalFilterOperand(operator="and", operands=[op1, op2])
        assert logical.operator == "and"
        assert len(logical.operands) == 2

    def test_or_operator(self):
        op = FieldFilterOperand(operator="exact", field="verified", value=True)
        logical = LogicalFilterOperand(operator="or", operands=[op])
        assert logical.operator == "or"

    def test_not_operator(self):
        op = FieldFilterOperand(operator="exact", field="native_type", value="column")
        logical = LogicalFilterOperand(operator="not", operands=[op])
        assert logical.operator == "not"

    def test_invalid_operator_raises(self):
        op = FieldFilterOperand(operator="exact", field="title", value="x")
        with pytest.raises(ValidationError):
            LogicalFilterOperand(operator="xor", operands=[op])  # type: ignore[arg-type]

    def test_nested_logical_operands(self):
        inner = FieldFilterOperand(operator="exact", field="native_type", value="table")
        outer = LogicalFilterOperand(
            operator="and",
            operands=[
                inner,
                LogicalFilterOperand(operator="not", operands=[inner]),
            ],
        )
        assert len(outer.operands) == 2


class TestFilterOperandUnion:
    def test_validates_field_filter(self):
        data = {"operator": "exact", "field": "title", "value": "orders"}
        result = FieldFilterOperand.model_validate(data)
        assert isinstance(result, FieldFilterOperand)

    def test_validates_logical_filter(self):
        data = {
            "operator": "and",
            "operands": [
                {"operator": "exact", "field": "native_type", "value": "table"},
                {"operator": "contains", "field": "title", "value": "customer"},
            ],
        }
        result = LogicalFilterOperand.model_validate(data)
        assert isinstance(result, LogicalFilterOperand)
        assert len(result.operands) == 2


class TestSortTieBreaker:
    def test_valid_tie_breaker(self):
        tb = SortTieBreaker(field="created_at", order="desc")
        assert tb.field == "created_at"
        assert tb.order == "desc"

    def test_invalid_order_raises(self):
        with pytest.raises(ValidationError):
            SortTieBreaker(field="created_at", order="random")  # type: ignore[arg-type]


class TestSortConfig:
    def test_simple_sort(self):
        s = SortConfig(field="title", order="asc")
        assert s.field == "title"
        assert s.order == "asc"
        assert s.tie_breaker is None

    def test_sort_with_tie_breaker(self):
        s = SortConfig(
            field="updated_at",
            order="desc",
            tie_breaker=SortTieBreaker(field="created_at", order="desc"),
        )
        assert s.tie_breaker is not None
        assert s.tie_breaker.field == "created_at"

    def test_model_dump_excludes_none_tie_breaker(self):
        s = SortConfig(field="title", order="asc")
        dumped = s.model_dump(exclude_none=True)
        assert "tie_breaker" not in dumped

    def test_invalid_order_raises(self):
        with pytest.raises(ValidationError):
            SortConfig(field="title", order="sideways")  # type: ignore[arg-type]
