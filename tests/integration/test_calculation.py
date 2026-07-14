# tests/integration/test_calculation.py
"""
Unit-level tests for the polymorphic Calculation models (two-operand: a, b).

These exercise the calculation logic and the factory in memory (no database).
Real database persistence is covered separately in test_calculation_db.py.
"""

import uuid
import pytest

from app.models.calculation import (
    Calculation,
    Addition,
    Subtraction,
    Multiplication,
    Division,
)


def dummy_user_id():
    """Random UUID standing in for a real user id in in-memory tests."""
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Individual operation results
# ---------------------------------------------------------------------------

def test_addition_get_result():
    calc = Addition(user_id=dummy_user_id(), a=10, b=5)
    assert calc.get_result() == 15


def test_subtraction_get_result():
    calc = Subtraction(user_id=dummy_user_id(), a=20, b=5)
    assert calc.get_result() == 15


def test_multiplication_get_result():
    calc = Multiplication(user_id=dummy_user_id(), a=3, b=4)
    assert calc.get_result() == 12


def test_division_get_result():
    calc = Division(user_id=dummy_user_id(), a=100, b=5)
    assert calc.get_result() == 20


def test_division_by_zero():
    calc = Division(user_id=dummy_user_id(), a=50, b=0)
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        calc.get_result()


# ---------------------------------------------------------------------------
# Factory pattern: correct subclass selection + stored result
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "calc_type, cls, a, b, expected",
    [
        ("addition", Addition, 1, 2, 3),
        ("subtraction", Subtraction, 10, 4, 6),
        ("multiplication", Multiplication, 3, 4, 12),
        ("division", Division, 100, 5, 20),
    ],
)
def test_factory_returns_correct_subclass(calc_type, cls, a, b, expected):
    calc = Calculation.create(calc_type, dummy_user_id(), a, b)
    assert isinstance(calc, cls)
    assert isinstance(calc, Calculation)
    # Factory computes and stores the result.
    assert calc.result == expected
    assert calc.get_result() == expected


def test_factory_invalid_type():
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create("modulus", dummy_user_id(), 10, 3)


def test_factory_case_insensitive():
    for calc_type in ["addition", "Addition", "ADDITION", "AdDiTiOn"]:
        calc = Calculation.create(calc_type, dummy_user_id(), 5, 3)
        assert isinstance(calc, Addition)
        assert calc.result == 8


def test_factory_division_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        Calculation.create("division", dummy_user_id(), 10, 0)


# ---------------------------------------------------------------------------
# Polymorphic behavior
# ---------------------------------------------------------------------------

def test_polymorphic_list_of_calculations():
    user_id = dummy_user_id()
    calculations = [
        Calculation.create("addition", user_id, 1, 2),
        Calculation.create("subtraction", user_id, 10, 3),
        Calculation.create("multiplication", user_id, 2, 4),
        Calculation.create("division", user_id, 100, 5),
    ]
    assert isinstance(calculations[0], Addition)
    assert isinstance(calculations[1], Subtraction)
    assert isinstance(calculations[2], Multiplication)
    assert isinstance(calculations[3], Division)
    assert [c.get_result() for c in calculations] == [3, 7, 8, 20]


def test_polymorphic_method_calling():
    user_id = dummy_user_id()
    cases = [
        ("addition", 12),
        ("subtraction", 8),
        ("multiplication", 20),
        ("division", 5),
    ]
    for calc_type, expected in cases:
        calc = Calculation.create(calc_type, user_id, 10, 2)
        assert calc.get_result() == expected


def test_base_get_result_not_implemented():
    """The base Calculation must not implement get_result()."""
    base = Calculation(user_id=dummy_user_id(), a=1, b=2)
    with pytest.raises(NotImplementedError):
        base.get_result()
