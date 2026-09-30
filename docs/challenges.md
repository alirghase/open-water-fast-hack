# Challenges

Northgate Bank — UK Market Entry & Competitive Intelligence Analyst.

The brief below is the challenge text as issued: scenario, definition of done, reading references, and tips. Work through it in order. Challenge 1 has no tools. Challenge 2 adds one data source. Challenge 3 splits the work across four agents. Challenge 4 hardens the deployment and pitches it.

Challenges 5–8 are **not part of the issued brief**. They were added afterwards to cover what the hackathon left out: automated evals, observability and Gemini cost features (5), taking actions safely (6), memory and long conversations (7), and what the framework does for you, plus open models and A2A (8).

Challenges 9–12 are **also added**, to cover what Google's new **Professional Agentic
Architect** exam tests that 1–8 don't: low-code agents in Gemini Enterprise (9), coding agents
on Google Cloud (10), enterprise retrieval, registries and runtime choices (11), and security
and governance (12). Together, 1–12 cover every section of that exam:

| Exam section (official guide, 2026) | Weight | Challenges |
|---|---|---|
| 1 Building agents using low-code tools | ~13% | **9** |
| 2 Using coding agents for application development | ~17% | **10** |
| 3 Developing custom agents (models, ADK, sessions/memory, RAG, permissions, MCP, A2A, multi-agent) | ~33% | 1, 2, 3, 7, 8, **11** |
| 4 Evaluating and deploying (golden sets, continuous eval, runtime choice, troubleshooting, cost) | ~22% | 2, 5, **11** |
| 5 Securing and governing (OAuth, PAB, Agent Gateway, Agent Registry, Model Armor, HITL) | ~15% | 1, 4, 6, **12** |

The exam has a hands-on lab section as well as multiple choice, so doing these in a real
project is the preparation.

**Before Challenge 3:** the hackathon GCP account has been deleted, so redeploy the Challenge 1–2 agent and MCP server on your own GCP project first.

The reading-reference titles are unchanged. Each one is linked to the public page it names.

---

## Challenge 1: Foundations & Persona Architecture

### Scenario Overview

You work in the Commercial Banking team at Northgate Bank, a UK bank whose clients are small and mid-sized businesses — the veterinary groups, the coffee chains, the plumbing firms, the dental practices. Your relationship managers each look after a book of them, and those clients keep asking the same kind of question.

"I'm thinking about opening a second practice in Bristol. Is that a good idea?"

It is a fair question and the bank has a real interest in the answer, because more often than not the client is asking Northgate to help fund it. But answering it properly takes hours. Someone has to search the public company register to find every business of that type in the area, check each one to see whether it is still trading and whether it looks like it is struggling, then go to national statistics for the population, the local income levels, and whether businesses in that sector tend to survive there. Then they write it up for a relationship manager who has to take a view and defend it to a credit partner.

Over the next four challenges you are going to build the thing that does all of that — Northgate's UK Market Entry & Competitive Intelligence Analyst. Ask it "should our client open a second practice in Bristol?" and it goes and finds out, then comes back with a written answer where every number can be traced to where it came from.

None of that exists yet. Today it has no tools at all and cannot look anything up, and the only thing you are building is who it is.

That is the whole challenge. You will scaffold an agent with ADK, Google's Python framework, on a Gemini model, and write the system prompt that turns it from a general-purpose chatbot into this specific analyst. It cannot look anything up yet, which is the point — with no data to hide behind, every weakness in the prompt shows immediately.

Think about what this analyst actually is. It works for a Northgate relationship manager who is going to make a real decision about real money, and who will have to justify it to a credit partner. So it does not guess. It does not pad an answer to sound useful. When it does not know something it says so, and when someone leans on it for a number it does not have, it does not fold. It also has to stay useful — a prompt written defensively enough produces an agent that will not answer anything at all, and that fails just as badly as one that makes things up.

Once the persona holds up in the ADK web UI, deploy it to Agent Runtime with the Google Agents CLI. Add Agent Identity to it on this first deployment. It gives this agent its own secure, immutable identity, so its access to models, data, and future integrations can be managed separately in Google Cloud IAM instead of sharing a broad service-account identity with other workloads. Do it now, while the agent is simple — get the deployment pipeline proven while there is nothing complicated attached to it.

### Definition of Done

#### Technical

* Scaffolded a minimal ADK Python agent project
* System prompt written, structured so any individual behaviour can be traced to a specific line
* Deployed the agent to Agent Runtime with agent identity and confirmed it answers from the managed runtime, in the Playground
* Captured the deployed agent's answer to the mandate prompt above

#### Non-technical

* define the core business scenario
* design the agent's conversational tone, voice, and boundaries
* define the "golden dataset" of expected inputs and outputs for later evaluation.

### Reading References

* [ADK — Python Quickstart](https://adk.dev/get-started/python/)
* [ADK CLI Reference (adk create, adk run, adk web)](https://adk.dev/runtime/command-line/)
* [ADK — LLM Agents: instruction, persona](https://adk.dev/agents/llm-agents/)
* [Deploy an existing ADK agent to Agent Runtime with Agents CLI](https://adk.dev/deploy/agent-engine/)
* [Agent Runtime agent identity](https://adk.dev/integrations/agent-identity/)
* Use a deployed agent — Agent Platform Console Playground
* [What is Prompt Engineering?](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/prompts/introduction-prompt-design)
* [Introduction to Prompt Engineering](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/prompts/introduction-prompt-design)
* [Prompt Design Strategies](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/prompts/prompt-design-strategies)
* [How to write ai agent instructions](https://adk.dev/agents/llm-agents/)
* [Golden Datasets](https://adk.dev/evaluate/)

### Tip

* Start from adk create. Three files. Build the persona against that, not against a production scaffold; the scaffold comes in only at the deployment step.

---

## Challenge 2: Bridging to Reality

### Scenario Overview

Your analyst knows exactly who it is. It runs on Agent Runtime, it speaks like a Northgate analyst, and when a relationship manager asks it about a real company it says, honestly, that it cannot look that up yet. That was the right answer in Challenge 1. It is not an answer anyone can take to a credit partner.

The first question about the Bristol mandate is always the same: who else is already doing this there? Before anyone can talk about whether a Manchester veterinary group should open a practice in Bristol, the relationship manager needs to know how many veterinary businesses are already trading in the city, who they are, and what shape they are in. Today someone answers that by hand, searching the public register one company at a time. In this challenge your agent learns to do it itself, with one data source, one agent, and nothing else.

That data source is Companies House, the UK's official register of companies. Every limited company in the country is on it: its name and company number, when it was incorporated and whether it has since been dissolved, where its registered office is, what line of business it declared, and whether it is keeping up with the accounts and annual confirmation statement it is legally required to file. The Companies House API exposes all of this for free.

Your agent will never hold that key. Instead you will build a small Model Context Protocol (MCP) server, the open standard that lets an agent discover and call tools hosted somewhere else, and it will talk to Companies House on the agent's behalf. You deploy that server to Cloud Run as its own service, connect your agent to it, and redeploy the agent to Agent Runtime. The server owns the credential and the API; the agent only ever sees tools.

The server needs two of them, and each one answers a different part of the relationship manager's question.

The first finds the competition. Companies House files every company under a SIC code, the Standard Industrial Classification number a company declares when it registers to say what it does; veterinary activities are 75000. Your search tool should let the agent find companies by SIC code and location together (veterinary businesses in Bristol), or by company name when the relationship manager asks about one practice they have heard of, and narrow the results by status (active or dissolved) and by when the company was incorporated. The search response reports the total number of matches as well as the page of results it returns, so the same tool answers both how many competitors are there? and who are they?

The second gets the details on a single competitor. Given a company number from the search, it returns the facts a banker actually reads: whether the company is still active, when it was incorporated, where it is registered, and where it stands on its filings — when its next accounts are due, whether they are overdue and by how many days, and whether its confirmation statement is up to date. Work out that "days overdue" figure in the server, not in the model; a language model should never be doing date arithmetic on a filing deadline. And set expectations early: most veterinary practices are small companies that file micro-entity or abridged accounts, which carry no turnover, no profit and no headcount. When the relationship manager asks what a competitor earns, the right answer is that the register does not say, not a plausible guess.

What you call the two tools is up to you. What matters more is each tool's description and the names of its arguments, because that is the only manual the model gets when it decides which tool to call and how. Every response should also carry its source, which endpoint the data came from and when it was retrieved, so the agent can put a citation beside every number it gives.

Keep the scope tight: one search, at most five competitors looked up in detail, a single pass with no retries. By the end of challenge, the deployed agent should take a question like "How many veterinary practices are already operating in Bristol, and who are the main ones?" and come back with the number of active companies registered under SIC 75000 in Bristol, a short list of them, and a few lines on up to five of them — status, incorporation date, filing position — with the Companies House source and retrieval date next to every figure. Ask it "What was their revenue last year?" and it should explain why the register cannot tell you.

### Definition of Done

#### Technical

* Built an MCP server with a tool to search for companies and a tool to get a company's details, and tested it on its own
* Deployed the MCP server to Cloud Run
* Connected the tools to your agent and shown them working from the deployed agent
* Answered the competitor question for the Bristol mandate, with every number sourced

#### Non-technical

* Audited the Companies House payloads and decided which fields the model needs
* Engineered prompts that make the right tool fire reliably
* Rescored the golden dataset manually using the Agent Platform Playground

### Reading References

#### Companies House

* [Companies House API — get started and register for a key](https://developer.company-information.service.gov.uk/get-started)
* [Company House overview](https://developer.company-information.service.gov.uk/overview)
* [Companies House — how to create an application](https://developer.company-information.service.gov.uk/how-to-create-an-application)
* [Companies House Public Data API — advanced company search](https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/search/advanced-company-search)
* [Companies House Public Data API — company profile resource](https://developer-specs.company-information.service.gov.uk/companies-house-public-data-api/reference/company-profile/company-profile)
* [ONS — UK Standard Industrial Classification (SIC 2007)](https://www.ons.gov.uk/methodology/classificationsandstandards/ukstandardindustrialclassificationofeconomicactivities/uksic2007)
* [GOV.UK — what micro-entities and small companies file](https://www.gov.uk/government/publications/life-of-a-company-annual-requirements/life-of-a-company-part-1-accounts)

#### MCP Server

* [MCP — build a server (Python SDK, FastMCP)](https://modelcontextprotocol.io/docs/develop/build-server)
* [MCP Inspector — test and debug MCP servers](https://modelcontextprotocol.io/docs/tools/inspector)

#### ADK & Cloud Run

* [Cloud Run — build and deploy a remote MCP server](https://docs.cloud.google.com/run/docs/host-mcp-servers)
* [Cloud Run — host MCP servers](https://docs.cloud.google.com/run/docs/host-mcp-servers)
* [ADK — MCP tools (McpToolset, streamable HTTP)](https://adk.dev/tools-custom/mcp-tools/)
* [Codelab — build and deploy an ADK agent that uses an MCP server on Cloud Run](https://codelabs.developers.google.com/codelabs/devsite/codelabs/adk-mcp-fulfillment-agent)
* [Deploy an ADK agent to Agent Runtime with Agents CLI](https://adk.dev/deploy/agent-engine/)

### Tips

* Register the Companies House key before anything else. Sign-up needs an email confirmation plus an SMS or authenticator code, and when you create the key choose a REST key on a Live application; a Streaming key or a Test application will not work against the live register.

---

## Challenge 3: Agent-to-Agent Collaboration

### Scenario Overview

The competitor report from Challenge 2 is useful. It can tell a relationship manager which veterinary businesses are registered in Bristol, how many are active, and which companies have been dissolved. But it cannot answer the question the client actually cares about: should we open another veterinary practice there?

The missing part is the local market. A city can have a long list of competitors and still be growing. It can also have a small list of competitors because businesses are struggling to survive. The relationship manager needs information about the wider business environment before they can explain the risk to the client. That information comes from two public Office for National Statistics (ONS) Explore local statistics datasets: Business births, the rate of new businesses, and Business deaths, the rate of businesses that have closed.

Neither dataset gives the answer on its own. Together they show whether the number of businesses in a local authority is increasing or decreasing. The data covers local areas across the United Kingdom and includes a United Kingdom figure for comparison. That national figure matters. A Bristol birth rate means more when the relationship manager can see whether it is above or below the UK rate for the same year. It is useful background, not strict proof that local people need another veterinary practice or that the client should invest.

In this challenge, the ONS data becomes the responsibility of a new Market Analyser. This agent searches the local business data and explains what it says about the chosen area and the UK comparison. It uses Google Cloud Agent Search to make the public ONS records available for search. It must stay within that boundary: it can discuss business births, business deaths, and the local change, but it must not invent figures about customers, household income, population, or individual companies.

The existing Competitor Analyst keeps a narrow Companies House role: it counts active and dissolved competitors and checks a named company's status. It does not interpret ONS market data. Keeping these two jobs separate is important. If one agent sees both sources from the start, it can blur them together and hide the fact that they tell different stories.

The two analysts pass their findings through shared session state to a third agent, the Strategist. The Strategist does not search for more data. It reads the company analysis and the local-market analysis, then writes a short Market Entry Report. In plain language, it explains the number and status of competitors alongside the local business trend and UK comparison. It should also be clear about what the data does not show.

Finally, the relationship manager speaks to an Orchestrator. The Orchestrator brings the three specialists together: it asks the Competitor Analyst for company evidence, asks the Market Analyser for local context, then asks the Strategist to write the report. The instructions, descriptions, and hand-offs between those agents matter as much as the data. The Orchestrator must know who to ask, when a piece of work is complete, and when the final report needs to say that there is not enough evidence.

By the end of the challenge, a relationship manager should be able to ask: "Our client runs six veterinary practices in Manchester. Should they open one in Bristol?" The answer should be one clear Market Entry Report that explains the Companies House competitor numbers and status, the ONS local-versus-UK market trend, and what those two sources can and cannot show.

### Definition of Done

#### Technical

* Combined the 2024 ONS Business births and Business deaths data into one local-market dataset with a United Kingdom comparison
* Made the local-market data searchable through Google Cloud Agent Search
* Built a multi-agent architecture with an Orchestrator, Competitor Analyst, Market Analyser, and Strategist
* Produced a short Market Entry Report that explains competitor numbers and status, the local market trend, and the United Kingdom comparison

#### Non-technical

* Design the multi-agent organisational chart: show what each of the four agents does and which data it uses.
* Draft the behavioural personas and system prompts for the sub-agents: make each agent's role and data boundary clear.
* Write explicit hand-off protocols and state rules: define how agents pass their findings to the next agent and when they return control to the Orchestrator.

### Reading References

* [What is AI-agent-orchestration](https://cloud.google.com/blog/products/ai-machine-learning/what-is-agent-orchestration)
* [Building Multi Agent Systems](https://adk.dev/agents/multi-agents/)
* [Draw.io](https://app.diagrams.net/)

#### ONS data

* [ONS Explore local statistics](https://www.ons.gov.uk/explore-local-statistics/)

#### Preparing the data with pandas

* [pandas — read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
* [pandas — merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html)
* [pandas — merge, join, and concatenate](https://pandas.pydata.org/docs/user_guide/merging.html)
* [pandas — DataFrame.to_csv](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html)

#### Agent Search

* [Agent Search - prepare data for ingestion](https://docs.cloud.google.com/generative-ai-app-builder/docs/prepare-data)
* [Agent Search — create a data store and ingest data](https://docs.cloud.google.com/generative-ai-app-builder/docs/create-datastore-ingest)
* [Agent Search - create search app](https://docs.cloud.google.com/generative-ai-app-builder/docs/create-engine-es)

#### ADK

* [ADK — multi-agent workflows and delegation](https://adk.dev/agents/multi-agents/)
* [ADK - multi-agent design patterns](https://adk.dev/workflows/patterns/)
* [ADK - sub-agents vs agents as tools](https://adk.dev/workflows/patterns/)
* [ADK — session state - Focus on how to access state object in agent instructions and how to add to state object](https://adk.dev/sessions/state/)
* [ADK - VertexAiSearchTool](https://adk.dev/tools/built-in-tools/)

### Tips

* Download needed datasets from ONS Explore local statistics directly
* After you index crafted dataset test it out by creating search app and testing search capabilities there

---

## Challenge 4: Enterprise Hardening & The Pitch

### Scenario Overview

The relationship manager now has a Market Entry Report backed by Companies House and ONS data. Before Northgate shares it more widely, two questions remain: can we return to an earlier assessment, and can we trust the agent when someone tries to mislead it?

First, keep the conversation. Vertex AI Agent Sessions, documented as Agent Platform Sessions, stores conversation history and shared agent state. Use VertexAiSessionService in the Agent Development Kit (ADK) so the relationship manager can resume an assessment after closing the client or restarting the application. A new session should start a separate conversation, not inherit the previous report.

Next, protect the deployed agent with Agent Gateway and Model Armor. Configure Client-to-Agent (ingress) protection only: requests from the client to the agent and responses back to the client. Agent-to-Anywhere (egress) protection is outside this challenge. Model Armor checks supported prompts and responses for risks such as attempts to override instructions, sensitive information, and harmful content. Its templates define the checks; the gateway applies them to supported traffic. Creating a template without connecting it to the agent is not enough.

Use the supplied test client to try a normal business question and a synthetic prompt that triggers your Model Armor policy. Save the results. An agent saying "I cannot answer" is different from the gateway blocking the request before it reaches the agent.

Not every attack comes from the person asking the question. Instructions can also hide inside a company name, filing description, or retrieved document. This is indirect prompt injection: the agent mistakes source text for an instruction. The Client-to-Agent gateway does not inspect the internal MCP tool exchange, so the agent must treat that text as data, not commands.

Your team now becomes the red team: try to make the agent invent revenue, recommend an acquisition, omit a limitation, or follow an instruction hidden in a synthetic tool result. Record what held, what failed, and what you fixed. Test only your team's authorised deployment or training labs, using synthetic data. The reading references include examples that require no coding.

Finish with a short pitch. Show the sourced report, a resumed conversation, and a before-and-after security result. Explain the time saved and the work still needed before production.

By the end, a relationship manager should be able to reopen a conversation and ask: "Continue our Bristol veterinary-practice assessment and refresh the company evidence." The agent should retain the earlier context, fetch fresh company facts, and keep the ONS reference period and data limitations visible.

### Definition of Done

#### Technical

* Used VertexAiSessionService to resume a deployed conversation with its history and shared state intact
* Shown that a new session starts without the previous conversation's history or ordinary session state
* Configured only Client-to-Agent (ingress) protection on the identity-enabled Agent Runtime, using Agent Gateway with Model Armor request and response templates; demonstrated an allowed request and a confirmed Model Armor block using the test client
* Shown that an instruction hidden in synthetic source data does not override the report's facts or rules

#### Non-technical

* Run the red-team exercise: try to jailbreak northgate AI agent to bypass his instructions
* Try harder to jailbreak northgate AI agent :)
* Draft a release checklist that lists the privacy, security, quality, and operational tasks still outstanding before go-live
* Build and present a compelling business pitch demonstrating the agentic workflow's ROI

### Reading References

#### Vertex AI sessions

* [Agent Platform Sessions overview — conversation history, events, and state](https://docs.cloud.google.com/gemini-enterprise-agent-platform/sessions/overview)
* [Use Sessions with ADK — connect VertexAiSessionService](https://adk.dev/sessions/session/)
* [ADK — session state and scope](https://adk.dev/sessions/state/)
* [Manage Sessions in the console and API — inspect stored sessions and events](https://docs.cloud.google.com/gemini-enterprise-agent-platform/sessions/manage-sessions-api)

#### Agent Gateway and Model Armor

* [Agent Gateway overview — ingress versus egress](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview)
* [Set up Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/set-up-agent-gateway)
* [Agent identity on Agent Runtime](https://adk.dev/integrations/agent-identity/)
* [Route Agent Runtime traffic through Agent Gateway — runtime binding, registry, and IAM](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-gateway-runtime-deploy)
* [Configure Model Armor on a gateway — roles and supported payloads](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/configure-model-armor)
* [Create and manage Model Armor templates](https://docs.cloud.google.com/security-command-center/docs/manage-model-armor-templates)
* [Validate templates and sanitize prompts and responses](https://docs.cloud.google.com/security-command-center/docs/sanitize-prompts-responses)

#### Educational AI red-teaming

No coding is needed for these readings and exercises. Start with the introduction, then adapt an example to the Bristol scenario. Older examples may not work on current models; a failed attempt is still worth recording.

* [Learn Prompting — What is prompt hacking?](https://learnprompting.org/docs/prompt_hacking/introduction) — a short introduction to misleading an AI through its instructions
* [Learn Prompting — Prompt injection examples](https://learnprompting.org/docs/prompt_hacking/injection) — simple "ignore the instructions" examples and explanations of attacks hidden in source material
* [Prompt Engineering Guide — Adversarial prompting](https://www.promptingguide.ai/risks/adversarial) — example prompts and responses; start with the Prompt Injection section
* [Lakera — Agent Breaker](https://www.lakera.ai/agent-breaker) — a browser-based AI hacking game for practice without setting up tools
* Jailbraking Gemini

### Tips

* Your Agent Gateway and Model Armor need to be deployed in the same region for the integration to work properly.

---

## Challenge 5: Measure and Observe *(added)*

### Scenario Overview

The analyst now answers the Bristol question end to end. But the only evidence it's any good is you reading its answers in the Playground and scoring them by hand. When a relationship manager says "it gave me a strange answer yesterday", you can't see which tools ran, what they returned, or what the answer cost.

In this challenge the golden dataset becomes an automated test that runs on every change. A cheap, deterministic check catches the failure that matters most: a number in the answer that no tool ever returned. An LLM judge handles the qualities code can't check, and you find out how far to trust it by comparing it against your own scores. Then every run becomes a trace, and every report gets a cost.

### Definition of Done

#### Technical

* The golden dataset runs with `adk eval` and an `eval_config.json` that sets thresholds, locally and in CI (GitHub Actions) on every push
* A custom deterministic metric: every number in the final answer appears in a tool response from the same session
* A rubric-based LLM judge (for example `rubric_based_final_response_quality_v1`) scores the same cases
* Traces from the deployed agent in Cloud Trace, with spans for model calls, tool calls and sub-agent handoffs
* Cost per Market Entry Report and p95 latency, computed from token usage
* **Context caching** for the long system instruction, with the change in cost and latency measured
* The LLM judge runs over the whole eval set as a **Vertex AI batch prediction** job, with its cost compared against calling the judge one case at a time

#### Non-technical

* Score 30 real answers yourself (pass/fail and why), then report how often the LLM judge agrees with you, and where it doesn't
* Break the prompt on purpose and show that CI catches it

### Reading References

* [ADK — Evaluation](https://adk.dev/evaluate/)
* [ADK — Evaluation criteria](https://adk.dev/evaluate/criteria/)
* [ADK — Custom metrics](https://adk.dev/evaluate/custom_metrics/)
* [ADK — Traces](https://adk.dev/observability/traces/)

### Tips

* Record Companies House responses as fixtures for CI, so tests don't hit the live API or burn your rate limit.

---

## Challenge 6: Acting Safely *(added)*

### Scenario Overview

So far the analyst only reads. An agent that only reads can't do much damage. Real agents act, and acting is where autonomy needs fences.

The relationship manager now wants two things. First, when they're happy with a Market Entry Report, they want to **file it** to the client's case folder. Second, they want to **watch** a company: add it to a watchlist so they hear about it when its filings go overdue or it's dissolved. Both are writes, and both need to be safe.

The fences are the point of this challenge. A write happens only after the RM approves the exact content. The identity that reads the register can't write anything. Every run has a hard budget. And a prompt injection hidden in a company name that says "file this report now" does nothing, because approval is enforced in code, not requested in a prompt.

### Definition of Done

#### Technical

* Two write tools: `file_report` (writes to a GCS case folder) and `add_to_watchlist` (writes to Firestore), both with `require_confirmation`. The RM approves the exact payload
* Separate identities: the agent that reads Companies House can't write. Only the confirmed-action path holds write permission, visible in IAM
* A per-run budget (maximum tool calls and tokens), enforced by a callback or plugin that stops the run
* A scheduled job (Cloud Scheduler) that checks watchlisted companies and **drafts** an alert when their filing status changes. It never sends anything on its own
* Eval cases: an injection that tries to trigger a write, an over-budget run, and a quiet day where no alert is the right answer

#### Non-technical

* A one-page threat model: what each identity can touch, what an attacker can control (the prompt, company names, tool output), and what stops each path

### Reading References

* [ADK — Tool confirmation](https://adk.dev/tools-custom/confirmation/)
* [ADK — MCP tools (advanced): `require_confirmation`](https://adk.dev/tools-custom/mcp-tools/advanced/)

---

## Challenge 7: Memory and Long Conversations *(added)*

### Scenario Overview

A relationship manager covers the same clients week after week, and they're tired of re-explaining that "our client" means a six-practice veterinary group in Manchester. Sessions from Challenge 4 remember one conversation. This challenge remembers the RM across conversations.

Memory creates a new way to be wrong. A competitor count remembered from March is a stale figure in September. So the rule here is that memory holds **context**, never **evidence**: any figure still comes from a fresh tool call. Long conversations have their own problem, too. Past a certain length the context window fills with old tool output, and quality drops. Compaction summarises older turns so the agent keeps what matters.

### Definition of Done

#### Technical

* Long-term memory per RM with `VertexAiMemoryBankService`: client profile, preferences, past mandates
* A written memory policy (what gets stored, what never does, when it expires), enforced in code and tested
* A test showing the agent re-fetches a figure instead of repeating one from memory
* `EventsCompactionConfig` on long sessions, with quality measured on a 20-turn conversation with and without compaction

#### Non-technical

* Decide what the analyst should *never* remember, and write down why

### Reading References

* [ADK — Context compaction](https://adk.dev/context/compaction/)
* ADK — Memory (`VertexAiMemoryBankService`, `PreloadMemoryTool`)

---

## Challenge 8: Under the Hood *(added)*

### Scenario Overview

ADK has been doing a lot of work for you: the loop that calls the model, the parsing of tool calls, the dispatch to MCP, the session state. That's what frameworks are for. But when something goes wrong inside the framework, you need to know what it's doing.

In this challenge you build the Competitor Analyst again **without ADK**. A plain Python loop calls Gemini with function calling, executes the tool calls against your same MCP server, feeds the results back, and stops. Then you run the Challenge 5 eval set against both versions.

### Definition of Done

#### Technical

* A framework-free agent loop (the model SDK plus an MCP client, nothing else) that answers the Bristol competitor question
* Handles a tool that errors, a tool that times out, and a maximum step count
* The Challenge 5 eval set runs against both the ADK version and yours, and the results are compared
* Swap the model: run your loop on an **open model from Vertex AI Model Garden** (one served as a managed API, so there's no endpoint to keep running) and compare it with Gemini on the same eval set
* **A2A:** expose your framework-free Competitor Analyst as an A2A service with an agent card, and have the ADK Orchestrator from Challenge 3 call it as a remote agent

#### Non-technical

* Write down three things ADK did that you had to build yourself, and one thing you'd do differently from ADK

### Tips

* Keep it small, a couple of hundred lines. The aim is to see the machinery, not to replace ADK.
* Check which Model Garden models are offered as a pay-per-token managed API in your region before you pick one.

### Reading References

* [ADK — Exposing an agent via A2A](https://adk.dev/a2a/quickstart-exposing/)

---

## Challenge 9: Low-Code Agents in Gemini Enterprise *(added — Agentic Architect §1)*

### Scenario Overview

Not every Northgate team will write Python. The relationship-management operations team wants to build their own simple agents, and the bank wants to know when a low-code agent is enough and when it needs yours.

In this challenge you rebuild a slice of the Northgate Analyst **without code**, in Gemini Enterprise. First, a **mandate intake agent** in CX Agent Studio: a state-based flow with pages, transition routes and event handlers. It collects the client, the sector, the location and the question, and it handles the RM going off-script. Then a **research assistant** in Agent Designer that answers from Northgate's own documents, connected securely as an enterprise data source, including an image (a chart) and an audio note from an RM.

Finally, the real question: where does low-code win, and where did you hit a wall that the ADK version doesn't have?

### Definition of Done

#### Technical

* A CX Agent Studio flow with at least four pages, conditional transition routes and event handlers (no-match, no-input, the RM changing their mind), plus a system instruction and a prompt template (few-shot or chain-of-thought)
* An Agent Designer agent connected to an enterprise data source (the ONS dataset and a folder of Northgate documents via Agent Search), answering with citations
* Unstructured multimodal input working end to end: a chart image and a short audio note fed into the workflow
* The same 10 golden-set questions run against the low-code agent and your ADK agent, with the results compared

#### Non-technical

* A one-page decision guide: when Northgate should use low-code agents, when it should use ADK, and why

### Reading References

* Official exam guide, section 1: [Professional Agentic Architect exam guide](https://services.google.com/fh/files/misc/professional_agentic_architect_exam_guide_english.pdf)
* Gemini Enterprise documentation: Agent Designer, CX Agent Studio, connecting data sources

### Tips

* Gemini Enterprise is licensed per user. Check the trial and pricing before you start, and tear it down afterwards.

---

## Challenge 10: Coding Agents on Google Cloud *(added — Agentic Architect §2)*

### Scenario Overview

Northgate's engineers now build with coding agents, and the platform team has to make that safe and useful. In this challenge the Northgate codebase itself is the target: you configure coding agents to work on it, inside a sandbox, with Northgate's own tools and rules.

### Definition of Done

#### Technical

* **Antigravity** and **Claude Code on Google Cloud** both configured with your Companies House MCP server (Challenge 2) and at least one Google Cloud MCP server, plus custom skills
* Both running inside a **secure sandbox**: Cloud Workstations or a locked-down GKE sandbox, with no access to anything outside the repo and its test environment
* Enterprise customisation in Antigravity: rules, hooks (a guard that blocks destructive commands), a skill, and a subagent (e.g. a reviewer)
* **Agents CLI** used to build, deploy and govern the Northgate agent from the coding agent's workflow
* The coding agents used on real work: refactor one module, optimise a slow path (measured before and after), and **patch a vulnerability you seed deliberately** (e.g. an unvalidated tool argument)

#### Non-technical

* A short comparison of the two coding agents on the same three tasks: success, time, cost, and where each needed help

### Reading References

* Official exam guide, section 2: [Professional Agentic Architect exam guide](https://services.google.com/fh/files/misc/professional_agentic_architect_exam_guide_english.pdf)
* Antigravity documentation (CLI, SDK, app) · Agents CLI in Agent Platform · Cloud Workstations

### Tips

* Your AI roadmap's capstone 01 builds a coding agent from scratch. This challenge is the other side: configuring and governing someone else's. Doing both is what makes you dangerous in an interview.

---

## Challenge 11: Enterprise Retrieval, Registries and Runtimes *(added — Agentic Architect §3–4)*

### Scenario Overview

The analyst works, but an architect has to justify every choice underneath it. Which retrieval service? Which runtime? How do other teams find and reuse Northgate's agents and tools? How does quality get checked continuously, not just before a release?

### Definition of Done

#### Technical

* **Retrieval, compared:** the same ONS and filings data served through Agent Search (Challenge 3), **RAG Engine**, and **Vector Search / Agent Retrieval** with your own embedding model and reranking. Retrieval quality measured on your golden set, plus cost and latency for each
* **Model choice, argued:** one sub-agent moved to a small or open model (Model Garden) where it's good enough, with the cost saved and the quality lost, measured
* **Workflow agents:** the Challenge 3 system rebuilt with ADK's sequential and parallel agents (Competitor and Market in parallel), and as a graph workflow. Compared on your eval set
* **Agent Registry:** Northgate's agents, tools and MCP servers registered, so another team could discover and call them. At least one **Google Cloud MCP server** (e.g. for BigQuery) connected
* **Runtime choice:** the same agent deployed on **Agent Runtime, Cloud Run and GKE**, compared on cost, cold start, scaling and operational effort
* **Continuous evaluation:** the **Gen AI evaluation service** plus your ADK evalset running on a schedule against production traffic, alerting on a drop in tool-call success
* **Troubleshooting:** find and fix one reasoning loop, one slow tool call and one hallucination using Cloud Trace and Cloud Logging, and write each one up

#### Non-technical

* An architecture decision record for each choice: retrieval service, model per agent, runtime

### Reading References

* Official exam guide, sections 3–4: [Professional Agentic Architect exam guide](https://services.google.com/fh/files/misc/professional_agentic_architect_exam_guide_english.pdf)
* [ADK — Multi-agent design patterns](https://adk.dev/workflows/patterns/) · RAG Engine · Vector Search · Agent Registry · Gen AI evaluation service

### Tips

* GKE and Vector Search have real idle costs. Deploy, measure, and destroy them in a window.

---

## Challenge 12: Security and Governance *(added — Agentic Architect §5)*

### Scenario Overview

Before Northgate lets the analyst act on behalf of a real relationship manager, security wants four answers. Whose identity does the agent use when it calls a tool? What's the most it could ever reach? Who can see what it's doing? And what stops client data leaking into prompts and logs?

Challenge 4 covered traffic from the client to the agent. This challenge covers everything else.

### Definition of Done

#### Technical

* **OAuth 2.0 for agent-to-tool calls** via Auth Manager: one tool acting **on behalf of the RM** (e.g. saving a report to their own Drive or adding a reminder to their calendar), with the user's identity propagated rather than a shared service account
* **Principal access boundary (PAB) policies** with Agent Identity, so each agent's maximum reach is capped even if someone grants it too much. Show a call it can't make
* **Agent Gateway egress:** traffic from the agent out to tools and third-party services monitored and filtered, with Model Armor on tool responses (closing the indirect-injection gap from Challenge 4)
* **Governance:** agent policies and Agent Registry controlling which agents may call which tools
* **Sensitive Data Protection:** client names and personal data detected and masked before they reach a prompt, a log line or a trace
* **Human-in-the-loop** (from Challenge 6) documented as part of the safety framework

#### Non-technical

* A threat model covering every path: user → agent, agent → tool, agent → agent, and data at rest in sessions, memory and logs. For each path, list the control and how you proved it works

### Reading References

* Official exam guide, section 5: [Professional Agentic Architect exam guide](https://services.google.com/fh/files/misc/professional_agentic_architect_exam_guide_english.pdf)
* Agent Identity · Auth Manager · Agent Gateway · Model Armor · Agent Registry · Sensitive Data Protection

### Tips

* Use synthetic client data only. The point is to prove the controls, not to handle real client information.
