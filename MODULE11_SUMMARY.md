# Module 11: Polymorphic SQLAlchemy Model & Pydantic Schemas

## Summary

Module 11 implements a **SQLAlchemy polymorphic `Calculation` model** with
two operands (`a`, `b`), a **factory** for the four operation types, and
**Pydantic schemas** for validation. Suite: **70 tests, ~95% coverage**.
No BREAD routes yet — those come in Module 12.

## What was added

### 1. Polymorphic model (`app/models/calculation.py`)

Single-table inheritance:

- **Base:** `Calculation` — table `calculations`, discriminator column `type`
- **Subclasses:** `Addition`, `Subtraction`, `Multiplication`, `Division`
- **Fields:** `id (UUID PK)`, `user_id (UUID FK → users.id, CASCADE)`,
  `a (Float)`, `b (Float)`, `type (String)`, `result (Float)`,
  `created_at`, `updated_at`
- **Factory:** `Calculation.create(type, user_id, a, b)` returns the correct
  subclass and stores the computed `result`
- **Template method:** each subclass implements `get_result()`

```python
calc = Calculation.create("addition", user_id, 10, 5)
assert isinstance(calc, Addition)
assert calc.result == 15
```

### 2. Pydantic schemas (`app/schemas/calculation.py`)

- `CalculationType` — enum (addition/subtraction/multiplication/division)
- `CalculationBase` — `type`, `a`, `b` + validators
- `CalculationCreate` — adds `user_id`
- `CalculationUpdate` — `a`, `b` optional
- `CalculationRead` — adds `id`, `result`, `user_id`, timestamps
  (`CalculationResponse` kept as an alias)

Validation: case-insensitive type normalization, unknown-type rejection,
and division-by-zero rejection (LBYL at the API boundary).

### 3. Supporting modules

- `app/database.py` — engine, `SessionLocal`, `Base`, `get_db`
- `app/core/config.py` — Pydantic settings (`DATABASE_URL`)
- `app/models/user.py` — `User` with `calculations` relationship

### 4. Tests

- `tests/integration/test_calculation.py` — model logic + factory (in-memory)
- `tests/integration/test_calculation_schema.py` — schema validation
- `tests/integration/test_calculation_db.py` — **real Postgres**: insert +
  read-back, type round-trip, relationship, CASCADE delete, error cases
- `tests/integration/conftest.py` — DB fixtures (skip if no DB reachable)
- `tests/unit/test_calculator.py`, `test_fastapi_calculator.py`,
  `tests/e2e/` — existing operation + API + e2e tests

## Design patterns

Polymorphic single-table inheritance · Factory · Template Method · DTO ·
Dependency Injection (`get_db`) · LBYL validation.

## Running tests

```bash
pytest tests/unit tests/integration -q                       # no DB needed (DB tests skip)
export DATABASE_URL=postgresql://user:password@localhost:5432/myappdb
pytest tests/integration/test_calculation_db.py -q           # with Postgres
pytest tests/unit tests/integration --cov=app                # coverage
```

## Next (Module 12)

BREAD routes for calculations, full DB-backed API, auth.
