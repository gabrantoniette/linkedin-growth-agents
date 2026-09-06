# LinkedIn Growth: a multi-agent system for AI engineering

A team of eight [Agno](https://github.com/agno-agi/agno) agents that works on
your LinkedIn profile so AI engineering recruiters can find you: it audits the
profile, rewrites the copy, defines the content strategy, plans the calendar,
writes the posts in Portuguese and English, reviews them against a rubric and
publishes through the official API.

It was built for a specific case: **someone moving into AI with no experience in
the field yet.** The whole strategy follows from that. With no track record to
claim, what works is evidence (projects, code, study notes) presented well. The
system is instructed never to invent experience.

**A note on language.** The codebase, docs and tests are in English. The posts
the agents produce are in Brazilian Portuguese, because that is the audience
they are written for, so the prompt text that shapes those posts, and the
reference files behind it, stay in Portuguese on purpose.

**The project in diagrams:** [docs/roadmap.md](docs/roadmap.md) walks the
end-to-end cycle stage by stage. [docs/mindmap.md](docs/mindmap.md) maps the
pieces and how they connect.

---



## Getting started



### 1. Dependencies

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```



### 2. Anthropic key

```bash
cp .env.example .env
```

Fill in `ANTHROPIC_API_KEY` with your key from the
[Anthropic console](https://console.anthropic.com/settings/keys).

### 3. Your real data

LinkedIn does **not** let you read your own profile through an API. The official
route is the data export:

1. LinkedIn -> **Settings & Privacy** -> **Data privacy** -> **Get a copy of
   your data**
2. Choose the complete archive and request it. The email arrives in minutes, or
   up to 24 hours.
3. Unzip it into `profile/linkedin_export/`
4. Run:

```bash
uv run linkedin import
```

That generates `profile/profile.yaml`. **Open it and review it.** It is every
agent's source of truth: whatever is wrong there comes out wrong everywhere.
Fill in the `goal` field in your own words in particular. Re-importing does not
erase what you wrote there.

If you have past posts, the importer also generates `profile/voice.md`, which
the agents use to write in your tone instead of generic LLM tone.

### 4. Run the cycle

```bash
uv run linkedin status          # what exists and what the next step is
uv run linkedin diagnose        # audits the profile against real AI job posts
uv run linkedin profile         # copy ready to paste into LinkedIn
uv run linkedin strategy        # positioning, pillars and cadence
uv run linkedin calendar --weeks 2
uv run linkedin post --topic "how have you kept your RAG system's quality up?"
```

Everything lands in `content/`.

---



## Connecting LinkedIn (to publish)

Only needed for the `publish` command. Everything else works without it.

1. **Create a LinkedIn Page** if you do not administer one
   ([create one](https://www.linkedin.com/company/setup/new/)). Every app has to
   be associated with a Page; it can be your own, with no content.
2. **Create the app** at [https://www.linkedin.com/developers/apps](https://www.linkedin.com/developers/apps)
   and associate it with the Page. Confirm the verification (you approve it
   yourself, as the Page admin).
3. On the **Products** tab, add:
   - **Share on LinkedIn** -> grants the `w_member_social` scope
   - **Sign In with LinkedIn using OpenID Connect** -> grants `openid` and
     `profile`

   Both are granted immediately, with no partner approval.
4. **Generate the token** at
   [https://www.linkedin.com/developers/tools/oauth/token-generator](https://www.linkedin.com/developers/tools/oauth/token-generator),
   ticking `openid`, `profile` and `w_member_social`.
5. Paste it into `LINKEDIN_ACCESS_TOKEN` in `.env` and check it:

```bash
uv run linkedin connection
```

**The token lasts 60 days.** Automatic refresh only exists for approved
partners, so when it expires you just generate another one in the same place.

### Publishing

```bash
uv run linkedin publish content/posts/2026-09-02-topic.md --dry-run     # see the JSON
uv run linkedin publish content/posts/2026-09-02-topic.md               # publish
uv run linkedin publish content/posts/2026-09-02-topic.md --language en # English version
```

It always asks for confirmation before sending. A published post is public and
immediate.

---



## Web interface

The repository ships the [Agno Agent UI](https://github.com/agno-agi/agent-ui)
in `agent_ui/`. In two terminals:

```bash
uv run linkedin serve          # backend on :7777
```

```bash
cd agent_ui && pnpm dev        # interface on :3000
```

Open [http://localhost:3000](http://localhost:3000), pick **Team** mode and talk
to the team.

The UI only knows Agents and Teams. The flows (`post`, `calendar`) run from the
CLI.

---



## What can and cannot be automated

LinkedIn is restrictive, and the system is honest about it.


|                                                 |                                                                                       |
| ----------------------------------------------- | ------------------------------------------------------------------------------------- |
| Publish a post (text, image, PDF)               | **Automated**, through the official API                                                |
| Read your own profile                           | **No API exists.** Hence the data export                                               |
| Edit headline, About, experiences, projects     | **No API exists, at any tier.** The system hands you the text and says where to paste  |
| Read your own posts' metrics                    | **Blocked** by LinkedIn (restricted access). You record them by hand with `linkedin metrics` |
| List already-published posts                    | **Blocked** (`r_member_social` is closed)                                              |


The system uses **only** the official API, with your consent. No scraping, no
session cookie, no browser driving, no automated connections or messages. All of
that is forbidden by LinkedIn's Terms of Use and gets accounts banned.

### The learning loop

Since the metrics do not come through an API, they go in by hand:

```bash
uv run linkedin metrics
```

That feeds `content/metrics.csv`, which the strategist reads to adjust the
pillars. Without it, the system never learns what works for you.

---



## Memory

The system remembers from one conversation to the next. There are three layers,
and it is worth knowing which is which, because they fail in different ways.

| Layer | What it keeps | Where it lives | Who reads it |
| --- | --- | --- | --- |
| Profile | Your real, verifiable data | `profile/profile.yaml` | every agent, every run |
| Conversation | The last turns, verbatim | a session in SQLite | the team and the agents with history |
| Memory | Distilled sentences about you | `agno_memories`, tied to your user | every agent, every run |

**The team is what writes memory, in conversation.** That is where you say what
you prefer, what you built and what got results. The CLI commands always receive
the same canned request, so they learn nothing new, but they read everything. In
practice: you mention in chat that a post earned a recruiter contact, and next
week's `linkedin post` already knows.

What is worth keeping (and what is not) is written in `agents/principles.py`, in
the `memory_instructions` function.

### Seeing and deleting

```bash
uv run linkedin memory                    # what the system learned about you
uv run linkedin memory --forget a1b2c3d4  # delete one
uv run linkedin memory --clear            # delete everything (asks first)
```

Memory you cannot inspect is memory you cannot trust. If an agent starts
repeating nonsense, this is where you find out where it came from.

### Separate conversations

```bash
uv run linkedin chat                        # continues the "main" conversation
uv run linkedin chat --session experiment   # a parallel line that does not mix
```

History is per session; memory is per user. So what you said in the `experiment`
conversation does not show up in `main`, but whatever became memory applies to
both.

---



## How it is organized

```
profile/                      your data (out of git)
  linkedin_export/            the LinkedIn export, unzipped
  profile.yaml                generated and reviewable, the source of truth
  voice.md                    samples of your writing

content/                      what the system produces (out of git)
  diagnosis.md                profile audit
  optimized_profile.md        copy ready to paste
  strategy.md                 positioning and pillars
  calendar/YYYY-Wxx.md        editorial calendar
  posts/YYYY-MM-DD-topic.md   posts in pt-BR and English
  metrics.csv                 filled in by you

references/                   supporting material, read-only (produces nothing)
  hooks.md                    hook formulas, one per pillar
  linkedin-algorithm.md       LinkedIn format and timing heuristics
  ai-vocabulary.md            vocabulary and tics that give away AI text
  headline-formulas.md        headline formula for the Profile Writer

src/linkedin_growth/
  config.py                   secrets, paths, models, database, memory
  profile/                    schema, importer and context
  tools/                      artifacts, references, web search, LinkedIn API
  agents/                     the eight specialists
    principles.py             the codified strategy, start here
  team.py                     the coordinating team (chat)
  flows.py                    the deterministic workflows
  cli.py                      the commands
  agentos.py                  the web interface server

docs/
  roadmap.md                  the end-to-end cycle, stage by stage
  mindmap.md                  the map of the pieces and how they connect

tests/                        the suite, no test calls a paid API
  conftest.py                 fixtures, the @tool helper and the SpyModel
  test_artifacts.py           confinement to content/, writing and reading
  test_references.py          read-only lookups into references/
  test_linkedin_format.py     little text format and payload assembly
  test_importer.py            reading the LinkedIn export CSVs
  test_schema.py              the profile data contract
  test_principles.py          invariants of the codified strategy
  test_agent_memory.py        what the system remembers, and what must not leak
  test_cli_memory.py          the command that shows and deletes memory
  test_flows.py               what each workflow step actually reads
  test_agentos.py             what the web interface needs from the server
```



### The eight agents


| Agent              | Does                                                          |
| ------------------ | ------------------------------------------------------------- |
| Profile Diagnosis  | Searches real AI job posts and scores each profile section    |
| Profile Writer     | Headline, About, experiences, projects and skills, pt and en  |
| Content Strategist | Positioning, pillars, audience, cadence, metrics              |
| Researcher         | What happened in AI this week, with an angle for you          |
| Editorial Planner  | A calendar with a specific topic and proof asset per post     |
| Writer             | Writes the post in Portuguese and English                     |
| Editor             | Scores against a seven-criteria rubric and finalizes          |
| Publisher          | Publishes through the API, always with approval               |




### Where to change things first

`src/linkedin_growth/agents/principles.py` concentrates the strategy: the
honesty rules, the positioning, the content pillars, the writing rules and the
editor's rubric. Changing how the system behaves means changing that file, not
seven agent files.

### Adding reference material

This project uses [Agno](https://github.com/agno-agi/agno) agents, not Claude
Skills, so there is no mechanism to simply "install" a `SKILL.md`. The pattern
adopted here for porting external knowledge (for example from
[sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills))
is:

1. Curate the relevant content, adapted to this project's context rather than
   pasted, as a new `.md` in `references/`.
2. Give the agent that needs it the `read_reference` tool
   (`tools/references.py`) and an instruction saying when to call it.

That mirrors the progressive disclosure of Claude Skills: the content only
enters the agent's context when it decides it needs it, instead of inflating
every prompt. A short universal rule (one line, true of every post) goes
straight into `principles.py`; long content, or content consulted only
occasionally, goes into `references/`.

---



## Tests

```bash
uv run pytest              # the whole suite, ~10s
uv run pytest -k linkedin  # one subject only
```

On Windows, if `linkedin serve` is running in another terminal, `uv run` fails
while syncing the environment (it cannot replace `linkedin.exe`, which is in
use). Use `uv run --no-sync pytest` without stopping the server.

**No test calls the Anthropic API or the LinkedIn API.** The suite covers pure
logic and disk I/O: the confinement of the file tools (an agent cannot write
outside `content/`), LinkedIn's *little text format* (escaping and hashtags),
reading the export CSVs (which arrive with a preamble and varying column names)
and the invariants of `principles.py`.

That last group is the least obvious and the most useful: since the strategy is
the product, the tests pin down that certain rules keep reaching every agent
(honesty is disqualifying, the rubric has its seven criteria) and lock in rules
that were decided for a reason, like the hashtag limit.

The memory tests (`test_agent_memory.py`) run real agents, with a `SpyModel` in
place of `Claude`. It is the only way to answer "does the agent remember?": the
answer is in the messages that reach the model, and only running them lets you
see it. The spy records every call, so the test can assert that memory reached
the prompt and, in the isolation tests, that it did **not** reach where it
should not have.

The ones in `test_agentos.py` hit the server through `TestClient`, with no open
port. They exist because a whole class of bug only shows up there: a field that
is read when the HTTP response is assembled and nowhere else in the system. That
is how the team disappeared from the web interface with nothing in the terminal
indicating an error.

What the suite does **not** cover: the quality of the text the agents generate.
That is not unit testing, it is evaluation, and today the Editor agent plays
that role, with the rubric.

---



## Cost

By default the judgement agents use `claude-opus-5` and the high-volume ones use
`claude-sonnet-5`. To spend less, in `.env`:

```
MAIN_MODEL=claude-sonnet-5
```
