# Architectural Pre-Flight & Contract Enforcement Engine

> **"Don't let the agent code first and discover the architecture later. Pre-flight the change first."**

An autonomous architecture and contract enforcement engine designed for [IBM Bob 2.0](https://bob.ibm.com/docs/ide). Architectural Pre-Flight intercepts developer requests and validates intent against repository architecture, contracts, dependencies, and blast radius *before* an AI coding agent generates code.

---

## 💡 The Problem

AI coding agents dramatically accelerate implementation speed, but they also accelerate the creation of architectural debt. When prompted, coding agents frequently:

- Duplicate existing internal services or abstractions
- Bypass defined layer boundaries (e.g., frontend querying database directly)
- Introduce deprecated or prohibited dependencies
- Break downstream API, type, or event contracts without realizing it
- Trigger expensive "dead-end" refactors that are discovered only at build or review time

---

## 🚀 The Solution

Architectural Pre-Flight acts as a **pre-implementation gate**. When a developer describes an intended change, the engine analyzes the repository and triggers **parallel IBM Bob subagents** across five dimensions:

| Subagent | Responsibility |
|---|---|
| **Architecture Explorer** | Evaluates layer boundaries, pattern consistency, and detects duplicate abstractions |
| **Contract Explorer** | Discovers API endpoints, types, and event schemas to check compatibility against downstream consumers |
| **Dependency Guardian** | Validates proposed libraries against lockfiles, deprecation registries, and repository policy |
| **Impact Explorer** | Maps the full blast radius across files, call sites, services, and tests |
| **Security Explorer** | Audits authentication boundaries, data egress, and credential exposure |

A **Deterministic Policy Engine** evaluates the findings and outputs an actionable verdict:

- 🟢 **CLEARED** — Change satisfies all architectural constraints; passed to IBM Bob for implementation
- 🟡 **REVIEW REQUIRED** — High impact or meaningful uncertainty detected; requires human approval
- 🔴 **BLOCKED** — Violates explicit architecture, dependency, or contract invariants

If blocked, the engine provides an evidence-backed remediation plan to guide the coding agent down a compliant path.

---

## 🏗️ System Architecture

```
Developer Intent
      ↓
Change Intent Analyzer
      ↓
Repository Knowledge Graph
      ↓
Parallel Specialist Subagents (IBM Bob 2.0)
      ├── Architecture Explorer
      ├── Contract Explorer
      ├── Dependency Guardian
      ├── Impact Explorer
      └── Security Explorer
      ↓
Deterministic Policy Engine
      ↓
Decision: [ PASS / REVIEW / BLOCK ]
      ↓
Evidence-Backed Remediation Plan
      ↓
Human Approval
      ↓
IBM Bob Agent (Implementation)
      ↓
Post-Flight Verification
```

---

## 📁 Repository Structure

```
architectural-preflight/
├── .bob/                         # IBM Bob custom modes and subagents
│   ├── modes/preflight.yaml      # Custom read-only preflight mode
│   └── subagents/                # Isolated specialist agent prompts
├── backend/                      # Core FastAPI & Python analysis engine
│   ├── app/
│   │   ├── agents/               # Orchestration & subagent coordinators
│   │   ├── decision/             # Deterministic policy engine & risk scoring
│   │   ├── graph/                # Repository knowledge graph (NetworkX)
│   │   └── remediation/          # Step-by-step remediation generator
│   └── cli/                      # Terminal CLI tool
├── frontend/                     # React + Vite + Tailwind + React Flow UI
├── policies/                     # Architecture-as-Code definitions
│   ├── architecture.yaml         # Layer boundaries and forbidden rules
│   ├── contracts.yaml            # Strict schema specifications
│   └── dependencies.yaml         # Blocked/deprecated package rules
├── benchmark_repo/               # Trap repo for controlled test scenarios
└── .github/workflows/            # CI/CD pre-flight gate actions
```

---

## 🛠️ Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- IBM Bob 2.0 IDE

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

### 3. CLI Usage

Run pre-flight checks directly against your repository from the command line:

```bash
# Analyze a proposed change
python -m backend.cli.main analyze --change "Add Google OAuth authentication"

# Run in CI mode (deterministic pass/fail)
python -m backend.cli.main ci --policy-dir policies/ --strict
```

---

## 📜 Architecture-as-Code Policy Example

Define your system boundaries inside `policies/architecture.yaml`:

```yaml
version: "1.0"

layers:
  frontend:
    allowed_dependencies:
      - api
      - ui
  api:
    allowed_dependencies:
      - services
  services:
    allowed_dependencies:
      - repositories
  repositories:
    allowed_dependencies:
      - database

rules:
  - id: ARCH-001
    description: "Frontend must not access database directly"
    from: frontend
    to: database
    action: block

dependencies:
  forbidden:
    - deprecated-package-name
  approval_required:
    - new-database-client
```

---

## 📊 Target Impact & Metrics

| Metric | Target |
|---|---|
| Reduction in dead-end refactoring time | ≥ 90% in benchmark scenarios |
| Deprecated or policy-blocked dependencies accepted | 0 |
| Pre-build contract validation coverage | 100% on supported change proposals |

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).
