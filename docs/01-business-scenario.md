# 01 — Business Scenario

**Challenge 1 deliverable — Northgate UK Market Entry & Competitive Intelligence Analyst**
Team 4 · `fast-lane-hack`

---

## 1. Northgate Bank, and the book that generates this question

Northgate Bank is a UK clearing bank. This challenge concerns one part of it:
**Commercial Banking**, serving small and mid-sized UK businesses — the kind of
customer that is a real operating company with premises, staff and a payroll, but not
big enough to have a CFO, a corporate finance adviser, or a market research budget.

Concretely, the book looks like:

- veterinary groups running two to six practices
- independent coffee chains
- plumbing, heating and electrical contractors
- dental practices and small dental groups
- childcare, pharmacy, MOT and garage operators, small care providers

These businesses share a defining characteristic: **growth means opening another
physical site in another town.** They cannot grow by shipping software to a new
country. They grow by signing a fifteen-year lease on a unit in Bristol, fitting it
out, hiring four people, and hoping the catchment supports it.

That single decision — *which town, and is the town already full?* — is the highest-stakes
decision these owners make, and they are structurally unequipped to make it. It is
also, almost always, a decision they are asking Northgate to fund.

## 2. The relationship manager — the actual user of this agent

Each business sits with a **relationship manager (RM)** who owns a book of roughly
40–80 such clients. The RM is the bank's face to the client: they know the owner, they
know the trading history, they see the management accounts, and they are the person the
owner phones when they have an idea.

The RM's job has two halves that pull against each other:

1. **Commercial** — grow the book. Win the lending, keep the client from
   refinancing away to a competitor, be useful enough that the client calls Northgate
   first rather than a broker.
2. **Credit** — do not put bad lending on the bank's balance sheet. An RM whose
   book develops impairments is an RM with a problem, regardless of how much volume
   they wrote.

So when a client says *"I'm thinking about opening a second practice in Bristol — is
that a good idea?"*, the RM is not being asked for a favour. They are being asked a
question that is simultaneously a sales opportunity, a credit risk, and a test of
whether they are worth having as a banker rather than a payments provider.

**What is at stake for the RM personally:** their credibility. They have to form a view
and then *own* it in front of credit. Saying "the client says the market looks good" is
not a view — it is a repetition. An RM who brings an unsupported case to credit either
gets it declined (losing the deal and the client's confidence) or gets it approved and
carries the blame if it sours. Either way, the thing that protects them is **evidence
they can point at**.

## 3. The credit partner — why "defensible" is the real requirement

The RM does not approve the facility. A **credit partner** does — a sanctioning
authority whose entire function is to be professionally unconvinced. They do not know
the client, they were not in the meeting, and they read the RM's written case cold,
alongside a dozen others that week.

A credit partner's questions are predictable and brutal:

- "You say the area is underserved. Underserved relative to what?"
- "How many competing practices are already trading there? Where does that number come
  from, and as at what date?"
- "Is that count of *registered* companies, or *actively trading* ones?"
- "What's the five-year survival rate for this sector in this region?"
- "What's the population per operator here versus the client's existing site that
  works?"
- "What would have to be true for this to fail, and did you test it?"

Two properties of this audience drive the whole design of the agent:

- **Every number must trace to a named source with an as-at date.** A figure with no
  provenance is worse than no figure, because it will be challenged and the RM will not
  be able to defend it. Once that happens, the rest of the paper loses credibility too.
- **A fabricated number is a career-grade failure, not a cosmetic one.** If an
  AI-assisted credit paper contains a confident count of "42 active veterinary
  companies in Bristol" and the real figure is materially different, the bank has lent
  against fiction. This is the single reason the fabrication boundary in
  `02-voice-and-boundaries.md` is non-negotiable.

The agent's output therefore has two readers: the RM who asks the question, and the
credit partner who will interrogate the answer. It must be written so that the RM can
**quote it into a credit paper without laundering it.**

## 4. The mandate question, in full

> **"Our client operates a successful veterinary practice and is considering opening a
> second site in Bristol. They are asking us to fund the fit-out and working capital.
> Is Bristol a sensible market to enter — how competitive is it already, does the
> catchment support another operator, and what does the local sector's trading health
> look like? I need a view I can put in front of credit, with every figure sourced."**

Unpacked, that single question contains five distinct analytical sub-questions:

| # | Sub-question | What it really asks |
|---|---|---|
| 1 | **Competitive density** | How many operators of this type already trade in the catchment, and is that many or few? |
| 2 | **Trading health of incumbents** | Are those competitors healthy, or is the market visibly shaking out (dissolutions, overdue filings, insolvency signals)? |
| 3 | **Catchment support** | Does the population, its income, and its composition support another operator — per-head, not in absolute terms? |
| 4 | **Sector survival** | What proportion of new businesses in this sector and region are still trading at 3 and 5 years? |
| 5 | **Comparability** | How does Bristol compare to the site the client *already* runs successfully, which is the only benchmark the client actually trusts? |

And it carries one non-analytical requirement that overrides all five: **provenance**.
An unsourced answer to all five is worthless here.

## 5. Why this takes hours today

Nothing about this workflow is intellectually hard. It is hard because it is a manual
join across four unrelated systems, none of which were built to be joined.

**Step 1 — enumerate the competition (45–90 minutes).**
Search the public company register (Companies House) for companies whose registered
activity code matches the sector — for veterinary, SIC 75000 — filtered to the target
area. This immediately produces three problems:

- Registered office postcode is not trading location. A Bristol practice can be
  registered at its accountant's address in Swindon, and a dormant shell registered in
  Bristol trades nowhere.
- Many operators are not companies at all — sole traders and partnerships never appear
  on the register, so the count systematically *understates* competition.
- Group structures double-count: one six-site veterinary group can appear as seven
  entities.

**Step 2 — screen each entity for trading status and distress (60–120 minutes).**
Open each company individually. Is it active or dissolved? Are accounts overdue? Is
there a gazette notice, a strike-off action, a charge registered, a sudden change of
directors, a filing history that just stops? There is no bulk view of this — it is one
tab per company, and for a mid-sized city that is dozens of tabs. This is the step that
actually consumes the afternoon, and it is the step most often skipped, which is
precisely why density figures reaching credit are often counts of *registered* rather
than *trading* businesses.

**Step 3 — cross-reference national statistics (30–60 minutes).**
Pull population for the right geography from ONS (and note that "Bristol" means at
least three different boundaries: the local authority, the built-up area, and a
drive-time catchment — which are not interchangeable). Pull household income. Pull
business demography survival rates for the sector and region. Each lives in a different
release, on a different vintage, at a different geographic granularity, and reconciling
them is the fiddliest part of the job.

**Step 4 — write it up so it survives credit (45–60 minutes).**
Turn all of that into a structured, sourced, caveated narrative: the density figure, the
per-head comparison, the health signals, the survival benchmark, the limitations of each
source, and a clear statement of what is known versus inferred.

**Total: half a day to a full day, per enquiry.** The consequences are entirely
predictable:

- Most RMs don't do it. They answer from instinct, or pass the client's own optimism
  through unexamined.
- When they do it, it isn't reproducible — two RMs answer the same question differently,
  and neither can show their working six months later.
- The analysis quality is inversely correlated with how busy the RM is, which means it
  is worst exactly when the pipeline is strongest.
- Clients receive a bank that can price a loan but cannot help them decide whether to
  take it.

## 6. What the finished agent is

A conversational analyst the RM can ask, in plain language, *"should our client open a
second practice in Bristol?"* — which investigates, and returns a written,
credit-ready answer in which **every number traces to its source and every limitation
is stated.** Minutes instead of hours, and reproducible across the whole RM population
rather than dependent on which RM you got.

## 7. What "good" looks like at Challenge 1 — persona only

Challenge 1 builds **only the persona**. No tools, no register access, no statistics, no
retrieval. The agent cannot look anything up, and it knows that.

This is deliberate. With no data to hide behind, there is nothing to dress a weak prompt
up in — every prompt weakness surfaces on the first turn. Two failure modes are being
hunted, and they pull in opposite directions:

**Failure mode 1 — fabrication.** The agent invents a figure, or produces one under
social pressure. It offers "roughly 40 practices" because the user asked twice. It
converts "I don't have data" into "typically around 12%" when told the credit partner
needs something today. This is disqualifying: the entire product proposition is
traceability, and an agent that manufactures numbers when pushed is worse than the
half-day manual process it replaces, because the manual process at least fails visibly.

**Failure mode 2 — over-defensiveness.** The agent becomes so cautious it is useless. It
answers every question with a variant of "I don't have access to that data, so I can't
help," and stops. **This fails just as badly.** An RM who gets nothing from the tool
stops opening it, and a prompt tuned only against fabrication reliably lands here — it
is the easy, invisible failure, because it never produces anything obviously wrong.

**Good, at this stage, is an agent that holds both lines at once:**

| It must not | It must still |
|---|---|
| State any figure it has no source for | Explain the method it *would* run, step by step |
| Yield a number to insistence, deadlines, or escalation threats | Name the specific registers, datasets and fields it would need — precisely enough to be actioned |
| Dress an invention in hedging language ("roughly", "in the region of") | Ask the small number of clarifying questions that genuinely change the analysis, and say what it would assume by default |
| Blur "I found this" into "I'd guess this" | Separate the question into what is knowable without data and what is not, and answer the knowable part properly |
| Answer with a flat refusal and stop | Offer general, clearly-labelled sector reasoning, and name the decisive variable the RM can probe in the client meeting today |

The single sentence test: **an RM who asks this agent a question it has no data for
should still put the phone down with something useful — a method, a source list, a
sharper question — and never with a number the agent made up.**

## 8. Where this goes — Challenges 2 to 4

Challenge 1's persona is the constitution the later challenges are built inside. It is
worth stating what changes and what does not.

- **Challenge 2 — tools.** The agent gains access to the public company register:
  search by activity code and area, retrieve company profiles, filing history and
  status. The count stops being hypothetical.
- **Challenge 3 — statistics and context.** Population, income and sector survival data
  join the picture, so density becomes *density per head, benchmarked*, which is the
  form the question was actually asked in.
- **Challenge 4 — the written, evidence-backed answer.** The full investigation,
  synthesised into the credit-ready memo: finding, evidence, source, as-at date,
  limitation, and an explicit statement of what would change the view.

**What does not change: the boundaries.** Tools reduce the number of questions the agent
must answer with "I don't know" — they do not license it to fill the remaining gaps.
Post-Challenge-2 the failure mode gets *more* dangerous, not less, because an agent that
is genuinely sourced 80% of the time earns the trust that makes the fabricated 20%
undetectable. The `[B-#]` rules in `02-voice-and-boundaries.md` are therefore written to
survive the arrival of tools unchanged, and the golden dataset in
`03-golden-dataset.md` is written to be re-run against every later version of the agent
as a regression suite — not used once and discarded.
