"""
Thin HTTP client for the UK Companies House "public data" API.

Auth: HTTP Basic Auth, API key as the username, empty-string password.
Base host: https://api.company-information.service.gov.uk

Two entry points are exposed:
  - search_companies(...): wraps GET /advanced-search/companies
  - get_company_details(company_number): wraps GET /company/{company_number}

Design notes (deliberate, see docs/06-mcp-payload-audit.md for the full audit):
  - Single-pass, no retries. A failed call returns a clear error dict; it never
    raises up through the MCP tool layer and never retries automatically.
  - search_companies caps `size` at 20 — this is a quick competitive scan for
    an analyst, not a bulk-export / pagination tool. No second-page fetching.
  - get_company_details computes "days overdue" itself in Python rather than
    leaving that inference to the calling model. Companies House only gives a
    due date + a boolean `overdue` flag; we turn that into a concrete number
    when it's true, and null/0 otherwise (see _days_overdue docstring).
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Any

import httpx

BASE_URL = "https://api.company-information.service.gov.uk"
SEARCH_PATH = "/advanced-search/companies"
COMPANY_PATH = "/company/{company_number}"

MAX_SEARCH_SIZE = 20

# Filing types where Companies House does not require turnover / profit /
# headcount to be disclosed. If a company's last accounts were filed under one
# of these, we surface a financials_note so the model doesn't infer numbers
# that simply aren't on the public register.
SMALL_FILING_TYPES = {
    "micro-entity",
    "dormant",
    "abridged",
    "audited-abridged",
    "unaudited-abridged",
}

FINANCIALS_NOTE_TEXT = (
    "Turnover, profit and headcount are not required in this filing type and "
    "are not available from this register."
)

# Companies House's own API sometimes returns the literal string "null"
# (not JSON null) as accounts.last_accounts.type — observed on companies
# dissolved before ever filing a set of accounts. Treat it as "no accounts
# filed", not as a real filing-type value.
NO_ACCOUNTS_FILED_NOTE_TEXT = (
    "No accounts have ever been filed for this company, so no financial "
    "figures are available from this register."
)


def _get_api_key() -> str:
    """Read the API key from the environment at call time.

    Never logged, never returned, never embedded in any response — only used
    as the HTTP Basic Auth username for the outbound request.
    """
    api_key = os.environ.get("COMPANIES_HOUSE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COMPANIES_HOUSE_API_KEY is not set in the environment. "
            "Set it in .env (local) or via Secret Manager env injection (Cloud Run)."
        )
    return api_key


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_address(addr: dict | None) -> str:
    if not addr:
        return ""
    parts = [
        addr.get("address_line_1"),
        addr.get("address_line_2"),
        addr.get("locality"),
        addr.get("region"),
        addr.get("postal_code"),
        addr.get("country"),
    ]
    return ", ".join(p for p in parts if p)


def _days_overdue(due_on: str | None) -> tuple[int | None, str | None]:
    """Compute an overdue-by-N-days figure from a raw due date string.

    Returns (days_overdue, next_due):
      - If due_on is missing: (None, None).
      - If due_on is in the past (overdue): (positive int days overdue, due_on).
      - If due_on is today or in the future (not yet due): (0, due_on) — we
        report 0 rather than a negative number, and the caller can still see
        the upcoming due date in `next_due`.

    We compute this ourselves rather than trusting an inferred figure because
    Companies House only exposes a boolean `overdue` flag plus the raw date —
    not a day count.
    """
    if not due_on:
        return None, None
    try:
        due_date = date.fromisoformat(due_on)
    except ValueError:
        return None, due_on
    delta = (date.today() - due_date).days
    if delta > 0:
        return delta, due_on
    return 0, due_on


def search_companies(
    sic_codes: str | None = None,
    location: str | None = None,
    company_name: str | None = None,
    company_status: str | None = None,
    incorporated_from: str | None = None,
    incorporated_to: str | None = None,
    size: int = 20,
) -> dict[str, Any]:
    """Search Companies House for companies matching the given criteria.

    See server.py's search_companies tool docstring for the model-facing
    contract; this function is the underlying HTTP call + response trimming.
    """
    if size is None or size < 1:
        size = 1
    if size > MAX_SEARCH_SIZE:
        size = MAX_SEARCH_SIZE

    params: dict[str, Any] = {"size": size}
    if sic_codes:
        params["sic_codes"] = sic_codes
    if location:
        params["location"] = location
    if company_name:
        params["company_name_includes"] = company_name
    if company_status:
        params["company_status"] = company_status
    if incorporated_from:
        params["incorporated_from"] = incorporated_from
    if incorporated_to:
        params["incorporated_to"] = incorporated_to

    url = f"{BASE_URL}{SEARCH_PATH}"
    retrieved_at = _now_iso()

    try:
        api_key = _get_api_key()
        response = httpx.get(
            url,
            params=params,
            auth=(api_key, ""),
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        return {
            "error": True,
            "error_type": "request_failed",
            "message": f"Request to Companies House search failed: {exc}",
            "source": url,
            "retrieved_at": retrieved_at,
        }

    request_url = str(response.request.url)

    if response.status_code != 200:
        return {
            "error": True,
            "error_type": "http_error",
            "status_code": response.status_code,
            "message": (
                f"Companies House search returned HTTP {response.status_code}."
            ),
            "source": request_url,
            "retrieved_at": retrieved_at,
        }

    payload = response.json()
    raw_items = payload.get("items", [])
    # NOTE (payload audit): Companies House's own field name for the total
    # match count is `hits`, not `total_results` (confirmed against a live
    # response — the field name in some third-party docs is wrong). We expose
    # it to the model as `total_results` since that's clearer than CH's
    # internal terminology, but read it from the real key.
    total_results = payload.get("hits")

    # NOTE (payload audit): the advanced-search response's items DO include
    # sic_codes for most items in practice, but it's not guaranteed present
    # on every item, so we surface it as [] when absent rather than omitting
    # the key — keeps the shape stable for the calling model.
    items = []
    for item in raw_items:
        items.append(
            {
                "company_name": item.get("company_name"),
                "company_number": item.get("company_number"),
                "company_status": item.get("company_status"),
                "address": _format_address(item.get("registered_office_address")),
                "sic_codes": item.get("sic_codes", []),
            }
        )

    return {
        "total_results": total_results,
        "items": items,
        "source": request_url,
        "retrieved_at": retrieved_at,
    }


def get_company_details(company_number: str) -> dict[str, Any]:
    """Fetch a single company's profile from Companies House.

    See server.py's get_company_details tool docstring for the model-facing
    contract; this function is the underlying HTTP call + field computation.
    """
    if not company_number or not str(company_number).strip():
        return {
            "error": True,
            "error_type": "invalid_input",
            "message": "company_number is required and must be non-empty.",
        }

    company_number = str(company_number).strip()
    url = f"{BASE_URL}{COMPANY_PATH.format(company_number=company_number)}"
    retrieved_at = _now_iso()

    try:
        api_key = _get_api_key()
        response = httpx.get(url, auth=(api_key, ""), timeout=15.0)
    except httpx.HTTPError as exc:
        return {
            "error": True,
            "error_type": "request_failed",
            "message": f"Request to Companies House company profile failed: {exc}",
            "source": url,
            "retrieved_at": retrieved_at,
        }

    if response.status_code == 404:
        return {
            "error": True,
            "error_type": "not_found",
            "message": f"No company found for company_number={company_number!r}.",
            "source": url,
            "retrieved_at": retrieved_at,
        }

    if response.status_code != 200:
        return {
            "error": True,
            "error_type": "http_error",
            "status_code": response.status_code,
            "message": (
                f"Companies House company profile returned HTTP {response.status_code}."
            ),
            "source": url,
            "retrieved_at": retrieved_at,
        }

    data = response.json()

    accounts = data.get("accounts", {}) or {}
    last_accounts = accounts.get("last_accounts", {}) or {}
    next_accounts = accounts.get("next_accounts", {}) or {}
    confirmation_statement = data.get("confirmation_statement", {}) or {}

    raw_last_accounts_type = last_accounts.get("type")
    no_accounts_ever_filed = raw_last_accounts_type == "null"
    last_accounts_type = None if no_accounts_ever_filed else raw_last_accounts_type

    accounts_overdue_days, accounts_next_due = _days_overdue(
        next_accounts.get("due_on")
    )
    confirmation_overdue_days, confirmation_next_due = _days_overdue(
        confirmation_statement.get("next_due")
    )

    if no_accounts_ever_filed:
        financials_note = NO_ACCOUNTS_FILED_NOTE_TEXT
    elif last_accounts_type in SMALL_FILING_TYPES:
        financials_note = FINANCIALS_NOTE_TEXT
    else:
        financials_note = None

    return {
        "company_number": company_number,
        "company_name": data.get("company_name"),
        "company_status": data.get("company_status"),
        "date_of_creation": data.get("date_of_creation"),
        "date_of_cessation": data.get("date_of_cessation"),
        "registered_office_address": _format_address(
            data.get("registered_office_address")
        ),
        "sic_codes": data.get("sic_codes", []),
        "last_accounts_type": last_accounts_type,
        "accounts_overdue_days": accounts_overdue_days,
        "accounts_next_due": accounts_next_due,
        "confirmation_statement_overdue_days": confirmation_overdue_days,
        "confirmation_statement_next_due": confirmation_next_due,
        "confirmation_statement_last_made_up_to": confirmation_statement.get(
            "last_made_up_to"
        ),
        "financials_note": financials_note,
        "source": url,
        "retrieved_at": retrieved_at,
    }
