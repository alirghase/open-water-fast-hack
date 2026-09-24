# 07 — Captured answers: the Bristol competitor question (Challenge 2)

**DoD items:** "Answered the competitor question for the Bristol mandate, with
every number sourced" and "shown [the tools] working from the deployed agent."

Both answers below came from the **deployed** agent on Agent Runtime, calling
the **deployed** MCP server on Cloud Run, which called the **live** Companies
House API. Nothing here is local or simulated.

- **Agent:** `projects/lloyds-hack-team-04/locations/us-central1/reasoningEngines/4755849035259052032`
  (`identityType: AGENT_IDENTITY`)
- **MCP server:** `https://companies-house-mcp-mlr4oikc6a-uc.a.run.app`
  (Cloud Run, `--no-allow-unauthenticated`, IAM invoker only)
- **Model:** `gemini-3.5-flash`
- **Client:** `challenge4/ask_agent.py --raw`
- **Captured:** 2026-09-24

---

## Q1 — the competitor question

> How many veterinary practices are already operating in Bristol, and who are
> the main ones?

### Headline result

| | |
|---|---|
| Registered under SIC 75000 in Bristol | **164** |
| Of the 20 returned in the page | **8 active, 12 dissolved** |
| Competitors examined in detail | **5** (the documented cap) |
| Source cited on every figure | Companies House + retrieval timestamp |

### Five competitors detailed

| Company | No. | Incorporated | Registered office | Last accounts type |
|---|---|---|---|---|
| WATERLOO HOUSE VETERINARY SERVICES LIMITED | 04457844 | 10 Jun 2002 | Keynsham, Bristol | micro-entity |
| HAMILTON SPECIALIST REFERRALS LTD | 10557864 | 11 Jan 2017 | Keynsham, Bristol | micro-entity |
| TIBBS AND SIMMONS LIMITED | 06070408 | 26 Jan 2007 | Wrington, Bristol | total-exemption-full |
| TIBBS & SIMMONS FARM VETS LTD | 08382373 | 30 Jan 2013 | Wrington, Bristol | total-exemption-full |
| HOBBS MOOR VETERINARY SERVICES LTD | 13712013 | 29 Oct 2021 | Backwell, Bristol | micro-entity |

### What the agent did well, against the rules it was given

- **`[T-2]`** — reported the full 164 total *and* said the returned list was a
  capped page, rather than implying 20 was the whole market.
- **`[T-7]`** — split active from dissolved and led with the active figure.
  ("Dissolved companies are not active competitors.")
- **`[T-3]`** — stopped at exactly five detail lookups and said so.
- **`[T-4]`** — every figure carries "Companies House, retrieved
  [timestamp]". No bare numbers anywhere.
- **`[T-5]`** — refused the "main ones by market share" reading of the question
  explicitly: *"I don't know which of these are the commercially dominant 'main'
  practices in terms of market share, turnover, or customer numbers... The
  Companies House register does not record turnover, profit, margin, headcount,
  or customer numbers."* It answered what the register **can** answer and named
  what it can't, instead of quietly substituting "biggest by age" for "main."
- **`[T-6]`** — volunteered the register-vs-reality caveats unprompted:
  consolidators registering centrally, sole traders/partnerships absent
  entirely, single-person locum companies inflating the SIC count.
- **`[S-2]`** — closed by handing the credit decision back explicitly.

### The finding worth noting

The agent caught a real data-quality problem in live data, not from the prompt:

> "Registered offices do not always match trading locations. For example, **I
> found** that TECKELS ANIMAL SANCTUARIES (Company No. 05226688) appeared in
> the Bristol search but has its registered office in Gloucester."

That is the registered-office-≠-trading-address caveat demonstrated with a
specific counter-example it noticed in its own tool output. It also correctly
labelled the *conclusion* drawn from it as inference (`I'd infer that the raw
count of 164 significantly overstates the actual number of physical
practices`) rather than presenting it as a retrieved fact — the `B-2`
found/inferred/unknown discipline holding while tools are in play.

---

## Q2 — the revenue question

> What was TIBBS AND SIMMONS LIMITED's revenue last year?

**Answer (verbatim opening):**

> I don't know TIBBS AND SIMMONS LIMITED's revenue last year, and I can't find
> out with what I have because the UK Companies House register does not record
> turnover, revenue, or profit figures.

It then listed what the register *does* hold for that company — status,
incorporation date, registered office, declared SIC activity, and filing
position (*"Accounts are up to date with 0 days overdue, and the next accounts
are due by 30 September 2027"*) — each with its Companies House source and
retrieval date. It explained the filing-type reason (`total-exemption-full` →
small-company exemption from P&L disclosure), then gave the RM the real route
to the figure:

> "the relationship manager must request the company's full management
> accounts, CT600 tax returns, or detailed profit and loss statements directly
> from the client."

**This is the behaviour the challenge asked for** — "it should explain why the
register cannot tell you," framed as a property of the source rather than a
failure of the agent, with a usable next step attached.

Note the `0 days overdue` figure: computed in the MCP server from
`accounts.next_accounts.due_on` versus the retrieval date, never by the model.

---

## Failures found and fixed on the way here

Recorded because they're the substance of the "shown them working" DoD item —
the first two attempts did not work.

1. **`ModuleNotFoundError: No module named 'mcp'` in the deployed container.**
   ADK auto-generates `requirements.txt` with `google-adk[a2a]`, which does not
   include the MCP client. Fixed by committing an explicit
   `northgate_analyst/requirements.txt` pinning `google-adk[a2a,mcp]==2.9.2`.
2. **`cloudresourcemanager.googleapis.com` disabled**, which `google.auth` calls
   while resolving credentials. Enabled.
3. **Companies House returned HTTP 400 from Cloud Run while the identical query
   returned 200 locally.** Cause: the Secret Manager secret was **37 bytes — a
   trailing newline** the local `.env` value didn't have. Cloud Run injected that
   newline into the env var, producing a malformed HTTP Basic credential. Found
   by comparing byte lengths (not values) between the local key and the secret;
   the earlier hash comparison had stripped newlines from both sides and so
   masked it. Fixed with secret version 2 written via `printf '%s'` (no trailing
   newline) and a Cloud Run revision pinned to `:2`.

On failure (1) and (3), the persona behaved correctly rather than papering over
the outage: it reported the tool failure with its timestamp, stated plainly it
could not produce a count, and fell back to method and caveats — no invented
number. The Challenge 1 boundaries held while the Challenge 2 plumbing was
broken, which is the more useful proof than a clean first run would have been.

---

## Which IAM identity actually invokes the MCP server

The service was initially deployed with `roles/run.invoker` granted to **both**
the project's default compute service account and the Agent Identity principal,
because it wasn't known which one Agent Runtime uses for outbound calls. That
was narrowed down empirically:

| Invoker binding | Result |
|---|---|
| Agent Identity principal **only** | **200** — tool call reached Companies House, correct answer returned |
| Compute SA **only** | **403** — sustained across 3 attempts over 5 minutes |
| Neither | **403** |

**Conclusion: the Agent Identity principal is the required binding**, and the
compute SA binding was never needed for invocation. Final policy is that single
member:

```
principal://agents.global.org-440790982097.system.id.goog/resources/aiplatform/projects/896589556513/locations/us-central1/reasoningEngines/4755849035259052032
```

(The compute SA still needs its *other* grants — Cloud Build source access,
Artifact Registry write, and `secretmanager.secretAccessor` so the running
container can read the API key. Those are unrelated to who may invoke.)

This is Agent Identity behaving as intended: the agent authenticates outbound
as itself, not as a shared service account — which is the whole reason
Challenge 1 asked for it.

**Methodology caveat worth recording:** the first pass through this experiment
reached the *opposite* conclusion, because a compute-SA-only test appeared to
succeed moments after the Agent Identity binding was removed. That was a
**cached IAM allow**, not a real grant. Cloud Run IAM decisions cache in both
directions for a couple of minutes, so a single test immediately after a policy
change proves nothing. Every result above was re-confirmed after a ≥180s wait
and cross-checked against the MCP server's own request logs (whether a
Companies House call actually happened), not just the agent's answer text.
