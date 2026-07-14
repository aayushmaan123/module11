# tests/integration/test_calculation_schema.py
"""
Tests for the Calculation Pydantic schemas (two-operand: a, b).

Covers valid data acceptance, invalid-data rejection, type normalization,
division-by-zero validation, and the create/update/read schemas.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationType,
    CalculationBase,
    CalculationCreate,
    CalculationUpdate,
    CalculationRead,
    CalculationResponse,
)


# ---------------------------------------------------------------------------
# CalculationType enum
# ---------------------------------------------------------------------------

def test_calculation_type_enum_values():
    assert CalculationType.ADDITION.value == "addition"
    assert CalculationType.SUBTRACTION.value == "subtraction"
    assert CalculationType.MULTIPLICATION.value == "multiplication"
    assert CalculationType.DIVISION.value == "division"


# ---------------------------------------------------------------------------
# CalculationBase
# ---------------------------------------------------------------------------

def test_base_valid_addition():
    calc = CalculationBase(type="addition", a=10.5, b=3)
    assert calc.type == CalculationType.ADDITION
    assert calc.a == 10.5
    assert calc.b == 3


def test_base_case_insensitive_type():
    for variant in ["Addition", "ADDITION", "AdDiTiOn"]:
        calc = CalculationBase(type=variant, a=1, b=2)
        assert calc.type == CalculationType.ADDITION


def test_base_invalid_type():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="modulus", a=10, b=3)
    assert any("Type must be one of" in str(e) for e in exc.value.errors())


def test_base_missing_operand():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="addition", a=10)  # b missing
    assert any(e["loc"] == ("b",) for e in exc.value.errors())


def test_base_non_numeric_operand():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", a="not-a-number", b=3)


def test_base_division_by_zero():
    with pytest.raises(ValidationError) as exc:
        CalculationBase(type="division", a=100, b=0)
    assert any("Cannot divide by zero" in str(e) for e in exc.value.errors())


def test_base_division_nonzero_ok():
    calc = CalculationBase(type="division", a=100, b=5)
    assert calc.b == 5


def test_base_zero_numerator_ok():
    """Zero as the numerator (a) is valid; only b must be non-zero."""
    calc = CalculationBase(type="division", a=0, b=5)
    assert calc.a == 0


def test_base_negative_operands_ok():
    calc = CalculationBase(type="subtraction", a=-5, b=-10)
    assert calc.a == -5 and calc.b == -10


# ---------------------------------------------------------------------------
# CalculationCreate
# ---------------------------------------------------------------------------

def test_create_valid():
    user_id = uuid4()
    calc = CalculationCreate(type="multiplication", a=2, b=3, user_id=str(user_id))
    assert calc.type == CalculationType.MULTIPLICATION
    assert calc.user_id == user_id


def test_create_missing_user_id():
    with pytest.raises(ValidationError) as exc:
        CalculationCreate(type="addition", a=1, b=2)
    assert any("user_id" in str(e) for e in exc.value.errors())


def test_create_invalid_user_id():
    with pytest.raises(ValidationError):
        CalculationCreate(type="subtraction", a=10, b=5, user_id="not-a-uuid")


def test_create_division_by_zero():
    with pytest.raises(ValidationError) as exc:
        CalculationCreate(type="division", a=10, b=0, user_id=str(uuid4()))
    assert any("Cannot divide by zero" in str(e) for e in exc.value.errors())


# ---------------------------------------------------------------------------
# CalculationUpdate
# ---------------------------------------------------------------------------

def test_update_valid():
    calc = CalculationUpdate(a=42, b=7)
    assert calc.a == 42 and calc.b == 7


def test_update_all_fields_optional():
    calc = CalculationUpdate()
    assert calc.a is None and calc.b is None


# ---------------------------------------------------------------------------
# CalculationRead
# ---------------------------------------------------------------------------

def test_read_valid():
    calc = CalculationRead(
        id=str(uuid4()),
        user_id=str(uuid4()),
        type="addition",
        a=10,
        b=5,
        result=15.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert calc.result == 15.0
    assert calc.type == CalculationType.ADDITION


def test_read_missing_result():
    with pytest.raises(ValidationError) as exc:
        CalculationRead(
            id=str(uuid4()),
            user_id=str(uuid4()),
            type="multiplication",
            a=2,
            b=3,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    assert any("result" in str(e) for e in exc.value.errors())


def test_response_alias_is_read():
    assert CalculationResponse is CalculationRead
