"""Throwaway manual test script. Prints only API responses, never the API key.
Run with: uv run --python .venv/bin/python _manual_test.py
"""
import json
import sys

from dotenv import load_dotenv

load_dotenv()

from companies_house_client import search_companies, get_company_details

def show(label, obj):
    print(f"\n=== {label} ===")
    print(json.dumps(obj, indent=2)[:4000])

# 1. Search by SIC + location
search_result = search_companies(sic_codes="75000", location="Bristol")
show("search_companies(sic_codes=75000, location=Bristol)", search_result)

items = search_result.get("items", [])
if not items:
    print("No items returned, aborting further tests.")
    sys.exit(1)

# Find a company number to test details on
first_number = items[0]["company_number"]
details = get_company_details(first_number)
show(f"get_company_details({first_number})", details)

# 2. Look through search results for a micro-entity / dormant company
micro_or_dormant = None
for item in items:
    d = get_company_details(item["company_number"])
    if d.get("last_accounts_type") in ("micro-entity", "dormant"):
        micro_or_dormant = d
        break

if micro_or_dormant:
    show("get_company_details (micro-entity/dormant example)", micro_or_dormant)
else:
    print("\nNo micro-entity/dormant company found in first page of results; trying more items via a second search page is out of scope (size cap), will report in summary.")

# 3. 404 test
bad = get_company_details("00000000")
show("get_company_details(00000000) [expect not_found]", bad)

# 4. size cap test
capped = search_companies(sic_codes="75000", location="Bristol", size=9999)
print("\n=== size cap test ===")
print("requested 9999, items returned:", len(capped.get("items", [])), "source:", capped.get("source"))
