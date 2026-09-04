# Project mind map

This document answers one question: **what lives in here and how the pieces
connect.** For the temporal sequence, what to run first and what to run next,
see [roadmap.md](roadmap.md).

The diagrams are Mermaid. They render directly on GitHub and in VS Code's
Markdown preview.

---

## 1. The whole project

```mermaid
mindmap
  root((LinkedIn Growth))
    Input
      LinkedIn data export
      profile.yaml reviewed by hand
      voice.md with past posts
      goal written by you
    Core
      principles.py
        Honesty
        Positioning
        Five pillars
        Writing rules
        Editor rubric
      config.py
        Keys and paths
        Opus 5 for judgement
        Sonnet 5 for volume
        Shared SQLite
      context.py
        Whole profile in the prompt
        No RAG, by decision
        Cached per run
    Agents
      Profile Diagnosis
      Profile Writer
      Content Strategist
      Researcher
      Editorial Planner
      Writer
      Editor
      Publisher
    Orchestration
      Team in coordinate mode
        linkedin chat
        agent_ui in the browser
      Deterministic workflows
        post_flow
        week_flow
      CLI with Typer
      AgentOS on port 7777
    Tools
      Files
        save_artifact
        read_artifact
        list_artifacts
        today
      Web
        recent_search
        broad_search
      LinkedIn
        check_linkedin_connection
        publish_post
    Output
      diagnosis.md
      optimized_profile.md
      strategy.md
      weekly calendar
      posts in pt and en
      Published post in the feed
    Feedback
      metrics.csv by hand
      Feeds the strategist
      Adjusts the pillars
```

---

## 2. How the artifacts depend on each other

An arrow means **"reads"**. No agent invents context: either the fact is in the
profile, or it is in an artifact another agent already wrote.

```mermaid
flowchart TD
    EXPORT["LinkedIn export<br/>profile/linkedin_export/*.csv"] --> YAML["profile/profile.yaml<br/><i>source of truth</i>"]
    EXPORT --> VOICE["profile/voice.md<br/><i>tone sample</i>"]

    YAML --> CTX["profile_context<br/><i>injected into every agent</i>"]
    VOICE --> CTX

    CTX --> DIAG["content/diagnosis.md"]
    CTX --> PROF["content/optimized_profile.md"]
    CTX --> STRAT["content/strategy.md"]
    CTX --> CAL["content/calendar/YYYY-Wxx.md"]
    CTX --> POST["content/posts/YYYY-MM-DD-topic.md"]

    DIAG --> PROF
    DIAG --> STRAT
    MET["content/metrics.csv<br/><i>filled in by you</i>"] --> STRAT
    STRAT --> CAL
    CAL -.->|topic of the day| POST
    POST --> PUB(["Post published on LinkedIn"])
    PUB -.->|days later, by hand| MET

    classDef input fill:#e8f0fe,stroke:#4a6fa5,color:#1a2332
    classDef output fill:#e9f5ec,stroke:#4a8a5e,color:#1a2332
    classDef external fill:#fdf0e3,stroke:#b07d3a,color:#1a2332
    class EXPORT,YAML,VOICE,MET input
    class DIAG,PROF,STRAT,CAL,POST output
    class PUB external
```

The loop closes at `metrics.csv`. Without it the system produces forever but
never learns what worked.

---

## 3. The eight agents

They all inherit `base_instructions()` from `principles.py` and receive the
whole profile in `additional_context`. What differs between them is the role,
the tools and the model.

| Agent | Role | Tools | Model | Writes |
|---|---|---|---|---|
| **Profile Diagnosis** | Audits the profile against real job posts and scores each section 0 to 10 | `broad_search`, `save_artifact` | Opus 5 | `diagnosis.md` |
| **Profile Writer** | Headline, About, experiences, projects and skills, pt + en | `read_artifact`, `save_artifact` | Opus 5 | `optimized_profile.md` |
| **Content Strategist** | Positioning, audience, pillars, cadence, metrics, first 30 days | `read_artifact`, `save_artifact` | Opus 5 | `strategy.md` |
| **Researcher** | What happened in AI this week, with a personal angle per item | `recent_search`, `today` | Sonnet 5 | nothing, it feeds another agent |
| **Editorial Planner** | A calendar with six fields per post, including the proof asset | `today`, `read_artifact`, `list_artifacts`, `save_artifact` | Opus 5 | `calendar/YYYY-Wxx.md` |
| **Writer** | Writes the post in Portuguese and rewrites it for an international reader | `read_artifact` | Opus 5 | nothing, it hands off to the Editor |
| **Editor** | Applies the seven-criteria rubric, cuts and finalizes | `today`, `save_artifact` | Opus 5 | `posts/YYYY-MM-DD-topic.md` |
| **Publisher** | The last gate before the public. Checks the token, extracts the body, publishes | `check_linkedin_connection`, `read_artifact`, `list_artifacts`, `publish_post` | Sonnet 5 | nothing, it publishes |

**Why Sonnet in two of them:** the Researcher and the Publisher do volume and
execution work, not judgement. Opus there would be money spent for no gain.
Swappable in `.env` through `MAIN_MODEL` and `FAST_MODEL`.

---

## 4. The three ways to drive the system

The same set of agents is exposed through three different surfaces. They do not
compete; each one serves a different moment.

```mermaid
flowchart LR
    subgraph YOU["You"]
        CLI["Terminal<br/>uv run linkedin ..."]
        WEB["Browser<br/>localhost:3000"]
    end

    subgraph SYS["The system"]
        direction TB
        WF["Workflows<br/><i>fixed order, no decision</i>"]
        TEAM["Team coordinate<br/><i>the leader picks who does it</i>"]
        AG["Single agent<br/><i>direct call</i>"]
    end

    subgraph EXEC["The eight specialists"]
        A8["Diagnosis · Profile · Strategist<br/>Researcher · Planner<br/>Writer · Editor · Publisher"]
    end

    CLI -->|post, calendar| WF
    CLI -->|chat| TEAM
    CLI -->|diagnose, profile, strategy| AG
    WEB -->|AgentOS :7777| TEAM
    WEB --> AG

    WF --> A8
    TEAM --> A8
    AG --> A8

    classDef you fill:#e8f0fe,stroke:#4a6fa5,color:#1a2332
    classDef sys fill:#f4f1e8,stroke:#8a7a4a,color:#1a2332
    class CLI,WEB you
    class WF,TEAM,AG sys
```

**When to use each:**

- **Workflow** (`post`, `calendar`): the order of the steps is already known.
  Research, write, edit, save. It spends no tokens deciding who does what, and
  the result is the same every time. This is the production path.
- **Team** (`chat`, or the web UI in Team mode): you do not know in advance who
  needs to answer. The leader reads the request, delegates and synthesizes. This
  is the conversation path.
- **Single agent** (`diagnose`, `profile`, `strategy`): one task, one
  specialist, no middleman.

The `agent_ui` only sees Agents and Teams. Workflows exist in AgentOS over HTTP
but do not show up in the chat. Run those from the CLI.

---

## 5. Anatomy of an agent

Every `build()` in `agents/` assembles the same structure. Understand one and
you understand all eight.

```mermaid
flowchart TB
    subgraph AGENT["Agno Agent"]
        direction TB
        DESC["description<br/><i>who it is</i>"]
        INST["instructions<br/><i>base_instructions + role rules</i>"]
        CTX["additional_context<br/><i>the user's real data + voice</i>"]
        TOOLS["tools<br/><i>what it can do in the world</i>"]
        MOD["model<br/><i>Opus 5 or Sonnet 5</i>"]
        DB["db<br/><i>session SQLite</i>"]
        LIM["tool_call_limit<br/><i>spend ceiling</i>"]
    end

    PRINC["principles.py"] --> INST
    PROFILE["profile.yaml + voice.md"] --> CTX
    CONF["config.py"] --> MOD
    CONF --> DB

    classDef source fill:#e8f0fe,stroke:#4a6fa5,color:#1a2332
    class PRINC,PROFILE,CONF source
```

**The repository's golden rule:** behaviour changes in
`agents/principles.py`, not across eight files. That is where honesty,
positioning, the five pillars, the writing rules, the forbidden list and the
Editor's rubric live.

---

## 6. File map

```
profile/                         your data, out of git
  linkedin_export/               the LinkedIn .zip, unpacked
  profile.yaml                   generated and hand-reviewed · source of truth
  voice.md                       up to 25 past posts, as a tone sample

content/                         everything the system produces
  diagnosis.md                   profile audit against real job posts
  optimized_profile.md           copy ready to paste, pt and en
  strategy.md                    positioning, pillars, cadence
  calendar/YYYY-Wxx.md           editorial calendar by ISO week
  posts/YYYY-MM-DD-topic.md      post in pt and en + the Editor's evaluation
  metrics.csv                    filled in by you, by hand

src/linkedin_growth/
  config.py                      secrets, paths, models, database
  profile/
    schema.py                    the profile's Pydantic contract
    importer.py                  reads the CSVs, tolerant of variation
    context.py                   profile -> markdown for the prompt
  tools/
    artifacts.py                 read, save, list, confined to content/
    search.py                    web search via DDGS, no API key
    linkedin.py                  official API: token, URN, payload, publishing
  agents/
    principles.py                the codified strategy · start here
    <eight files>                one build() each
  team.py                        the coordinating Team
  flows.py                       the two workflows
  cli.py                         the thirteen commands
  agentos.py                     the web interface server

agent_ui/                        the Next.js interface, on :3000
tmp/linkedin_growth.db           the agents' sessions, history and memory
docs/                            this map and the roadmap
```

---

## 7. The system's boundaries

Three limits are structural. They are not missing implementation, they are what
LinkedIn allows, and they explain the shape of half the artifacts.

```mermaid
flowchart LR
    subgraph OK["What the API allows"]
        P1["Publish a text post"]
        P2["Identify the token's owner"]
    end

    subgraph NONE["What does not exist"]
        N1["Read your own profile<br/>→ hence the data export"]
        N2["Edit headline, About,<br/>experiences, projects<br/>→ hence the 'paste into:' lines"]
    end

    subgraph BLOCKED["What is restricted"]
        B1["Post metrics<br/>→ hence metrics.csv by hand"]
        B2["List published posts"]
    end

    classDef ok fill:#e9f5ec,stroke:#4a8a5e,color:#1a2332
    classDef none fill:#fdeaea,stroke:#a55,color:#1a2332
    classDef blocked fill:#fdf0e3,stroke:#b07d3a,color:#1a2332
    class P1,P2 ok
    class N1,N2 none
    class B1,B2 blocked
```

The system uses **only** the official API, with your consent. No scraping, no
session cookie, no driven browser, no automated connections or messages. All of
that violates the Terms of Use and gets accounts banned.

And everything is destined for **your personal profile**: the post's author is
`urn:li:person:<you>`. The Company Page exists only because LinkedIn requires
one to register any developer app.
