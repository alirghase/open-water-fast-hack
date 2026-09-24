# 05 — Deploy runbook: Agent Runtime, via the Google Agents CLI (`adk`)

How `northgate_analyst` gets from local code to a live, IAM-identified deployment
on Agent Runtime, and how to redeploy it after an edit. Written so a future
challenge (2–4) can repeat this without re-discovering the same gotchas.

---

## 0. One-time prerequisites

```bash
cd ~/projects/fast-lane-hack
uv add "google-cloud-aiplatform[adk,agent_engines]"   # ADK's deploy path needs this SDK
gcloud config configurations activate fast-lane-hack   # isolated gcloud identity for this project
```

**The ADC gotcha.** `gcloud auth login` authenticates the CLI, but `adk deploy`
needs *Application Default Credentials*, which `gcloud auth login` does **not**
create. Running deploy without this fails with `Your default credentials were
not found`. Fix — point at the account's existing legacy credential file
instead of running the separate interactive `gcloud auth application-default
login`:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/legacy_credentials/hacker008@20260924.gcphack.com/adc.json"
```

Set this in every shell before `adk deploy`. (Swap the account folder name if a
future challenge uses a different one — check `~/.config/gcloud/legacy_credentials/`.)

---

## 1. Scaffold (one time per agent)

```bash
uv run adk create northgate_analyst \
    --model gemini-3.5-flash \
    --project lloyds-hack-team-04 \
    --region global
```

`--model` must be passed explicitly — `adk create` otherwise prompts
interactively, which hangs in a non-interactive shell.

This generates exactly `northgate_analyst/{__init__.py, agent.py, .env}` —
confirmed straight from ADK's own source (`cli_create.py`'s `_SUCCESS_MSG_CODE`).
Build and iterate the persona against this bare three-file shape, with the
system prompt as the `instruction=` string directly inside `agent.py` — not
split into a separate module. Extra scaffolding (`.agent_engine_config.json`,
`requirements.txt`, the generated Dockerfile) belongs to the deploy step, not
the persona-authoring step; see §3 below. (An earlier version of this repo
split the prompt into its own `instruction.py`; it was folded back inline to
match the scaffold this brief specifies.)

---

## 2. The region split — the single biggest gotcha

**`gemini-3.5-flash` only resolves via the `global` Vertex AI location.** A call
to `us-central1` for this model 404s. But **reasoning engines (the deployed
agent resource) have no `global` endpoint** — `.../locations/global/reasoningEngines`
404s too. So the two things that need a location disagree, and both are right:

| What | Location | Why |
|---|---|---|
| The deployed engine resource | `us-central1` | No `global` reasoningEngines endpoint exists |
| The model call the agent makes at runtime | `global` | Only location `gemini-3.5-flash` serves from |

The split is carried by `GOOGLE_CLOUD_LOCATION=global` in `northgate_analyst/.env`.
ADK reads `.env` and folds its keys into the container's runtime environment
variables — this survives even though `--region us-central1` (passed to the
deploy command) sets the *engine's* location. Confirmed live: the deployed
engine's `deploymentSpec.env` shows `GOOGLE_CLOUD_LOCATION=global` even though
the resource path itself says `.../locations/us-central1/...`.

If a future agent uses a model that resolves fine in `us-central1`, this whole
split is unnecessary — it exists only because of this specific model's location
restriction. Check with a direct `generateContent` call before assuming the
split is needed:

```bash
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/us-central1/publishers/google/models/<MODEL>:generateContent" \
  -d '{"contents":[{"role":"user","parts":[{"text":"hi"}]}],"generationConfig":{"maxOutputTokens":8}}'
```
404 → the model needs `global` (or another specific location); check there instead.

---

## 3. Agent Identity — how it's actually configured

`adk deploy agent_engine` has **no CLI flag** for identity. It's set via a
config file ADK reads from the agent folder:

**`northgate_analyst/.agent_engine_config.json`:**
```json
{
  "display_name": "Northgate Analyst",
  "description": "Northgate Bank UK Market Entry & Competitive Intelligence Analyst (persona-only build).",
  "identity_type": "AGENT_IDENTITY"
}
```

**Two traps:**

1. **Key must be `identity_type` (snake_case), not `identityType`.** The
   receiving pydantic model (`AgentEngineConfig`) has `extra="forbid"` — a
   misspelled or wrong-case key is a hard validation error at deploy time, not
   a silent no-op.
2. **Never set `service_account` alongside `identity_type: AGENT_IDENTITY`.**
   The API's own field docs say the two are mutually exclusive; `AGENT_IDENTITY`
   means the engine gets its own principal, not a shared service account.

No fallback (direct SDK call, REST PATCH) was needed — ADK passes this config
straight through to `client.agent_engines.create/update(config=...)`, which
sets `spec.identity_type` on the real API request.

---

## 4. Deploy

```bash
cd ~/projects/fast-lane-hack   # must run from here — uv resolves the venv relative to cwd
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/legacy_credentials/hacker008@20260924.gcphack.com/adc.json"

uv run adk deploy agent_engine \
    --project=lloyds-hack-team-04 \
    --region=us-central1 \
    --display_name="Northgate Analyst" \
    --agent_engine_id=4755849035259052032 \
    northgate_analyst
```

**`--agent_engine_id` is what makes this an update, not a new deployment.**
Omit it only for a genuinely first-ever deploy of a new agent — once you have
an ID, always pass it back in, or every redeploy spins up a new, separate
resource instead of updating this one.

Successful output ends with:
```
Deployed to Agent Platform: projects/<project>/locations/us-central1/reasoningEngines/<id>
```

---

## 5. Verify identity actually took effect

Don't trust the deploy log alone — confirm against the live resource:

```bash
TOKEN=$(gcloud auth print-access-token)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/us-central1/reasoningEngines/<ID>" \
  | python3 -c "
import json,sys
spec = json.load(sys.stdin)['spec']
print('identityType:', spec.get('identityType'))
print('effectiveIdentity:', spec.get('effectiveIdentity'))
"
```

Expect:
```
identityType: AGENT_IDENTITY
effectiveIdentity: agents.global.org-<org-id>.system.id.goog/resources/aiplatform/projects/<project-number>/locations/<region>/reasoningEngines/<id>
```

If `effectiveIdentity` instead looks like `service-<project>@gcp-sa-aiplatform-re.googleapis.com`
or a `...@<project>.iam.gserviceaccount.com` address, Agent Identity did **not**
apply — check `.agent_engine_config.json` for the snake_case/`service_account`
traps above and redeploy.

**Second confirmation, from the console (no API call needed):** Agent Platform
→ Agents → Deployments → the agent → **Identity** tab shows the same
`principal://agents.global.org-.../reasoningEngines/<id>` string directly.

---

## 6. Smoke-test the live deployment

Console Playground (`Playground` tab, same page as Identity) is the fastest
manual check — type a prompt, confirm a real response comes back.

For a scripted check, this repo has a vendored client
(`lloyds-agenticai-hack-resources/challenge4/ask_agent.py`) that calls the
deployed engine directly:

```bash
cd lloyds-agenticai-hack-resources
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/legacy_credentials/hacker008@20260924.gcphack.com/adc.json"
uv run --project ~/projects/fast-lane-hack python challenge4/ask_agent.py --raw "who are you?"
```

Use `--raw` — the client has a pre-existing bug where plain runs report "no
text found" on a perfectly healthy response, because it only parses
SSE-prefixed lines and this route returns bare JSON.

That client's own `.env` needs `PROJECT_ID` / `LOCATION_ID=us-central1` /
`RESOURCE_ID` filled in with the values from step 4 — it's a separate script
with no import relationship to `northgate_analyst/`, so it needs the deployed
coordinates spelled out explicitly.

---

## 7. Redeploying after any future change

Same command as step 4, unchanged. `adk deploy` repackages the current
`northgate_analyst/` folder every time, so editing the `INSTRUCTION` string in
`agent.py` (or anything else in the agent folder) and re-running step 4 is the
entire update workflow. Re-run step 5 after any redeploy — identity is a
property of the deployed resource, not something set once and forgotten, and a
config mistake in a later edit could silently drop it.

---

## 8. Considered and declined: splitting `INSTRUCTION` into ADK skills

ADK genuinely has a skill-loading system (`google.adk.skills` / `SkillToolset`)
that works like Claude Code's — an `<available_skills>` block of name+description
stays resident in context, and the model calls `load_skill()` to pull in full
content only when it judges a skill relevant. It was considered for splitting the
persona's four rule categories (Voice/Scope/Boundaries/Usefulness) into 4 skills
plus a meta-skill router, to reduce token footprint.

**Declined, for two reasons:**

1. **Coverage risk.** All four categories apply on essentially every turn — there's
   no clean topic-conditional subset. The boundary rules (`B-#`) specifically exist
   to help recognize subtle fabrication traps; if lazy-loaded, the model would need
   to already recognize a trap *before* deciding to load the rules that teach it
   what a trap looks like. That gap is exactly the failure mode this persona exists
   to prevent.
2. **The token-saving premise doesn't hold here.** Gemini/Vertex auto-caches the
   repeated system instruction for free, no code required — observed live in this
   project: a single-turn call showed `prompt_token_count: 2836` with no cache
   fields; by the third turn of that session, `cached_content_token_count` had
   grown to `6073`. Splitting into skills would add tool-call overhead
   (`search_skills`/`load_skill` schemas + round trips) and destabilize the prompt
   prefix (since which skills load can vary turn to turn), working against caching
   rather than with it.

**What was done instead:** a straight editorial trim of the same instruction — same
36 rule IDs, same meaning, ~11% less text, confirmed via a live A/B: the flagship
mandate case's `prompt_token_count` dropped from 2836 to 2576 (~9%) after the trim,
with identical persona behavior (re-verified against the MAN-01, U-10, and
placeholder-trap regression cases post-redeploy).

**Where the real skill system is a legitimate fit:** once a later challenge adds
tools, genuinely conditional procedural knowledge (e.g. "how to query Companies
House," "how to interpret an ONS survival-rate table") is exactly what
`SkillToolset` is for — narrow, topic-triggered, safe to omit when irrelevant.
Universal persona/safety rules are not that shape.

---

## Quick reference — this deployment's actual values

| | |
|---|---|
| Project | `lloyds-hack-team-04` |
| Engine region | `us-central1` |
| Model | `gemini-3.5-flash` (via `global`) |
| Resource ID | `4755849035259052032` |
| Full resource name | `projects/lloyds-hack-team-04/locations/us-central1/reasoningEngines/4755849035259052032` |
| Identity | `AGENT_IDENTITY` |
