# CLAUDE.md — PROJECT.MD Development Guidelines

## Canonical Specification
- Full Product Requirements & Architecture Blueprint: `docs/PRD.md`

## Project Vision & Mission
PROJECT.MD is a zero-prerequisite cross-platform architecture tool for complete beginners, busy vibe coders, and hackathon teams.
- **The Core Problem:** Beginners waste hours picking wrong stacks or letting AI assistants write thousands of lines of doomed code (e.g. using OpenCV for handwriting OCR, which fails completely in testing). Expecting beginners to know their tech stack or architecture is broken.
- **The Solution:** The user inputs ONLY their idea in plain English (1 input). The engine automatically infers the optimal modern stack, intercepts fatal anti-patterns (OpenCV for handwriting, polling for real-time, etc.), and generates native AI context files (`PROJECT.md`, `CLAUDE.md`, `.cursorrules`, `GEMINI.md`, `AGENTS.md`).

## Non-Negotiable Technical Rules
1. **Zero External Dependencies:** Built with 100% Python standard library (dataclasses, argparse, re, json, typing). Must run instantly out-of-the-box on Mac, Windows, and Linux without needing `pip install` first.
2. **1-Shot User Experience:** Never interrogate the beginner with questions about databases, frontend frameworks, or architecture layers. The engine must automatically infer the optimal stack from their plain-English prompt.
3. **Evidence & Truth:** Trap warnings must explain WHY an anti-pattern fails in plain English and mandate the modern replacement.

## Build & Test Commands
- Run CLI: `python3 -m project_md.cli`
- Run 1-shot: `python3 -m project_md.cli "An app to transcribe doctor handwriting"`
- Run tests: `python3 -m unittest discover -s tests -v`