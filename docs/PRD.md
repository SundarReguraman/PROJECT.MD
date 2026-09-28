# PROJECT.MD: Universal Pre-Flight Architecture & Native Context Engine

> **Tagline:** Build the right thing before you build it wrong. Stop AI coding assistants from hallucinating dead-end architectures.

---

## 1. The Origin Story: The "OpenCV Handwriting Trap"

```
[Developer Idea] ➔ "Read human handwriting"
       │
[Naive Assumption / AI Hallucination] ➔ "Let's use OpenCV image processing & contours!"
       │
       ▼ (2 weeks of coding & 3,000 lines of code)
[Testing Phase] ➔ Catastrophic Failure.
       │         OpenCV is for computer vision & image filters, NOT handwritten text recognition.
       ▼         The real solution required TrOCR, Vision-Language Models, or CRNN.
[Result] ➔ Complete rewrite. Total sunk cost. Massive frustration.
```

### Why AI Assistants Make This Worse Today
AI coding assistants (Claude Code, Cursor, Copilot, Bob, Antigravity) are eager implementers. When a beginner prompts: *"Help me write a Python script using OpenCV to transcribe messy doctor handwriting,"* the assistant will happily write thousands of lines of contours, thresholding, and morphological hacks. **It does not push back.** It leads the developer straight off an architectural cliff.

**PROJECT.MD** fixes this:
It sits between the human's idea and the AI assistant. It intercepts assumptions, validates technology fitness, flags dead-end libraries, designs the system structure, and outputs a single, battle-tested, native context file (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.cursorrules`, `PROJECT.md`).

---

## 2. Core Value Proposition

| Traditional Way | With PROJECT.MD |
| :--- | :--- |
| Jump straight into coding; discover fundamental library mismatches in testing. | **Pre-flight tech audit**: Intercepts library/architecture dead ends before line 1. |
| Scattered, bloated PRDs that AI agents ignore or hallucinate across. | **Single Source of Truth**: One compact, structured, high-density context file. |
| Locked to one assistant; incompatible rules files for Cursor vs Claude vs Bob. | **Universal Native Adapter**: Generates native formats for every major AI coding platform. |
| Beginners overwhelmed by system design, interfaces, and contracts. | **Interactive elicitation**: Guides the user through constraints, trade-offs, and choices. |

---

## 3. Product Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        USER INPUT (CLI / TUI)                          │
│  • Project Idea                                                        │
│  • Constraints (budget, latency, offline/cloud, hardware, language)    │
│  • Core Features & User Stories                                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              PRE-FLIGHT VIABILITY & TECH AUDIT ENGINE                  │
│                                                                        │
│  • Dead-End Detector (e.g. OpenCV for handwriting → Flag! Use TrOCR)   │
│  • Tech Stack Advisor (SQLite vs Postgres, Fastify vs Express)         │
│  • Complexity & Constraint Harmonizer (offline vs cloud API conflicts) │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               SYSTEM DECOMPOSITION & CONTRACT GENERATOR                │
│                                                                        │
│  • Clean Architecture Layers (Domain, Service, Data, Interface)        │
│  • Data Contracts & Schemas (Pydantic / Zod / Type definitions)        │
│  • Testing & Acceptance Boundaries (Zero-hallucination definitions)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   UNIVERSAL NATIVE CONTEXT ADAPTER                     │
│                                                                        │
│   ├── CLAUDE.md                   (Anthropic Claude Code)              │
│   ├── GEMINI.md & .agent/rules/   (Google Antigravity)                 │
│   ├── AGENTS.md                   (IBM Bob / OpenCode)                 │
│   ├── .cursorrules / .cursor/     (Cursor IDE)                         │
│   ├── copilot-instructions.md     (GitHub Copilot / VS Code)           │
│   └── PROJECT.md                  (Universal Markdown Fallback)        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Subsystems

### 4.1 The Pre-Flight Tech Audit ("The Anti-OpenCV Engine")
A curated heuristic + AI reasoning matrix mapping project requirements to optimal libraries and flagging lethal mismatches:

| Domain | Trap / Anti-Pattern | Recommended Solution |
| :--- | :--- | :--- |
| **Handwritten OCR** | OpenCV contours, basic Tesseract | TrOCR (HuggingFace), Donut, Google Cloud Vision / Textract |
| **Real-time Sync** | HTTP Polling at scale | WebSockets, SSE, or CRDTs (Yjs) |
| **Edge AI / Local** | Heavy PyTorch models in Electron | ONNX Runtime, whisper.cpp, llama.cpp |
| **Heavy I/O Concurrency** | Python synchronous `requests` loop | `asyncio` + `httpx`, or Go/Node runtime |
| **Vector Search (Small)** | Complex distributed Milvus/Pinecone | In-process SQLite-vec, Chroma, or pgvector |

### 4.2 The Universal Native Context Adapter
Every AI assistant expects context in its own native convention:

1. **`CLAUDE.md`** (Claude Code):
   - Command cheat sheets (`make test`, `pnpm run lint`).
   - Strict architectural boundaries.
   - Code style and error handling idioms.
2. **`GEMINI.md` & `.agent/rules/*.md`** (Google Antigravity):
   - Progressive disclosure context.
   - Hierarchical workspace rules.
   - Subagent protocol definitions.
3. **`AGENTS.md`** (IBM Bob / OpenCode):
   - `/init` indexing targets.
   - Plan vs Code vs Ask mode operating constraints.
   - Task session summary hooks.
4. **`.cursorrules`** (Cursor):
   - Directives, linting rules, framework-specific typing constraints.
5. **`.github/copilot-instructions.md`** (VS Code & Copilot):
   - System prompt extensions, workspace symbol conventions.
6. **`PROJECT.md`** (Universal Master):
   - Human-readable + machine-parseable standalone specification.

---

## 5. User Workflow: How a Developer Uses It

```bash
# 1. Install via Homebrew, Winget, or curl single-binary
brew install project-md
# or: winget install project-md
# or: curl -fsSL https://get.projectmd.dev | sh

# 2. Run inside any new project directory
project-md init
```

### The Interactive Experience:
```text
╭─────────────────────────────────────────────────────────────╮
│                   PROJECT.MD Architecture Pre-Flight         │
╰─────────────────────────────────────────────────────────────╯

? What do you want to build?
> A mobile and desktop app that transcribes handwritten doctor notes.

? What is your preferred stack or language?
> Python backend, cross-platform app.

? What are your constraints?
  [X] Must run offline without cloud costs
  [ ] Budget < $100/mo
  [X] Latency < 2 seconds per page

⚡ PRE-FLIGHT AUDIT RUNNING...
⚠️  CRITICAL WARNING DETECTED:
    You mentioned Python and image processing. If you are planning to use OpenCV 
    or standard Tesseract for handwriting, DO NOT PROCEED.
    OpenCV lacks sequence recognition for cursive text.
    Recommended: TrOCR-small via ONNX Runtime (Offline, CPU-friendly, < 2s).

? Select target AI Assistants to generate context for:
  [*] Claude Code (CLAUDE.md)
  [*] Google Antigravity (GEMINI.md)
  [*] Cursor (.cursorrules)
  [*] IBM Bob / OpenCode (AGENTS.md)
  [*] Universal (PROJECT.md)

✔ Generated PROJECT.md (Universal Architecture Specification)
✔ Generated CLAUDE.md
✔ Generated GEMINI.md
✔ Generated AGENTS.md
✔ Generated .cursorrules

You are ready! Open your AI assistant of choice and start building without hallucination.
```

---

## 6. Implementation & Packaging Plan

### Technology Choice: **Rust** or **Go** (Single Binary)
- **Why?** Instant launch, zero runtime dependencies (no requiring Python or Node.js to be installed on the user's machine), native binaries for:
  - macOS (Apple Silicon + Intel)
  - Windows (`.exe` with GUI/TUI support)
  - Linux (x86_64 and ARM64)
- **Alternative for rapid MVP**: Python CLI bundled as a standalone binary via PyInstaller / Nuitka, featuring `rich` and `textual` for the terminal interface.

---

## 7. Phased Roadmap

### Phase 1: Core Engine & Prompt Synthesizer (MVP)
- Interactive CLI that interviews the developer on Intent, Constraints, Stack, and Features.
- Knowledge rules database: Top 25 tech traps (Computer Vision, OCR, Auth, Databases, Queues, Concurrency).
- Exporters: `PROJECT.md`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, `.cursorrules`.

### Phase 2: Native Cross-Platform Distribution
- Single-binary builds via GitHub Actions for Mac, Windows, Linux.
- Distribution channels: `brew`, `winget`, `npm install -g project-md`, `curl | sh`.

### Phase 3: Live Verification & Repo Scan Mode (`project-md check`)
- Run in an existing repository to evaluate if the current code violates the original `PROJECT.md` contracts.
