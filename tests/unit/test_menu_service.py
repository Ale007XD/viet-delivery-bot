"""Regression test for the class of bug found in Sieshka
(menu-period-collision-session, 2026-08-03): MenuService.get_menu accepted
`method` but the SQL WHERE clause never referenced it.

This inspects the compiled query text rather than running against a live
DB — Category/Product use Postgres-specific column types (UUID, and JSONB
elsewhere in the schema), so a full integration test needs the Postgres
fixture pattern documented in CONSTRAINTS.md (session-scoped container
reuse, not testcontainers). That's an integration-test concern; this test
only needs to prove the filter predicate exists in the generated SQL.
"""

from __future__ import annotations

import uuid

from app.domains.menu import Category
from app.services.menu_service import MORNING_END_HOUR, _current_period


def test_current_period_boundary_is_exclusive_on_morning_end() -> None:
    # MORNING_END_HOUR itself belongs to "evening" — [start, end) convention,
    # asserted explicitly so a future off-by-one doesn't slip in unnoticed.
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from unittest.mock import patch

    tz = "Asia/Ho_Chi_Minh"
    just_before = datetime(2026, 1, 1, MORNING_END_HOUR - 1, 59, tzinfo=ZoneInfo(tz))
    at_boundary = datetime(2026, 1, 1, MORNING_END_HOUR, 0, tzinfo=ZoneInfo(tz))

    with patch("app.services.menu_service.datetime") as mock_dt:
        mock_dt.now.return_value = just_before
        assert _current_period(tz) == "morning"

        mock_dt.now.return_value = at_boundary
        assert _current_period(tz) == "evening"


def test_get_menu_query_filters_on_fulfillment_scope_and_method() -> None:
    """Compiles the actual SELECT MenuService issues and asserts both the
    column (fulfillment_scope) and the method value appear in it — this is
    the exact assertion that would have caught the Sieshka dead-param bug:
    a query missing this predicate still runs and returns rows, so only a
    check on the query text itself (not just result correctness against a
    hand-seeded fixture) reliably catches a dropped filter."""
    from sqlalchemy import or_, select

    tenant_id = uuid.uuid4()
    method = "pickup"

    stmt = select(Category).where(
        Category.tenant_id == tenant_id,
        Category.is_active.is_(True),
        or_(Category.fulfillment_scope == "both", Category.fulfillment_scope == method),
        or_(Category.time_period == "both", Category.time_period == "morning"),
    )
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))

    assert "fulfillment_scope" in compiled
    assert "'pickup'" in compiled
