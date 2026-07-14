# app/schemas/calculation.py
"""
Calculation Pydantic Schemas (two-operand: a, b)

Validation and serialization contracts for calculation data at the API
boundary. These act as Data Transfer Objects (DTOs).

Schemas:
- ``CalculationType``  - enum of valid operation types
- ``CalculationBase``  - common fields (a, b, type) + validation
- ``CalculationCreate``- create payload (adds user_id)
- ``CalculationUpdate``- partial update (a, b optional)
- ``CalculationRead``  - read/serialization model (adds id, result, timestamps)

``CalculationResponse`` is kept as an alias of ``CalculationRead`` for
backward compatibility.
"""

from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
)


class CalculationType(str, Enum):
    """Valid calculation types. Inherits ``str`` so values serialize as JSON strings."""
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"


class CalculationBase(BaseModel):
    """
    Common calculation fields shared by create/read schemas.

    Business rules:
    - ``type`` must be one of the four supported operations (case-insensitive).
    - Division requires a non-zero ``b`` (LBYL check at the API boundary).
    """
    type: CalculationType = Field(
        ...,
        description="Type of calculation to perform",
        examples=["addition"],
    )
    a: float = Field(..., description="First operand", examples=[10.5])
    b: float = Field(..., description="Second operand", examples=[3])

    @field_validator("type", mode="before")
    @classmethod
    def validate_type(cls, v):
        """Normalize the type to lowercase and reject unknown values."""
        allowed = {e.value for e in CalculationType}
        if not isinstance(v, str) or v.lower() not in allowed:
            raise ValueError(
                f"Type must be one of: {', '.join(sorted(allowed))}"
            )
        return v.lower()

    @model_validator(mode="after")
    def validate_operands(self) -> "CalculationBase":
        """Reject division by zero before it reaches the model layer."""
        if self.type == CalculationType.DIVISION and self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {"type": "addition", "a": 10.5, "b": 3},
                {"type": "division", "a": 100, "b": 2},
            ]
        },
    )


class CalculationCreate(CalculationBase):
    """
    Payload for creating a calculation.

    ``user_id`` associates the calculation with a user. In a real API this
    typically comes from the authenticated session rather than the body.
    """
    user_id: UUID = Field(
        ...,
        description="UUID of the user who owns this calculation",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "addition",
                "a": 10.5,
                "b": 3,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )


class CalculationUpdate(BaseModel):
    """
    Partial update for a calculation. Operands are optional; type is immutable
    after creation.
    """
    a: Optional[float] = Field(None, description="Updated first operand")
    b: Optional[float] = Field(None, description="Updated second operand")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"a": 42, "b": 7}},
    )


class CalculationRead(CalculationBase):
    """
    Read model returned to clients.

    ``from_attributes=True`` allows populating this directly from a SQLAlchemy
    ``Calculation`` instance. Note that ``user`` and the raw ORM object are not
    exposed - only the safe, serializable fields below.
    """
    id: UUID = Field(..., description="Unique UUID of the calculation")
    user_id: UUID = Field(..., description="UUID of the owning user")
    result: float = Field(..., description="Result of the calculation", examples=[13.5])
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last-update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174999",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "type": "addition",
                "a": 10.5,
                "b": 3,
                "result": 13.5,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00",
            }
        },
    )


# Backward-compatible alias.
CalculationResponse = CalculationRead
