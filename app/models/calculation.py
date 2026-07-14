# app/models/calculation.py
"""
Calculation Models with Polymorphic Inheritance (two-operand: a, b)

This module defines a Calculation model using SQLAlchemy single-table
polymorphic inheritance. A base ``Calculation`` model stores two operands
``a`` and ``b`` plus a ``type`` discriminator, and four subclasses
(``Addition``, ``Subtraction``, ``Multiplication``, ``Division``) each
implement ``get_result()`` for their specific operation.

Design patterns demonstrated:
- Polymorphic single-table inheritance (``type`` discriminator column)
- Factory pattern (``Calculation.create()`` returns the right subclass and
  stores the computed ``result``)
- Template method (``get_result()`` defined on the base, implemented by
  each subclass)

Fields (per assignment spec): id, user_id (FK), a, b, type, result.
"""

from datetime import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base


class AbstractCalculation:
    """
    Mixin defining columns shared by every calculation type.

    Uses ``@declared_attr`` so the columns can live on a mixin and be applied
    to the mapped ``Calculation`` class and its subclasses.
    """

    @declared_attr
    def __tablename__(cls):
        """All calculation types share the 'calculations' table."""
        return 'calculations'

    @declared_attr
    def id(cls):
        """Unique identifier for each calculation (UUID)."""
        return Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False
        )

    @declared_attr
    def user_id(cls):
        """
        Foreign key to the owning user.

        CASCADE delete removes calculations when their user is deleted.
        Indexed to speed up filtering by user.
        """
        return Column(
            UUID(as_uuid=True),
            ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            index=True
        )

    @declared_attr
    def type(cls):
        """
        Discriminator column for polymorphic inheritance.

        Values: 'addition', 'subtraction', 'multiplication', 'division'.
        """
        return Column(
            String(50),
            nullable=False,
            index=True
        )

    @declared_attr
    def a(cls):
        """First operand."""
        return Column(Float, nullable=False)

    @declared_attr
    def b(cls):
        """Second operand."""
        return Column(Float, nullable=False)

    @declared_attr
    def result(cls):
        """
        The computed result.

        Stored on creation by the factory. Nullable so a record can exist
        before the result is computed.
        """
        return Column(Float, nullable=True)

    @declared_attr
    def created_at(cls):
        """Timestamp when the calculation was created."""
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def updated_at(cls):
        """Timestamp when the calculation was last updated."""
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False
        )

    @declared_attr
    def user(cls):
        """Bidirectional relationship to the owning User."""
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID,
               a: float, b: float) -> "Calculation":
        """
        Factory: build the correct Calculation subclass and store its result.

        Args:
            calculation_type: One of 'addition', 'subtraction',
                'multiplication', 'division' (case-insensitive).
            user_id: UUID of the owning user.
            a: First operand.
            b: Second operand.

        Returns:
            A subclass instance with ``result`` already computed.

        Raises:
            ValueError: If the type is unsupported, or the operation is
                invalid (e.g. division by zero).

        Example:
            calc = Calculation.create('addition', user_id, 2, 3)
            assert isinstance(calc, Addition)
            assert calc.result == 5
        """
        calculation_classes = {
            'addition': Addition,
            'subtraction': Subtraction,
            'multiplication': Multiplication,
            'division': Division,
        }
        calculation_class = calculation_classes.get(calculation_type.lower())
        if not calculation_class:
            raise ValueError(
                f"Unsupported calculation type: {calculation_type}"
            )
        obj = calculation_class(user_id=user_id, a=a, b=b)
        # Store the result so it is persisted with the record.
        obj.result = obj.get_result()
        return obj

    def get_result(self) -> float:
        """
        Compute the result. Each subclass overrides this.

        Raises:
            NotImplementedError: If called on the base class.
        """
        raise NotImplementedError(
            "Subclasses must implement get_result() method"
        )

    def __repr__(self):
        return (
            f"<Calculation(type={self.type}, a={self.a}, b={self.b}, "
            f"result={self.result})>"
        )


class Calculation(Base, AbstractCalculation):
    """
    Base calculation model with polymorphic configuration.

    - ``polymorphic_on``: the ``type`` discriminator column
    - ``polymorphic_identity``: the value stored for the base class
    """
    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "calculation",
    }


class Addition(Calculation):
    """Addition: a + b."""
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self) -> float:
        return self.a + self.b


class Subtraction(Calculation):
    """Subtraction: a - b."""
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self) -> float:
        return self.a - self.b


class Multiplication(Calculation):
    """Multiplication: a * b."""
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self) -> float:
        return self.a * self.b


class Division(Calculation):
    """
    Division: a / b.

    Guards against division by zero (LBYL check before dividing).
    """
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self) -> float:
        if self.b == 0:
            raise ValueError("Cannot divide by zero.")
        return self.a / self.b
