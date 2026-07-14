# Module 11 — Reflection

## What I built

For this module I implemented a **polymorphic SQLAlchemy `Calculation` model**
using single-table inheritance. One `calculations` table holds a `type`
discriminator column, and four subclasses — `Addition`, `Subtraction`,
`Multiplication`, and `Division` — each implement `get_result()` for their own
operation over two operands, `a` and `b`. A **factory method**,
`Calculation.create(type, user_id, a, b)`, returns the correct subclass and
stores the computed `result`, so object creation lives in one place and adding
a new operation only means adding a subclass.

On top of the model I wrote **Pydantic schemas** that act as Data Transfer
Objects: `CalculationCreate` validates incoming `a`, `b`, `type`, and
`user_id`; `CalculationRead` serializes the record back out with `id`,
`result`, and timestamps; and `CalculationUpdate` allows partial edits.
Validation covers unknown operation types and rejects division by zero before
it ever reaches the database. The `Calculation` model also has a foreign key to
`users.id` with `ON DELETE CASCADE`, plus the matching relationship on `User`.

## Testing

I split the tests into three layers:

- **Unit / logic tests** exercise each operation and the factory in memory —
  confirming the factory picks the right subclass, that types are
  case-insensitive, and that invalid input is rejected by the schemas.
- **Database integration tests** run against a **real PostgreSQL** database
  (the GitHub Actions service container). They insert a calculation, read it
  back, confirm the polymorphic type round-trips, verify the user relationship
  and `CASCADE` delete, and check error cases (invalid type, division by zero,
  a `NULL` operand rejected by the database).
- **End-to-end tests** drive the running FastAPI app through a real browser
  with Playwright.

The final suite is **70 tests with ~95% coverage**, and the DB tests skip
cleanly when no database is reachable so the suite still runs locally without
Postgres.

## Challenges faced

- **Refactoring the model to two operands.** The model started out storing a
  variable-length list of inputs. The assignment specifies `a` and `b`, so I
  reworked the model, the schemas, and every test to a clean two-operand shape
  while keeping the polymorphic inheritance and the factory intact.
- **Wiring the database into CI.** The integration tests needed to reach the
  Postgres service container in GitHub Actions. I had to set `DATABASE_URL`
  in the workflow to match the service credentials and build a
  transaction-rollback fixture so each test stays isolated and leaves no state
  behind.
- **The security scan (Trivy) failing the build.** The pipeline's Trivy stage
  failed on `HIGH`/`CRITICAL` CVEs in outdated dependencies (`h11`,
  `starlette`, `urllib3`, and others). I upgraded the pinned packages to their
  patched versions — which cascaded into bumping `fastapi`, `httpcore`, and
  `httpx` — then re-ran the tests to make sure nothing broke.
- **A breaking change from the dependency upgrade.** Bumping Starlette changed
  the `TemplateResponse` signature, which broke the `/` route and made the
  end-to-end server fail to start. Tracking that down from a
  `TypeError: unhashable type: 'dict'` and fixing the call to the new
  `(request, name)` signature was a good reminder that dependency upgrades need
  their own round of testing.

## What I learned

- How **polymorphic single-table inheritance** works in SQLAlchemy and how the
  discriminator column drives which subclass is returned from a query.
- How the **factory** and **template-method** patterns keep the data layer
  extensible and put creation logic in one place.
- How **Pydantic schemas** enforce validation at the API boundary before bad
  data can reach the model or the database.
- How the full **CI/CD pipeline** fits together: run every test layer against a
  real database, scan the built image for vulnerabilities, and only then push
  to Docker Hub — and how a failure in any one stage blocks the release.

## Screenshots

### GitHub Actions — successful workflow run

_Paste screenshot below (test + security + deploy all green):_

<!-- ![GitHub Actions successful run](docs/screenshots/github-actions.png) -->



### Docker Hub — image pushed

_Paste screenshot below (public `aayushrox007/module11_is601` repo with the pushed tag):_

<!-- ![Docker Hub image](docs/screenshots/docker-hub.png) -->


