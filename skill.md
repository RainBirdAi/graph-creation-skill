---
name: graph-creation-skill
description: Create and modify Rainbird knowledge graphs and models
---

## Overview

This is not a software project — it is a knowledge-engineering workspace for building **Rainbird knowledge graphs** in RBLang (an XML format). Tasks include creating new graphs from scratch, extending or fixing existing ones, and validating/testing them against the live Rainbird API. Graphs built here may become **production knowledge systems** — treat every build as production-quality: encode ALL the expertise you are given, at full depth, with complete traceability from requirement to rule.

**Read `project_instructions.md` first on every task** — it is the authoritative task brief and requires entering plan mode before executing.

Your steps will be:
1. Read the project instructions, `rblang_guide.md`, `patterns.md`, and `MEMORY.md`.
2. Ask the user for their Rainbird API key. If they say they don't have one, point them to sign up at https://app.rainbird.ai/signup
3. Plan the work (plan mode), then perform the task, carefully following the project instructions.
4. Validate by uploading the graph via the API, then test it live (see loop below).
5. Fix any issues and re-validate until clean.
6. Give the user the outputs (XML, tests, documentation).

## Before you start

Before you start work you *must* ask the user for their Rainbird API key so that you can complete the validation loop at the end of the process.

## Key files and directories

- `rblang_guide.md` — the RBLang format reference (concepts, relationships, instances, rules, expressions) including confirmed platform semantics. Read before writing any XML.
- `patterns.md` — the design-pattern catalogue: proven architectures for decision models (layered pipelines, precedence ladders, certainty design, normalization tables, text analysis, evidence layers). Pick your architecture from here before authoring.
- `example_graphs/` — reference graphs showing established patterns; `example_graphs/INDEX.md` says what each one demonstrates. Follow them closely.
- `MEMORY.md` — accumulated, hard-won findings from previous tasks: platform quirks, validation gotchas, confirmed API behaviours. **Read it before writing RBLang and update it with any new findings** (function-call argument limits, expression evaluation order, dedup semantics, question-harvesting behaviour, comment character restrictions, etc. live there — do not rediscover them).
- `tests_examples.json` — the exact Studio test-suite JSON shape. Follow it precisely; Studio import is strict (see MEMORY.md "Studio test-suite JSON").

## Build / validate / test loop

There is no compiler or test suite. The equivalent loop is:

1. Write RBLang XML (following `rblang_guide.md`, `patterns.md`, and the examples).
2. **Deterministic lint**: run `python3 tools/lint_rblang.py <graph.xml>` — it mechanically checks declarations, concinsts for literal fact objects, quoted rel names in list functions, explicit `askable` on every rel, `alt` text on expression conditions (balanced `{{...}}`, no `"` or `<`, ≤220 chars), function calls with expression arguments, left-to-right expression-order hazards, comment character restrictions, unbound variables, self-counting rules, and more. Fix every ERROR and review every WARN. Do not eyeball instead.
3. Upload via the **undocumented map-upload API** and fix validation errors until clean:
   - `POST https://api.rainbird.ai/maps`
   - Headers: `X-API-Key: <key>` **and `Version: v1`** (omitting `Version` yields 400 "unsupported API version").
   - JSON payload: `{"rblang": "<xml>", "name": "<name — index 1/2/3…n as you iterate>", "description": "<short plain text — long/punctuated descriptions are rejected with DESCRIPTION_ERROR>"}`
   - Success is 201 with a `kmID`; the map is live immediately.
4. Test behaviour live with the returned kmID: `GET https://api.rainbird.ai/start/{kmID}` to open a session, then inject facts and run queries (exact payload shapes are in MEMORY.md "API playbook"). See https://docs.rainbird.ai/rainbird/developer-docs/api-guide.
5. Run the **three-grade test set** (see `project_instructions.md`): straight-through (zero questions), few-questions (scripted Q&A), and fringe/boundary flips (verified on both sides).
6. Audit the **evidence/reason layer** of live runs, not just outcomes — on multiple past builds the only post-live bugs were reason/evidence lines firing on outcomes they don't narrate.
7. Generate Studio tests **from the live runs** so expected certainty values are engine-exact.

You *must* complete this loop every time before you give the user any assets you've created.

External references: RBLang reference at https://docs.rainbird.ai/rainbird/knowledge-modelling/modelling-features/rblang-reference and the API guide above — read the API guide as part of any build so data/query design suits consumers of the graph.

## Working rules

- Never delete a rule that traces to a requirement; fix non-firing rules in place. If consolidating redundant rules, preserve coverage and document the old→new mapping (see MEMORY.md lessons).
- Follow existing graph patterns and vocabulary from `example_graphs/` and any graphs you are editing.
- Design askability deliberately: systems-of-record data is `askable="none"` and injected; only facts a human could genuinely answer are askable. Every rel gets an explicit `askable` attribute (missing = defaults to askable at runtime).
- Do not ship programmatically built `.rbird` files — they corrupt the Studio UI (see MEMORY.md). Deliver XML + Studio tests JSON + markdown documentation instead.
- If subagents must analyse a large graph, give them trimmed extracts or summaries, never the raw XML — large-file agents stall and return nothing (see MEMORY.md "Build-process lessons").
