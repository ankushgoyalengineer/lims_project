## 2025-10-23
**Tasks**
- Installed Docker and configured PostgreSQL container.
- Verified FastAPI `/health` endpoint.
- Connected PostgreSQL to FastAPI via SQLAlchemy.
- Created models and applied Alembic migrations.

**Next planned**
- Build CRUD routes for Users and Samples.
- Add authentication (JWT).

**Notes**
- Local database running on 127.0.0.1:5432.

# LIMS Project Log — 2025-10-24

## Changes Made
- Fixed `deps.py` SQLAlchemy query to use `text()` for raw SQL.
- Fixed `Sample` model conflict by renaming `metadata` property to `metadata_json`.
- Updated `samples.py` to include duplicate barcode validation.
- Verified working endpoints:
  - `/users` (user creation)
  - `/token` (authentication)
  - `/samples` (sample creation and listing)
- Confirmed functional database connection to PostgreSQL (lims@127.0.0.1:5432/lims).
- Successfully tested API using PowerShell `Invoke-RestMethod`.

## Current Status
- Server runs cleanly with no startup errors.
- Authentication and authorization confirmed via JWT.
- Duplicate sample prevention implemented.

## Next Planned Step
- Add project module (Projects CRUD + link Samples).
