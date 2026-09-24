"""
MCP server exposing Companies House lookups to a banking-analyst AI agent.

Two tools are exposed via FastMCP:
  - search_companies: find companies by SIC code + location, or by name.
  - get_company_details: fetch filing/status facts for one company number.

Run locally:
    uv run --python .venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8080

Cloud Run (see Procfile):
    uvicorn server:app --host 0.0.0.0 --port $PORT
"""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load .env locally only. In production (Cloud Run) there is no .env file —
# env vars come from Secret Manager injection instead, so this is a no-op
# there and never errors if the file is absent.
load_dotenv()

from companies_house_client import get_company_details as _get_company_details
from companies_house_client import search_companies as _search_companies

mcp = FastMCP("companies-house")


@mcp.tool()
def search_companies(
    sic_codes: str | None = None,
    location: str | None = None,
    company_name: str | None = None,
    company_status: str | None = None,
    incorporated_from: str | None = None,
    incorporated_to: str | None = None,
    size: int = 20,
) -> dict:
    """Search the UK Companies House register to find companies. This is the
    ONE tool for locating companies — use it both to answer "how many
    companies are there matching X" (read `total_results`) and "who are
    they" (read `items`, a list of company summaries).

    Two distinct search modes, pick based on the question:
      - Market/competitive-density questions ("how many vets are there in
        Bristol?", "list veterinary practices in Bristol"): pass `sic_codes`
        (a UK SIC 2007 code, e.g. "75000" for veterinary activities) together
        with `location` (a free-text place name, e.g. "Bristol"). Do not
        guess a company name for this kind of question.
      - Looking up one specific, named company ("find Acme Vets Ltd"): pass
        `company_name` (matches on companies whose name includes this text).
        `sic_codes`/`location` are not needed in this mode but may be
        combined with `company_name` to narrow further if useful.

    All filters are optional and combine as AND conditions. Optional extra
    filters: `company_status` (e.g. "active", "dissolved"), `incorporated_from`
    / `incorporated_to` (ISO dates, YYYY-MM-DD) to bound incorporation date.

    `size` controls how many results come back per call (default 20, hard
    capped at 20 server-side — this tool is for a quick scan, not a bulk
    export; it does not paginate beyond one page). `total_results` in the
    response tells you the true total even when `items` is capped at 20, so
    you can still answer "how many" accurately even if you can't list them
    all.

    Each item in `items` has: company_name, company_number, company_status,
    address (formatted string), sic_codes. To get filing/financial-filing-
    type details on any one of these companies, pass its company_number to
    the get_company_details tool — never guess a company_number yourself.

    Returns a dict with: total_results (int), items (list), source (the
    exact API URL called, for citation), retrieved_at (UTC timestamp). On
    failure, returns an error dict with error=true and a message instead of
    raising — there are no retries, so treat an error result as final for
    this turn.
    """
    return _search_companies(
        sic_codes=sic_codes,
        location=location,
        company_name=company_name,
        company_status=company_status,
        incorporated_from=incorporated_from,
        incorporated_to=incorporated_to,
        size=size,
    )


@mcp.tool()
def get_company_details(company_number: str) -> dict:
    """Get filing and status facts for ONE specific company, identified by
    its `company_number`. `company_number` must come from a prior
    search_companies result (its `company_number` field) — never guess or
    construct one, as an invalid number will simply 404.

    This is also the SOURCE OF TRUTH for whether the public register shows
    financial figures for a company. Check the returned `financials_note`
    field before answering any revenue/profit/turnover/headcount question:
    if it is non-null, it means this company's last filed accounts were a
    small-company filing type (micro-entity, dormant, or abridged) that
    Companies House does NOT require to include turnover, profit or
    headcount — so those figures are genuinely unavailable from this
    register, not merely omitted by this tool. Don't ask this tool again or
    look elsewhere on this register for those numbers when `financials_note`
    is set; state that they aren't publicly available for this filing type.

    Returns a dict with: company_name, company_status, date_of_creation,
    date_of_cessation, registered_office_address (formatted string),
    sic_codes, last_accounts_type, accounts_overdue_days (0 if not overdue,
    null if unknown — see accounts_next_due for the actual due date),
    accounts_next_due, confirmation_statement_overdue_days,
    confirmation_statement_next_due, confirmation_statement_last_made_up_to,
    financials_note (see above), source (exact API URL, for citation),
    retrieved_at (UTC timestamp). On a missing/invalid company_number,
    returns an error dict (error=true, error_type="not_found") instead of
    raising.

    Usage limit: call this AT MOST 5 TIMES per conversation turn. Each call
    is a single-pass HTTP request with no retries — if a call errors, do not
    retry it and do not substitute a different company_number to compensate;
    just report the error. This limit is not enforced by the server (there
    is no session state here) — you must self-limit by not issuing more than
    5 of these calls before responding to the user.
    """
    return _get_company_details(company_number)


# ASGI app for Cloud Run / uvicorn. mcp.streamable_http_app() returns a
# mountable Starlette ASGI app implementing the MCP Streamable HTTP transport.
app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
