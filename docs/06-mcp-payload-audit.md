# 06 — MCP payload audit: Companies House tools

What Companies House returns vs. what `companies_house_mcp`'s two tools
actually surface to the model, and why each field was kept or dropped.
Written against `companies_house_mcp/companies_house_client.py` and
`companies_house_mcp/server.py` (Wave 1 of Challenge 2).

---

## Status: live-verified

Both tools were run against the real live Companies House API (SIC 75000 +
Bristol search, several real company-detail lookups, edge cases). Two real
findings surfaced during that verification, both fixed in
`companies_house_client.py`:

1. **The search response's total-match-count field is `hits`, not
   `total_results`.** Initial research (from third-party docs, not the raw
   API) had the wrong field name — confirmed against a live response (164
   real matches for SIC 75000 + Bristol). The client reads the correct raw
   key (`hits`) but still exposes it to the model as `total_results`, since
   that's clearer than Companies House's internal terminology.
2. **Companies House sometimes returns the literal string `"null"`** (not
   JSON `null`) as `accounts.last_accounts.type`, observed on a company
   dissolved before it ever filed a set of accounts. The client now
   normalizes this to a real `null` in `last_accounts_type` and sets
   `financials_note` to a distinct, more accurate message ("no accounts
   have ever been filed") rather than reusing the micro-entity wording.

The overdue-days computation was verified both against live due dates (all
sampled active companies showed future due dates → `0`, correctly not
overdue) and directly against edge cases (30 days overdue, 1 day overdue,
due today, due in future, missing date — all correct).

---

## Captured payload

Raw `GET /company/06070408` response (TIBBS AND SIMMONS LIMITED, an active
Bristol veterinary practice, SIC 75000) — real, public company data, nothing
redacted:

```json
{
  "accounts": {
    "accounting_reference_date": { "day": "31", "month": "12" },
    "last_accounts": {
      "made_up_to": "2025-12-31",
      "period_end_on": "2025-12-31",
      "period_start_on": "2025-01-01",
      "type": "total-exemption-full"
    },
    "next_accounts": {
      "due_on": "2027-09-30",
      "overdue": false,
      "period_end_on": "2026-12-31",
      "period_start_on": "2026-01-01"
    },
    "next_due": "2027-09-30",
    "next_made_up_to": "2026-12-31",
    "overdue": false
  },
  "can_file": true,
  "company_name": "TIBBS AND SIMMONS LIMITED",
  "company_number": "06070408",
  "company_status": "active",
  "confirmation_statement": {
    "last_made_up_to": "2025-12-10",
    "next_due": "2026-12-24",
    "next_made_up_to": "2026-12-10",
    "overdue": false
  },
  "date_of_creation": "2007-01-26",
  "etag": "d550a36355d9eca2957a77379e5ea011ede68f14",
  "has_been_liquidated": false,
  "has_charges": false,
  "has_insolvency_history": false,
  "jurisdiction": "england-wales",
  "last_full_members_list_date": "2016-01-26",
  "links": {
    "persons_with_significant_control": "/company/06070408/persons-with-significant-control",
    "self": "/company/06070408",
    "filing_history": "/company/06070408/filing-history",
    "officers": "/company/06070408/officers"
  },
  "previous_company_names": [
    { "ceased_on": "2007-02-19", "effective_from": "2007-01-26", "name": "PEPPERTREND LIMITED" }
  ],
  "registered_office_address": {
    "address_line_1": "Tibbs And Simmons Ltd",
    "address_line_2": "Nates Lane",
    "country": "United Kingdom",
    "locality": "Wrington",
    "postal_code": "BS40 5RS",
    "region": "Bristol"
  },
  "registered_office_is_in_dispute": false,
  "sic_codes": ["75000"],
  "type": "ltd",
  "undeliverable_registered_office_address": false,
  "has_super_secure_pscs": false
}
```

What our `get_company_details` tool actually returns for this same company:

```json
{
  "company_number": "06070408",
  "company_name": "TIBBS AND SIMMONS LIMITED",
  "company_status": "active",
  "date_of_creation": "2007-01-26",
  "date_of_cessation": null,
  "registered_office_address": "Tibbs And Simmons Ltd, Nates Lane, Wrington, Bristol, BS40 5RS, United Kingdom",
  "sic_codes": ["75000"],
  "last_accounts_type": "total-exemption-full",
  "accounts_overdue_days": 0,
  "accounts_next_due": "2027-09-30",
  "confirmation_statement_overdue_days": 0,
  "confirmation_statement_next_due": "2026-12-24",
  "confirmation_statement_last_made_up_to": "2025-12-10",
  "financials_note": null,
  "source": "https://api.company-information.service.gov.uk/company/06070408",
  "retrieved_at": "2026-09-24T14:07:30Z"
}
```

23 raw top-level/nested fields → 12 surfaced fields (2 of them derived, not
passthrough: the two `*_overdue_days` computations and `financials_note`).
`previous_company_names`, `links`, `etag`, `can_file`,
`registered_office_is_in_dispute`, `has_super_secure_pscs`,
`last_full_members_list_date`, and the raw `overdue` booleans are all
visibly present above and absent below, matching the field-by-field table.

---

## `get_company_details` — field-by-field

Reasoning below reflects what the code in `companies_house_client.py`
actually does (`get_company_details`), cross-checked against Companies
House's published company-profile schema.

| CH top-level field | Surfaced? | As | Reason |
|---|---|---|---|
| `company_name` | Kept | `company_name` | Primary identifier for the analyst. |
| `company_number` | Kept | `company_number` | Echoes the input; lets the model confirm which company it got back. |
| `company_status` | Kept | `company_status` | Core status fact (active/dissolved/etc.) — directly answerable question. |
| `date_of_creation` | Kept | `date_of_creation` | Company age is a standard due-diligence data point. |
| `date_of_cessation` | Kept | `date_of_cessation` | Needed to explain a non-active status; null for active companies. |
| `registered_office_address` (object) | Kept, reshaped | `registered_office_address` (formatted string) | Flattened from the nested address object (`address_line_1/2`, `locality`, `region`, `postal_code`, `country`) into one human-readable string — a model has no use for the nested shape, and a flat string is cheaper for it to quote back to a user. |
| `sic_codes` (array) | Kept | `sic_codes` | Needed to confirm/cross-check the industry classification a search was run against. |
| `accounts.last_accounts.type` | Kept | `last_accounts_type` | Drives the `financials_note` decision directly; also independently useful (tells the analyst how detailed a filing to expect). |
| `accounts.next_accounts.due_on` | Kept, computed | `accounts_overdue_days` + `accounts_next_due` | Raw date converted to a day-count via `(date.today() - due_date).days` — see "Overdue computation" below. Not left for the model to infer from a raw date. |
| `accounts.next_accounts.overdue` (bool) | Dropped (superseded) | — | CH's own boolean is redundant once we compute an exact day count ourselves; keeping both invites the two to disagree if CH's flag lags. `accounts_overdue_days > 0` is the single source of truth downstream. |
| `accounts.overdue` (bool, top-level accounts overdue flag) | Dropped | — | Same reasoning as above — the computed field is authoritative. |
| `confirmation_statement.next_due` | Kept, computed | `confirmation_statement_overdue_days` + `confirmation_statement_next_due` | Same overdue-day-count treatment as accounts. |
| `confirmation_statement.overdue` (bool) | Dropped (superseded) | — | Same reasoning as `accounts.next_accounts.overdue`. |
| `confirmation_statement.last_made_up_to` | Kept | `confirmation_statement_last_made_up_to` | Shows filing currency/history, cheap to include, no computation needed. |
| — (derived, not a CH field) | Added | `financials_note` | Computed from `last_accounts_type` — see "financials_note logic" below. This is the field the details tool's docstring points to as "source of truth for whether the register shows financial figures," so a revenue question doesn't need a second explanation. |
| `etag` | Dropped | — | Internal CH cache-validation token; no analytical value to a banking agent. |
| `links` (self, filing-history, officers, etc. URLs) | Dropped | — | API navigation URLs meant for a browser/crawler, not an LLM answering business questions; `source` (the URL actually called) already gives citeable provenance. |
| `has_charges` | Dropped | — | Relevant to secured-lending/insolvency questions, not this wave's competitive-density/filing-health scope. Candidate to add in a later wave if a charges-related question enters scope. |
| `has_insolvency_history` | Dropped | — | Same reasoning as `has_charges` — out of scope for Wave 1, easy to add later without a breaking shape change. |
| `previous_company_names` | Dropped | — | Rarely relevant to a live competitive/filing-health scan; adds noise for the common case. |
| `jurisdiction`, `type` (company type, e.g. `ltd`) | Dropped | — | Marginal value for this tool's target questions (filing health, status, basic identity); can be added later if a question needs it. |
| `can_file` | Dropped | — | Internal CH filing-eligibility flag, not an analyst-facing fact. |
| `undeliverable_registered_office_address` (bool) | Dropped | — | Edge-case operational flag, out of scope for Wave 1. |
| `annual_return` (legacy, pre-2016 companies) | Dropped | — | Deprecated/legacy field superseded by `confirmation_statement`; not relevant for any company incorporated post-2016 and adds confusion for older ones. |

### Overdue computation

Companies House gives a due date plus its own boolean `overdue` flag, but
never a day count. `_days_overdue()` in `companies_house_client.py` computes
`(date.today() - due_date).days` itself rather than leaving that arithmetic
to the calling model (models are unreliable at date math and at "today" in
particular). Shape chosen:

- Overdue (due date in the past): `*_overdue_days` = positive integer,
  `*_next_due` still shows the original due date for context.
- Not yet due (due date today or in the future): `*_overdue_days` = `0`
  (never negative), `*_next_due` shows the upcoming due date so the model
  can still say *when* it's due even though it isn't overdue yet.
- Missing due date entirely: both fields `None`.

This was chosen over a `null`-when-not-overdue shape because "0 days
overdue" reads unambiguously as "not overdue" to a model, whereas `null`
is easy to conflate with "unknown" — and `*_next_due` is always populated
alongside it, so no information is lost either way.

### `financials_note` logic

`last_accounts_type` is checked against a fixed set of small-filing types
— `micro-entity`, `dormant`, `abridged`, `audited-abridged`,
`unaudited-abridged`. When it matches, `financials_note` is set to:

> "Turnover, profit and headcount are not required in this filing type and
> are not available from this register."

Full/small/medium/group filings leave `financials_note` as `null`. This is
a derived field, not a passthrough — it exists specifically so the model
doesn't need a second lookup or a hardcoded explanation elsewhere in the
agent to correctly decline a revenue/profit/headcount question for a small
company.

---

## `search_companies` — item field-by-field

The advanced-search endpoint's response envelope (`total_results`, `items`,
plus per-item paging fields like `start_index`) is trimmed to just what a
competitive-scan question needs:

| CH item field | Surfaced? | As | Reason |
|---|---|---|---|
| `hits` (top-level, not per-item — CH's real field name; not `total_results`, see status note above) | Kept | `total_results` | Directly answers "how many" even when `items` is capped at 20 — this is the number the tool's docstring tells the model to read for count questions. Renamed on the way out for clarity, not passed through under CH's own name. |
| `company_name` | Kept | `company_name` | Primary identifier. |
| `company_number` | Kept | `company_number` | Required as the input to `get_company_details` — without this, the second tool is unreachable. |
| `company_status` | Kept | `company_status` | Cheap, high-value filter/display fact (active vs dissolved at a glance). |
| `registered_office_address` | Kept, reshaped | `address` (formatted string) | Same flattening treatment as the details tool, for the same reason. |
| `sic_codes` | Kept, defensively | `sic_codes` (defaults to `[]` if absent) | In practice most search-result items include `sic_codes`, but the field isn't guaranteed present on every item in the advanced-search response, so the client defaults to an empty list rather than omitting the key — keeps the item shape stable for the calling model regardless of which fields a given result happened to include. |
| `date_of_creation`, `date_of_cessation` (present on some search items) | Dropped | — | Available a lookup away via `get_company_details` if actually needed; keeping the search response lean matters more here since it can return up to 20 items per call. |
| `matches` (highlighted-match metadata some CH search responses include) | Dropped | — | UI-highlighting metadata for a browser search box, no meaning to an LLM. |
| `kind` (CH resource-type discriminator, e.g. `"searchresults#company"`) | Dropped | — | Internal API plumbing, not analyst-facing. |
| `description`, `description_identifier` (CH's own human-readable summary string) | Dropped | — | Redundant with the structured fields already kept (`company_name` + `company_status` + `address` cover the same ground), and duplicating it risks the model quoting CH's phrasing instead of reasoning over the structured fields. |
| `links` | Dropped | — | Same reasoning as the details tool — navigation URLs, not facts; `source` already gives citeable provenance for the whole response. |

`size` is clamped server-side to a max of 20 (`MAX_SEARCH_SIZE` in
`companies_house_client.py`) regardless of what's requested — this tool is
scoped to a quick scan, not bulk export, and there is no second-page
fetch built on top of `start_index`.

---

## Envelope fields added on every response (not from CH)

Both tools add two fields that Companies House doesn't return, for
provenance and auditability:

- `source` — the exact request URL called (including query params for
  search), so a downstream answer can cite exactly what was queried.
- `retrieved_at` — UTC ISO-8601 timestamp of the call, so a downstream
  answer can be dated (filing-status facts are time-sensitive).

On any failure (network error, non-200/404, invalid input), both tools
return `{"error": true, "error_type": ..., "message": ..., ...}` instead of
raising — no retries are attempted, matching the single-pass constraint in
both tool docstrings.
