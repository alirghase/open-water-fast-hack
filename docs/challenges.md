# Challenges

Northgate Bank — UK Market Entry & Competitive Intelligence Analyst.

The brief below is the challenge text as issued: scenario, definition of done, reading references, and tips. Work through it in order. Challenge 1 has no tools. Challenge 2 adds one data source. Challenge 3 splits the work across four agents.

The reading-reference titles are unchanged. Each one is linked to the public page it names. [fastlane.haron.app/#/attendee](https://fastlane.haron.app/#/attendee) is login-only, so these are the public docs, not a copy of the hrefs inside that app.

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
