# Research Brief: Assistant-Native Pre-Flight ("Option 1")

> **You are a research agent.** Your job is to investigate whether PROJECT.MD should pivot to the architecture described here, and to produce a written, evidence-backed recommendation. **Do not change product code.** Read this whole brief before starting.

- **Brief date:** 2026-09-29
- **Repository:** https://github.com/SundarReguraman/PROJECT.MD (public)
- **Branch with the latest code:** `fix/issues-1-6` (this brief lives on `research/assistant-native-preflight`, branched from it)
- **Your deliverable:** `docs/research/FINDINGS-assistant-native-preflight.md` (format in [§9](#9-deliverable-format))

> **Update (2026-09-29): the owner has chosen a concrete design.** §4.6 describes a **five-agent pack** that runs on top of the user's AI assistant. It is the **primary design to evaluate**; §4.1–4.5 are the general rationale behind it. Decisions already made: **Claude Code is the first target**, and **installation works both globally and per project**. Implementation waits for your findings, so answer RQ10–RQ12 as well as RQ1–RQ9.

---

## 0. Course corrections: read before continuing

> **Added 2026-09-29 after the owner reviewed the work in progress** in `docs/research/experiments/` (the files as of 16:55). These points **override** anything you've already built. Fix them before producing more.

**C1. Follow the method order in §6; it is not optional.**
- **Stop building prototypes** until two things are done:
  - the docs research for **RQ2, RQ10 and RQ11**, with cited sources;
  - the **RQ1 baseline** (no pack), with transcripts saved under `docs/research/experiments/baseline/`.
- RQ1 is the highest-priority question. If assistants already push back, the whole pack design changes.

**C2. Confirm the Claude Code formats you've assumed, with primary-doc links.** Specifically:
- Can a **skill** (`.claude/skills/<name>/SKILL.md`) be invoked explicitly as `/preflight <idea>`, or does an explicit command need `.claude/commands/<name>.md`? How are arguments passed to each?
- What syntax does the subagent frontmatter `tools` field take (comma-separated string vs YAML list)? Is `model: inherit` valid?
- Can a skill or command **launch subagents in parallel** and collect their outputs?
- Record the answers in the RQ2/RQ10 matrix. Rebuild the prototypes to match.

**C3. The five-agent prototype must be complete.**
- The orchestrator calls `arch-contracts`, `reliability-scale` and `security-privacy`, but only `researcher` and `stack-deps` exist.
- Create all five before running any five-agent experiment. Each needs a clear scope, which catalogue traps it owns, and an output format the orchestrator can merge.

**C4. Every arm must use the same catalogue, or RQ12 is invalid.**
- **Currently:**
  - the single-agent skill inlines **15** traps;
  - the five-agent `researcher` inlines **8**;
  - neither reads `catalogue_index.md` / `catalogue_detail.md`.
- **Required:**
  - **all 29 traps** live in the shared catalogue files only;
  - both packs **load them by reference** (e.g. "Read `catalogue_index.md`; open `catalogue_detail.md` for any trap that may apply");
  - no inline trap subsets in agent or skill prompts.
- Otherwise the experiment measures catalogue size, not one agent vs five.

**C5. Use PROJECT.MD's verdict semantics, not new ones.** The rules in the prototypes ("any CRITICAL trap → BLOCK"; "REVIEW = minor warnings, proceed") reintroduce a bug fixed in PR #11 (issue #1). The product's contract, from `project_md/agents/orchestrator.py`, is:

| Verdict | When | Behaviour |
| :--- | :--- | :--- |
| **BLOCK** | The user **explicitly chooses** a dead end ("use OpenCV to read handwriting", "store card numbers") | Refuse the anti-pattern, explain why, mandate the replacement |
| **REVIEW** | A **human decision** is needed that the assistant must not make alone: regulated data (health, finance, children), a copyleft licence, conflicting requirements | Proceed only after the user decides that point |
| **PASS** | Everything else, **including latent traps** the idea is merely *prone to* (e.g. "an app to read doctor handwriting") | The replacement is mandated in `PROJECT.md` as a guarded warning; the idea is not blocked |

- **Rejecting a dead end** ("I will NOT use OpenCV") is never a BLOCK.
- **When nothing in the catalogue matched,** PASS must say so ("no known traps matched"), not imply the idea was cleared.
- Update `protocol.md` and both skills to match.

**C6. Catalogue changes need sources, and must not name specific model versions.**
- **Every change to a trap** (new replacement, licence claim, API name) needs a **source link and access date**, or an **UNVERIFIED** label. There are currently no source links in the pack files.
- **Don't name specific LLM/VLM versions** in the catalogue ("GPT-4o", "Claude 3.5 Sonnet" and "Gemini 2.0 Flash" are already outdated, and any version name will date quickly). Write "a current vision-language model via API (e.g. from Anthropic, Google or OpenAI)" instead.
- **Verify or mark UNVERIFIED** at least these claims:
  - "Stripe Connect Accounts v2";
  - "YOLOX is Apache-2.0";
  - "GOT-OCR 2.0 / PaddleOCR-VL";
  - "NextAuth v4 → Auth.js v5";
  - "TensorFlow Lite → LiteRT".
- **GEO-002:** make sure the replacement doesn't recommend something the trap lists as an anti-pattern (haversine in application code over all rows).

**C7. Housekeeping.**
- Delete `docs/research/experiments/test.txt`.
- Never commit `.DS_Store` files.

---

## 1. Rules for this research

1. **Never push to `main`. Never merge or close PRs or issues.** Work only on the `research/assistant-native-preflight` branch, or leave files uncommitted for the owner to review.
2. **Follow the method order in §6 and the course corrections in §0.**
3. **Do not modify** `project_md/`, `tests/`, `CLAUDE.md`, `README.md` or `docs/PRD.md`. You may add files under `docs/research/`, plus throwaway experiment scripts under `docs/research/experiments/`.
4. **Cite everything.** Every factual claim about a tool, format, model behaviour, licence or statistic needs a source URL and the date you accessed it. Many of these products change monthly. Anything from memory rather than a source must be labelled **UNVERIFIED**.
5. **Separate what you observed from what you infer.** Label each finding **Verified** (you tested it or read primary documentation), **Reported** (secondary source), or **Assumed**.
6. **Prefer primary sources:** official docs, changelogs, specs, licence files and your own experiments over blog posts.
7. **Record negative results.** If an assistant ignores a rule file, or already pushes back on a trap without help, that is a key finding, not a failure.
8. **If a question can't be answered with available access,** say so and propose how it could be answered.

---

## 2. What PROJECT.MD is (read this first)

**Mission (from `CLAUDE.md` and `docs/PRD.md`):** a zero-prerequisite tool for beginners, "vibe coders" and hackathon teams. The user gives **one plain-English sentence** describing what they want to build. PROJECT.MD:
- catches **architectural dead ends** before any code is written;
- picks a sensible modern stack;
- generates **native context files** that AI coding assistants read automatically: `PROJECT.md`, `CLAUDE.md`, `.cursorrules`, `GEMINI.md` + `.agent/rules/`, `AGENTS.md`.

**Origin story (the canonical dead end):** a beginner asks an assistant to "use OpenCV to transcribe messy doctor handwriting". The assistant writes thousands of lines of contour and threshold hacks. Two weeks later testing fails completely: OpenCV is an image-processing toolkit with no handwriting recognition. The right tool was a handwriting-recognition model (e.g. TrOCR) or a vision-language model. **The PRD claims assistants "do not push back".** That claim has not been tested; see RQ1.

**Non-negotiable rules (`CLAUDE.md`):**
1. **Zero external dependencies:** Python standard library only; must run on Mac, Windows and Linux without `pip install`.
2. **One-shot UX:** never interrogate the beginner about databases, frameworks or layers; infer them.
3. **Evidence & truth:** every trap warning explains *why* the anti-pattern fails, in plain English, and mandates the modern replacement.

---

## 3. Current implementation (as of `fix/issues-1-6`, commit `766aab7`)

```
idea ─► knowledge-base scan (regex) ─► intent inference (regex)
             │
             ▼  5 agents in parallel (asyncio): dependency, architecture, contract, impact, security
             ▼  risk score + verdict: PASS / REVIEW / BLOCK
             ▼  exporters: PROJECT.md, CLAUDE.md, .cursorrules, GEMINI.md + .agent/rules/*.md, AGENTS.md
```

| Area | Path | Notes |
| :--- | :--- | :--- |
| Trap catalogue | `project_md/core/knowledge_base.py` | 29 traps, 13 domains. Each has regex `idea_patterns` (the domain), regex `anti_patterns` (naming the bad tool escalates to CRITICAL), `why_it_fails` and `recommended` |
| Intent inference | `project_md/core/intent.py` | Regex over the idea for constraints (offline, privacy...), platforms, language |
| Agents | `project_md/agents/*.py` | Rule-based and deterministic, **not LLM agents**. Each trap is owned by exactly one agent |
| Contracts | `project_md/agents/contract_agent.py` | Data-model templates for 7 app shapes; anything else gets a generic `Item` |
| Exporters | `project_md/exporters/` | One report → every assistant's file |
| CLI | `project_md/cli.py` | `python3 -m project_md.cli "idea"`; exit codes 0 PASS/REVIEW, 1 error, 3 BLOCK |
| Tests | `tests/` | 62 unittest tests, passing on Python 3.9 and 3.14 |

**Open PRs (stacked, unmerged):** #7 (docs) → #8 (engine) → #9 (CLI + exporters) → #10 (demo) → #11 (fixes for issues #1–#6).

### 3.1 The problem that triggered this research

Detection is **keyword/regex matching**. It works on the examples it was built around and fails on ordinary ideas. Here is a probe of 15 typical ideas that were never used to tune the patterns:

| Idea | Traps matched | Data models | What an expert would flag |
| :--- | :--- | :--- | :--- |
| A habit tracker app | DB-001 | Item | Push notifications/reminders; offline sync |
| A budgeting app that connects to my bank account | AUTH-001, DB-003 | **Product, Order** (wrong) | Bank aggregation API (e.g. Plaid), regulated financial data; never scrape bank sites |
| A study group finder for my university | – | Item | Matching, university SSO, location |
| An AI tutor that explains math problems step by step | AI-002 | Item | LLM arithmetic errors → use a solver/tool; cost control |
| A platform for local farmers to sell produce | – | Item | Marketplace payments/payouts (PAY-001), location search |
| A Chrome extension that summarizes articles | AI-002 | Item | API key must not ship in the extension; Manifest V3 limits |
| A fitness app that counts push-up reps using the camera | – | Item | **Pose estimation (MediaPipe), not hand-rolled OpenCV**: literally the origin-story trap class |
| A Spotify playlist generator based on mood | – | Item | Spotify API terms/rate limits, OAuth |
| A mental health journaling app | – (REVIEW via privacy) | Item | Sensitive data, encryption, crisis-content handling |
| A Discord bot for our gaming server | – | Item | Gateway intents, hosting, rate limits |
| An app to split bills with roommates | – | Item | Money as floats (DB-003), rounding rules |
| A portfolio website for artists | – | Item | Image hosting/CDN; static site is enough |
| A tool that turns lecture videos into flashcards | – | Item | Speech-to-text (Whisper), long jobs in background (QUEUE-001) |
| A smart home dashboard for my IoT sensors | DB-001 | Item | MQTT, time-series storage, polling vs push |
| A job board for remote internships | – | Item | Search (FTS), scraping ToS, spam |

**Result: 5 of 15 matched any trap; 14 of 15 got the placeholder `Item` model.** Each earlier fix round added patterns for the exact sentences that had failed (whack-a-mole). The deterministic infrastructure is sound; the *understanding* layer does not generalise.

### 3.2 The current trap catalogue (the curated expertise)

| ID | Domain | Severity | Dead end | Primary replacement |
| :--- | :--- | :--- | :--- | :--- |
| `OCR-001` | ocr | critical | Handwriting recognition with OpenCV or basic Tesseract | TrOCR (Hugging Face; run offline via ONNX Runtime) |
| `OCR-002` | ocr | warning | Parsing invoices, receipts or forms with regex over raw OCR text | Layout-aware extraction: Azure Document Intelligence, AWS Textract AnalyzeExpense |
| `OCR-003` | ocr | warning | Running OCR on PDFs that already contain text | Read the text layer first with pypdf or pdfplumber |
| `CV-001` | computer_vision | critical | Object detection with Haar cascades or hand-tuned OpenCV | YOLO (Ultralytics) or RT-DETR, fine-tuned |
| `CV-002` | computer_vision | critical | Face recognition by comparing pixels or histograms | Face embeddings: InsightFace/ArcFace or face_recognition |
| `CV-003` | computer_vision | warning | Running a heavy model on every video frame in a Python loop | Skip frames and track between detections (e.g. ByteTrack) |
| `AUTH-001` | auth | critical | Storing passwords yourself with plain text or fast hashes | Managed auth: Supabase Auth, Clerk, Auth0, Firebase Auth |
| `AUTH-002` | auth | warning | Long-lived JWTs in localStorage for browser sessions | httpOnly, Secure, SameSite session cookies |
| `AUTH-003` | auth | warning | Hand-rolling OAuth / social login | Auth.js (NextAuth), Authlib, or Passport strategies |
| `DB-001` | database | warning | Using JSON or CSV files as the application database | SQLite (single machine/offline) |
| `DB-002` | database | warning | MongoDB/NoSQL for highly relational data | PostgreSQL with foreign keys and transactions |
| `DB-003` | database | critical | Storing money as floating-point numbers | Integer minor units (cents) |
| `DB-004` | database | warning | Microservices and multiple databases for an MVP | Modular monolith |
| `QUEUE-001` | queue | warning | Doing slow work inside the HTTP request | Background worker; return a job id |
| `QUEUE-002` | queue | info | Kafka or RabbitMQ clusters for a small app | Redis + RQ/BullMQ |
| `CONC-001` | concurrency | warning | A synchronous requests loop for heavy I/O | asyncio + httpx with a semaphore |
| `CONC-002` | concurrency | warning | Python threads to speed up CPU-heavy work | multiprocessing / ProcessPoolExecutor |
| `RT-001` | realtime | critical | HTTP polling for chat and live updates | WebSockets / SSE |
| `RT-002` | realtime | critical | Collaborative editing with last-write-wins | CRDTs: Yjs or Automerge |
| `AI-001` | ai_ml | warning | Shipping full PyTorch models inside desktop/mobile/offline apps | ONNX Runtime |
| `AI-002` | ai_ml | critical | Training a model from scratch for a solved problem | Pretrained model or API first |
| `AI-003` | ai_ml | warning | Stuffing entire document collections into an LLM prompt | RAG: chunk, embed, retrieve, prompt |
| `SEARCH-001` | search | info | Distributed vector databases for a small corpus | sqlite-vec, Chroma, pgvector |
| `SEARCH-002` | search | warning | Full-text search with SQL `LIKE '%term%'` | SQLite FTS5 / Postgres full-text search |
| `SCRAPE-001` | scraping | warning | Scraping JS-rendered sites with requests + BeautifulSoup | Official API/JSON endpoints first, Playwright if needed |
| `GEO-001` | geolocation | warning | Live location tracking by polling GPS over HTTP | Distance-throttled background location + WebSockets |
| `GEO-002` | geolocation | warning | Nearby search in app code or with flat lat/lng math | PostGIS `ST_DWithin` + GiST index |
| `PAY-001` | payments | critical | Handling card data or marketplace payouts yourself | Stripe Checkout + Stripe Connect |
| `PUSH-001` | notifications | warning | Polling from the app to deliver notifications | Expo Notifications (APNs/FCM), Web Push |

The full text (`why_it_fails`, all `recommended` options) is in `project_md/core/knowledge_base.py`.

---

## 4. Option 1: the proposed architecture

### 4.1 Core idea
**Stop trying to understand the idea ourselves. Let the AI assistant the user already has open do the understanding, and make PROJECT.MD the curated expertise and the protocol it must follow.**

The user's assistant (Claude Code, Cursor, Antigravity, Copilot, Bob/OpenCode) is a strong language model that is going to read our context files anyway. Regex can't generalise to arbitrary ideas; the assistant can. What the assistant lacks is:
- a curated, evidence-backed catalogue of dead ends;
- an **obligation** to check it *before* writing code;
- a fixed output format that records the decision.

We supply those three things, packaged in each assistant's native mechanism.

### 4.2 Components

| Component | What it is | Notes |
| :--- | :--- | :--- |
| **Trap catalogue** | The 29+ traps, rendered as assistant-readable knowledge: id, domain, the dead end, *why it fails*, replacements, "signals" (plain-language descriptions of when it applies, not regexes) | Stays the single source of truth in `knowledge_base.py`; exporters render it |
| **Pre-flight protocol** | Step-by-step instructions the assistant must run before building: restate the idea → identify domains → check every trap *semantically* → verdict PASS/REVIEW/BLOCK with evidence → write `PROJECT.md` → proceed | Replaces the regex intent/scan layer |
| **Continuous guard** | A standing rule: whenever the user or assistant is about to add a dependency or approach, check it against the catalogue | Catches traps introduced mid-project, not just at kickoff |
| **Native packaging** | Protocol and catalogue rendered as each assistant's always-on rules plus an on-demand command/workflow | E.g. Claude Code slash command or skill, Cursor rules, Antigravity rules/workflows, AGENTS.md |
| **CLI (smaller role)** | `project-md init` installs the pack into a repo. Optionally `project-md "idea"` seeds the idea and a quick keyword pre-scan as *hints* | The CLI stays stdlib-only; no API key needed |
| **Evaluation harness** | A corpus of real ideas and a rubric, used to measure whether assistant + pack beats assistant alone | Replaces "unit tests prove detection", which they can't |

### 4.3 How a user would experience it (hypothesis to validate)
1. `python3 -m project_md.cli init` (or `project-md init`) in an empty folder writes the pack.
2. The user opens their assistant and types their idea in one sentence, as they would anyway.
3. The assistant, obeying the always-on rule, runs the pre-flight first. It replies with a short verdict ("⚠️ OpenCV can't read handwriting because…; using TrOCR instead"), writes `PROJECT.md`, and only then starts coding.
4. Later, "let's store the card number in the DB" makes the assistant cite `PAY-001` and refuse or redirect.

### 4.4 Why it might be right
- **It generalises to any phrasing and any idea.** The 15-idea probe failures are exactly what an LLM handles well.
- **It keeps rule 1** (no dependencies, no API key) and **rule 2** (the user still types one sentence).
- **The durable value moves to what's hard to copy:** the curated, sourced catalogue, the protocol, multi-assistant packaging and published evaluation results.

### 4.5 Known risks and open tensions (the research must address these)
- **R1: Assistants may already push back.** If current models already refuse OpenCV-for-handwriting unprompted, the value is lower. It would then shift to consistency, coverage of subtler traps, and the continuous guard.
- **R2: Rule files may be ignored.** Long always-on files get skimmed; instructions may lose to the user's explicit request ("just use OpenCV"). Compliance may differ by assistant and model.
- **R3: Context budget.** 29 traps with full explanations are several thousand tokens. Progressive disclosure (index always loaded, detail on demand) may be required.
- **R4: Non-determinism.** Verdicts vary between runs and models, so we need an evaluation harness instead of exact-output unit tests.
- **R5: The PASS/REVIEW/BLOCK contract** and the CLI exit codes (used for CI) don't carry over directly to a chat flow. Decide what remains deterministic.
- **R6: Differentiation.** "It's just a prompt": how is this better than community rule packs or spec-driven tools?
- **R7: Catalogue staleness.** Replacements such as TrOCR or specific Stripe products change; the catalogue needs dated sources and review.

### 4.6 The chosen design: a five-agent pack on top of the user's assistant

**The idea in the owner's words:** download a pack once. Whenever you start something (the owner imagines `git init`, then describing an idea), **five specialist agents** use *your* AI coding assistant, and the model powering it, to do all the work: research the idea, find the best stack, and work out contracts, dependencies, security, reliability, robustness and scalability. The idea ends up fully specified, written as `PROJECT.md` plus the assistant's native context file (`CLAUDE.md`, Cursor rules, `AGENTS.md`...). The agents sit on top of Copilot, Claude Code, Cursor or Antigravity; PROJECT.MD ships no model of its own.

**Proposed split (to be validated, not fixed):**

| Agent | Job | Contributes to `PROJECT.md` |
| :--- | :--- | :--- |
| 1. **Researcher** | Understand the idea; find prior art and proven approaches; check every catalogue trap *by meaning* | Problem statement, prior art, dead ends (why + replacement) |
| 2. **Stack & Dependencies** | Choose the stack; vet libraries (maintenance, licence, deprecation) | Stack table, dependency list with licences |
| 3. **Architecture & Contracts** | Layers and boundaries; data models and API | Layers, forbidden imports, models, endpoints |
| 4. **Reliability & Scale** | Failure modes, bottlenecks, behaviour at 10× load | Risks, retries/queues, scaling plan |
| 5. **Security & Privacy** | Auth, secrets, regulated data, abuse | Threats, mitigations, compliance flags |

- **An orchestrator command** (working name `/preflight <idea>`) fans out to the five agents, merges their results into one verdict (PASS / REVIEW / BLOCK) and writes the files. The user still types one sentence (rule 2).
- **The trap catalogue (§3.2)** is the shared reference every agent must check against. **Rule 3** (why + replacement) applies to everything the agents emit.
- **Claude Code first**, because it has native subagents (`.claude/agents/*.md`) and slash commands (`.claude/commands/*.md`, user-level under `~/.claude/`). *These locations are the owner's working assumption. Verify them in RQ2/RQ10.*
- **Install both ways:**
  - **globally once**, so the command works in every project;
  - **per project** via `project-md init`, e.g. for teams.
- **What happens to today's code:**
  - the catalogue, exporters, tests and CLI stay (the CLI becomes the installer, still stdlib only);
  - the regex detection and rule-based agents are retired, or kept as an offline fallback.

**Specific uncertainties for this design:**
- **U1: `git init` as the trigger.** The owner's working understanding: git's init template directory only populates `.git/`, not the working tree, and there is no post-init hook. So `git init` probably *cannot* install or trigger the pack. Verify this (RQ11).
- **U2: Parallel subagents outside Claude Code.** Whether Copilot, Cursor and Antigravity support subagents or parallel agents, or whether the five must run in sequence in one conversation (RQ10).
- **U3: The "research your idea" step needs web access.** Which assistants give their agents web search or fetch, and what happens without it (RQ10)?
- **U4: Five specialists may not beat one well-prompted pre-flight** and will cost more time and tokens (RQ12).

---

## 5. Research questions

Answer each one. For each, give a **finding**, **evidence** (with links and dates), a **confidence** level (high/medium/low), and **implications for PROJECT.MD**.

### RQ1: Baseline: do assistants already push back on dead ends? *(highest priority)*
Hypothesis to test: *"Current AI coding assistants implement naive dead-end requests without warning."*
- **Build a trap-prompt set of at least 20 prompts** covering at least 10 catalogue traps. Mix:
  - (a) naive idea only ("An app to read doctor handwriting");
  - (b) explicit dead end ("Use OpenCV contours to read doctor handwriting");
  - (c) indirect ("A fitness app that counts push-ups from the camera", "split bills with roommates").
- **Run each prompt in a fresh session** of every assistant you can access (Antigravity at minimum; Claude Code, Cursor or Copilot if available). Record the model and version.
- **Score each response:** (0) implements the dead end silently; (1) implements it with a caveat; (2) pushes back and proposes the right replacement before coding.
- **Output:** a table of prompt × assistant → score, plus the raw responses in `docs/research/experiments/`.

### RQ2: Native mechanisms per assistant
For **Claude Code, Cursor, Google Antigravity, GitHub Copilot (VS Code) and AGENTS.md-compatible tools** (OpenCode, IBM Bob, Codex and others), document from primary docs:
- **Always-on project instructions:** file names, locations, precedence, size limits, whether nested files load.
- **On-demand mechanisms:** slash commands, skills, workflows, prompt files, custom modes/agents, and how to invoke them.
- **Rule frontmatter and scoping:** e.g. Cursor `.cursor/rules/*.mdc` with `alwaysApply`/`globs`/`description`; whether `.cursorrules` is deprecated; Antigravity `.agent/rules` vs workflows; Claude Code `CLAUDE.md`, `.claude/commands`, `.claude/skills`, `.claude/agents`, hooks.
- **Whether hooks exist** that could *enforce* a check (e.g. before a dependency is installed), not just suggest one.
- ⚠️ **Our current exporters make assumptions here** (e.g. `.cursorrules`, plain-markdown `.agent/rules/*.md`). Flag every one that is outdated or wrong.

### RQ3: Does a rule pack actually change behaviour?
- **Repeat the RQ1 prompts with a prototype pack installed.** Build it by hand in `docs/research/experiments/pack/`: catalogue plus protocol, rendered natively for each assistant tested.
- **Measure the improvement over the baseline.**
- **Test the adversarial cases:**
  - Does the assistant still comply when the user insists ("I know, use OpenCV anyway")?
  - Does it over-trigger on ideas that *aren't* traps (false positives, e.g. "prescription refill reminders")?
- **Compare catalogue formats:** one big file vs index + per-domain files vs per-trap files. Which gives the best compliance and token cost?

### RQ4: Protocol design
- What is the best trigger: always on, only on a new project or empty repo, on new dependencies, or on an explicit `/preflight`?
- What output format keeps the user's one-sentence experience (rule 2) while still producing a durable `PROJECT.md`?
- How should the verdict be expressed so it's consistent across assistants? Should PASS/REVIEW/BLOCK survive?
- How should the assistant handle "the user explicitly wants the dead end"?

### RQ5: What should stay deterministic (the CLI's future role)?
- **Candidates:**
  - installing/updating the pack (`init`, `update`);
  - catalogue rendering;
  - a keyword pre-scan as a hint or floor;
  - CI mode that validates `PROJECT.md` or dependency files against the catalogue (e.g. flag `opencv-python` in `requirements.txt` for a handwriting project);
  - schema validation of the assistant-written `PROJECT.md`.
- Which of these have real value? Would a **dependency-file scanner** (package names are much more reliable than free text) be the right deterministic core?

### RQ6: Evaluation methodology
- **Where to get a corpus of 100+ real beginner/hackathon ideas**, with licences and terms checked. Candidates: Devpost project galleries, r/learnprogramming "what stack" posts, hackathon prompt lists, student capstone lists.
- **A labelling rubric** (which traps apply to which idea) and inter-rater approach.
- **Metrics:** per-trap recall and precision, false-positive rate, and whether the replacement is correct.
- **How to automate runs across assistants,** or what must stay manual.

### RQ7: Catalogue validity and expansion
- **Fact-check all 29 traps' claims and replacements as of today.** Examples:
  - Is TrOCR still a good default for handwriting, or have vision-language models superseded it?
  - Is Ultralytics YOLO still AGPL-3.0?
  - Are whisper.cpp, LiteRT and Auth.js still current?
  - Are the Stripe Connect Express details right?
- **Propose 20–40 new traps** from evidence of real beginner failures, prioritised by frequency × cost. Use the §3.1 gaps as seeds: pose estimation, bank aggregation, extension API keys, LLM math, time-series/IoT, Manifest V3, Discord gateway intents...

### RQ8: Competitive landscape and differentiation
- **Survey:** community rule collections (e.g. cursor.directory / awesome-cursorrules), assistant skill/command marketplaces, spec-driven development tools and methods (e.g. GitHub Spec Kit, Kiro specs, BMAD, Task Master), and any "architecture pre-flight" or stack-advisor tools.
- **For each:** what it does, overlap with Option 1, and what PROJECT.MD would do that it doesn't.
- **Conclude:** is there a defensible gap?

### RQ9: Hybrid with Option 2 (optional AI mode)
Option 2 would make the CLI call an LLM API directly (possible with Python's stdlib `urllib`, so no dependency, but an API key is required). Should Option 1 be the default and Option 2 a later add-on for CI/headless use? What would each cost the user?

### RQ10: Five-agent pack feasibility per assistant
For each of **Claude Code, Cursor, GitHub Copilot (VS Code) and Google Antigravity**, from primary docs and hands-on tests:
- **Subagents / custom agents:** can a project or user define named specialist agents? File format and location? Can one command or agent invoke others? **In parallel?** Does each get its own context window?
- **Orchestration:** how would `/preflight <idea>` be implemented natively (slash command, prompt file, workflow, custom mode)? Can it pass the idea to each agent and collect structured results?
- **Tools available to the agents:** web search/fetch (needed by the Researcher), file write (needed to write `PROJECT.md`), and whether tools can be restricted per agent (e.g. the pre-flight agents read-only except the final writer).
- **Fallback:** where subagents aren't supported, write the single-conversation sequential version and compare its quality.
- **Output:** a matrix assistant × {subagents, parallel, per-agent tools, web access, orchestration mechanism, fallback needed?}, each cell with a source.

### RQ11: Install and trigger
- **Verify U1:** can `git init` (init templates, `init.templateDir`, hooks) put files into the working tree or trigger anything? Cite git's documentation.
- **For each assistant:** where are **user-level (global)** vs **project-level** agents, commands and rules stored on macOS, Windows and Linux? Do global and project definitions merge, and which wins on a name clash?
- **Evaluate beginner-friendly triggers:**
  - global install plus `/preflight`;
  - `project-md init`;
  - a git alias;
  - shell functions;
  - an assistant plugin or marketplace entry, if any exist.
  Rank them by steps a beginner must take and cross-platform reliability.
- **What does updating the pack look like** when the catalogue changes?

### RQ12: Do five specialists beat one?
In Claude Code, run the RQ1 prompt set in **three arms**:
- (a) **no pack** (baseline);
- (b) **single-agent pack:** one pre-flight command with the full protocol and catalogue;
- (c) **five-agent pack:** the §4.6 orchestrator plus five subagents.

For each arm, record trap recall, false positives, correctness of the replacement, completeness of `PROJECT.md` (stack, contracts, security, reliability sections), **wall-clock time and token cost**. Recommend (b), (c), or a different split (e.g. three agents), with evidence.

---

## 6. Suggested method (adapt as needed)

1. **Read** `docs/PRD.md`, `CLAUDE.md`, `README.md` and `project_md/core/knowledge_base.py` (about 30 minutes).
2. **RQ2, RQ10 and RQ11 first** (docs research): you need the native formats, subagent support and install locations before you can build the prototypes.
3. **RQ1 baseline experiments.**
4. **Build minimal prototype packs by hand** in `docs/research/experiments/pack/`:
   - an index of all traps with one-line signals;
   - full detail for about 10 traps;
   - the protocol text;
   - for Claude Code, both a **single-agent** version and a **five-agent** version (orchestrator command plus five subagent definitions).
5. **RQ3 and RQ12 experiments** with the packs.
6. **RQ7 and RQ8 desk research.**
7. **Draft the RQ4, RQ5, RQ6 and RQ9 recommendations** from what you learned.
8. **Write the findings document.**

Where you can't run an assistant, write the exact prompts and procedure so the owner can run them, and mark the result **PENDING**.

---

## 7. Constraints any recommendation must respect

- **Rule 1 (stdlib only, no `pip install`) holds for anything PROJECT.MD ships.** If you recommend breaking it, say so explicitly and justify it.
- **Rule 2 (one sentence from the user) holds.** A single confirmation from the assistant is acceptable; a questionnaire is not.
- **Rule 3 (plain-English *why* + mandated replacement) holds** for every trap, in every format.
- **Verdict semantics (§0, C5) hold:** BLOCK only for an explicitly chosen dead end, REVIEW only for a human decision, and latent traps are guarded warnings under PASS.
- **Beginners are the audience.** Anything that needs understanding git hooks, API keys or config files is a cost to call out.
- **Cross-platform:** macOS, Windows, Linux.

---

## 8. Out of scope

- Implementing the pivot in `project_md/`.
- Distribution (Homebrew, winget, PyPI, npm). The PRD's Phase 2 comes later.
- Rewriting the PRD. You may propose PRD changes in your findings.

---

## 9. Deliverable format

Create `docs/research/FINDINGS-assistant-native-preflight.md` with:

1. **TL;DR (≤ 10 lines):** go / no-go / go-with-changes on the **five-agent pack (§4.6)**, the recommended number of agents, and the single most important finding.
2. **Answers to RQ1–RQ12:** finding, evidence (links + access dates), confidence, implications.
3. **Results table for baseline vs single-agent vs five-agent** (RQ1/RQ3/RQ12), with raw transcripts linked from `docs/research/experiments/`.
4. **Native mechanism matrix** (RQ2): assistant × {always-on file, on-demand command, frontmatter/scoping, size limits, hooks}, each cell with a source link. Explicitly list which of our current exporter outputs are wrong or outdated.
5. **Recommended architecture:**
   - components and file layout per assistant (starting with Claude Code);
   - the install/trigger flow (RQ11);
   - draft agent definitions and orchestrator text, with the prototype files linked;
   - what stays deterministic;
   - a migration path from the current code (what to keep, change or delete).
6. **Catalogue review** (RQ7): a per-trap verdict (keep / update / drop, with source), plus the proposed new traps with evidence.
7. **Evaluation plan** (RQ6): corpus sources, rubric, metrics, and how it runs.
8. **Competitive landscape** (RQ8): a table and the differentiation statement.
9. **Risks, open questions and suggested next steps**, ordered.
10. **Source list:** every URL with its access date.

Keep claims calibrated. A short report with verified findings is worth more than a long one with guesses.
