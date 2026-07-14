# Module 11 — Reflection

> Fill in the bracketed prompts with your own words before submitting. The
> notes below summarize what was built so you can speak to it accurately.

## What I built

- A **polymorphic SQLAlchemy `Calculation` model** using single-table
  inheritance. One `calculations` table holds a `type` discriminator column;
  `Addition`, `Subtraction`, `Multiplication`, and `Division` subclasses each
  implement `get_result()` for their own operation over two operands `a` and `b`.
- A **factory** (`Calculation.create(type, user_id, a, b)`) that returns the
  correct subclass and stores the computed `result`.
- **Pydantic schemas** as DTOs: `CalculationCreate` (validates incoming `a`,
  `b`, `type` + `user_id`), `CalculationRead` (serializes `id, a, b, type,
  result`, timestamps), and `CalculationUpdate`. Validation covers unknown
  types and division-by-zero.
- A **foreign key** from `calculations.user_id` to `users.id` with
  `ON DELETE CASCADE`, plus the reverse relationship on `User`.

## Testing

- **Unit / logic tests** (`tests/integration/test_calculation.py`,
  `test_calculation_schema.py`): each operation, the factory's subclass
  selection, case-insensitive types, and schema rejection of invalid input.
- **Database integration tests** (`tests/integration/test_calculation_db.py`):
  insert a record into PostgreSQL and read it back, confirm the polymorphic
  type round-trips, verify the user relationship and CASCADE delete, and check
  error cases (invalid type, division by zero, NOT NULL operand).
- Result: **70 tests passing, ~95% coverage.** DB tests skip cleanly when no
  database is reachable, so the suite still runs without Postgres locally.

## Challenges faced

- [Describe a challenge — e.g. wiring the `@declared_attr` mixin so the shared
  columns applied correctly to the polymorphic base and subclasses.]
- [Describe a CI/CD challenge — e.g. pointing `DATABASE_URL` at the Actions
  Postgres service container, or configuring Docker Hub secrets.]
- [Describe a testing challenge — e.g. isolating DB tests with a
  transaction-rollback fixture so they don't leak state.]

## What I learned

- [Your takeaways on polymorphic inheritance, the factory pattern, Pydantic
  validation, and the test → build → scan → deploy pipeline.]

## Screenshots (attach before submitting)

1. **GitHub Actions** — a successful workflow run (test + security + deploy).
2. **Docker Hub** — the pushed image in your repository.
