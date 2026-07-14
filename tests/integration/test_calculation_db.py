# tests/integration/test_calculation_db.py
"""
Database integration tests for the Calculation model.

These run against a real PostgreSQL database (see tests/integration/conftest.py).
They verify that records persist correctly, that polymorphic types round-trip,
that the user <-> calculation relationship and CASCADE delete work, and that
invalid data is rejected.

Skipped automatically when no database is reachable.
"""

import uuid
import pytest

from app.models.user import User
from app.models.calculation import (
    Calculation,
    Addition,
    Division,
)


def make_user(db_session):
    """Create and persist a unique user for a test."""
    suffix = uuid.uuid4().hex[:8]
    user = User(username=f"user_{suffix}", email=f"{suffix}@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_insert_and_read_addition(db_session):
    """Insert an Addition and confirm the DB stored the correct data."""
    user = make_user(db_session)
    calc = Calculation.create("addition", user.id, 10, 5)
    db_session.add(calc)
    db_session.commit()

    fetched = db_session.query(Calculation).filter_by(id=calc.id).one()
    assert isinstance(fetched, Addition)          # polymorphic type round-trips
    assert fetched.type == "addition"
    assert fetched.a == 10
    assert fetched.b == 5
    assert fetched.result == 15
    assert fetched.user_id == user.id
    assert fetched.created_at is not None


@pytest.mark.parametrize(
    "calc_type, a, b, expected",
    [
        ("addition", 2, 3, 5),
        ("subtraction", 10, 4, 6),
        ("multiplication", 3, 4, 12),
        ("division", 100, 5, 20),
    ],
)
def test_insert_each_type(db_session, calc_type, a, b, expected):
    """Each operation type persists with the correct stored result."""
    user = make_user(db_session)
    calc = Calculation.create(calc_type, user.id, a, b)
    db_session.add(calc)
    db_session.commit()

    fetched = db_session.query(Calculation).filter_by(id=calc.id).one()
    assert fetched.type == calc_type
    assert fetched.result == expected


def test_user_relationship(db_session):
    """user.calculations reflects inserted rows via the relationship."""
    user = make_user(db_session)
    db_session.add(Calculation.create("addition", user.id, 1, 2))
    db_session.add(Calculation.create("multiplication", user.id, 3, 4))
    db_session.commit()
    db_session.refresh(user)
    assert len(user.calculations) == 2


def test_cascade_delete(db_session):
    """Deleting a user removes their calculations (CASCADE)."""
    user = make_user(db_session)
    calc = Calculation.create("addition", user.id, 1, 2)
    db_session.add(calc)
    db_session.commit()
    calc_id = calc.id

    db_session.delete(user)
    db_session.commit()
    assert db_session.query(Calculation).filter_by(id=calc_id).first() is None


def test_error_invalid_type(db_session):
    """The factory rejects an unsupported calculation type."""
    user = make_user(db_session)
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create("modulus", user.id, 10, 3)


def test_error_division_by_zero(db_session):
    """Division by zero is rejected before persistence."""
    user = make_user(db_session)
    with pytest.raises(ValueError, match="Cannot divide by zero."):
        Calculation.create("division", user.id, 10, 0)


def test_missing_operand_rejected(db_session):
    """NOT NULL on operand b is enforced by the database."""
    from sqlalchemy.exc import IntegrityError
    user = make_user(db_session)
    bad = Division(user_id=user.id, a=10, b=None)
    db_session.add(bad)
    with pytest.raises(IntegrityError):
        db_session.commit()
