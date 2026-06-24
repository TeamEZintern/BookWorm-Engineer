# PROGRESS.md

Continuity notes for the paper2code / agent-loop hardening work on branch `feat/paper2code`.

_Last updated: 2026-06-24 (end of day) — items 4 & 5 applied (uncommitted); only the logic_design
cached-path fix remains before items 4/5 are fully closed._

## Done (committed in `9e6024c`)

Verified present in the working tree (clean except README.md + this file):

- **Fixed `validation.py:_run`** — `subprocess.run(command=command)` → positional `command`. The
  bad kwarg crashed `Popen`, silently making the **entire** validation stage a no-op (every check
  errored → gate skipped the rest → false "pass"). Validation only started doing real work after this.
- **Item 1 — repair-loop convergence (DONE):**
  - `validation.py:_run_validation` no longer skips pytest when ruff lint fails — pytest runs
    regardless of the lint result (`validation.py:452-456`), so the repairer sees lint + test
    failures in one attempt.
  - `--unsafe-fixes` added to `_run_ruff_autofix` (`validation.py:292`).
  - `MAX_VALIDATION_ATTEMPTS` bumped 3 → 6 (`pipeline.py:13`).
  - Repair-prompt rule "no new unused vars / use raw strings for regex" (`paper2code/prompts.py:39`).
- **Item 2 — agent transient-failure resilience (DONE):**
  - `complete_with_retry(client, *, on_retry=None, **kwargs)` extracted into `bookworm/llm.py`
    (retries `APIConnectionError` / `RateLimitError` / `InternalServerError` / `json.JSONDecodeError`
    with exponential backoff, `MAX_API_RETRIES = 4`; lets 4xx raise).
  - Used in `agent._run_turn` (`agent.py:173`); failed turn made non-fatal via
    `checkpoint = len(self.messages)` + `del self.messages[checkpoint:]` (`agent.py:97,111`).
- **Item 3 — pipeline `_llm` uses `complete_with_retry`** (`pipeline.py:11,16`).
- Created repo `CLAUDE.md` (architecture doc + "teach, don't just apply" working-style rule).

## Done today (2026-06-24, applied — UNCOMMITTED in working tree: `pipeline.py`, `prompts.py`)

- **Item 4 — content-level JSON self-correction (applied):** added `_llm_json` helper (`pipeline.py:27`)
  that re-rolls on parse failure, feeding the bad output back with a corrective "reply with ONLY valid
  JSON" message; each attempt still goes through `complete_with_retry` (content vs transport retry kept
  separate). Rewired `success_criteria` and `architecture` stages to save the artifact **only after a
  successful parse** (closes the poison-cache bug). Helper bugs fixed during validation: invalid
  `"assitant"` role → `"assistant"` (`:54`); `content` now guarded with `or ""` (`:47`).
- **Item 4 follow-on — `PIPELINE FAILED:` prefix + no raw dump:** architecture cached-path error now
  returns a clean `PIPELINE FAILED: cached architecture.txt is not valid JSON: ...` (`:367`).
- **Item 5 — agent guardrail (applied):** added the paper-to-code rule to `bookworm/prompts.py:72-75`
  — pipeline return value is the source of truth; on `PIPELINE FAILED:`/no-confirmation, report to the
  user and offer retry; never scaffold/hand-write the repo; OPERATING MANDATE "build files" steps do
  not apply to paper repos.
- **Verified:** `ruff check bookworm/` clean; `pytest` 15/15 pass; `_llm_json` re-roll proven with a
  fake-client smoke; the earlier `complete_with_retry() takes 1 positional argument but 3 were given`
  TypeError confirmed to be a ghost from an old positional call, now fixed (all call sites use kwargs).
- **NOT done (carried to WIP item A):** the `logic_design` stage still has the cached-path
  `NameError` — items 4/5 are not fully closed until that lands. Next step: commit once A is in.

## Fix queue (remaining — priority order)

(Items 1–5 are applied; the only remaining piece of items 4/5 is the logic_design cached-path fix,
tracked as WIP item A below. New design work is WIP item B.)

## Key diagnoses (expensive to re-derive)

- **Repair can't converge** (now mitigated by item 1): gated validation used to surface only one
  failure category per attempt (lint → tests → lint); with 3 attempts and two alternating categories
  it was structurally stuck. There is also a **test-vs-code oracle problem**: tests and code are both
  LLM-generated from the paper, so when they disagree there is no ground truth to repair against.
- **Euclidean DGP run "left the pipeline"** (item 4 target): `run_pipeline` early-returned at logic
  design because `logic_design.txt` was structurally invalid JSON (model wrapped `"key": "value"`
  pairs in `[ ]` instead of `{ }`). The error string went back to the agent, which (a) mistook the
  plain-string failure for success and (b) scraped the task_list out of the embedded raw response,
  then hand-wrote the repo **outside** the pipeline. Item 4 stops the malformed JSON from killing the
  run; item 5's guardrail stops the agent from improvising when a stage does fail.
- **Two distinct JSON-error categories** — keep separate: transport-level (SDK parsing a non-JSON HTTP
  body → transient → retry, item 2/3) vs content-level (model emits malformed JSON → re-roll, item 4).

## WIP — resume here tomorrow (2026-06-25)

### A. Finish the item-4 logic_design fix (small, do first)
The cached `logic_design` path still raises `NameError: cannot access local variable 'logic'` — reproduced
2026-06-24. Lines 384–387 (`try: logic = _extract_json(logic_raw)`) are still nested *inside* the
`if logic_raw is None:` block, so a resumed run skips assigning `logic`. Fix = convert to the same `if/else`
shape `architecture` uses (drop the dead re-parse, add an `else:` that parses the cached raw and returns
`PIPELINE FAILED: cached logic_design.txt is not valid JSON: ...`). Snippet was already drafted in chat.
Then re-run: `ruff check bookworm/`, `pytest`, and the cached-path smoke.

### B. Repair-loop non-convergence (the real work — see memory `paper2code-repair-nonconvergence.md`)
Evidence run: `User-Facing/.bookworm/paper2code/Euclidean_Distance_Geometry_and_Applications/`
(`validation/result.txt` = failed, 6 attempts, 5 triage rounds). Repair cleared the mechanical failures
(markdown fence in a test file → attempt 2; `F821 self` in geometry_utils.py → attempt 3) but then stalled:
attempts 3–6 produced the **identical** pytest failing set (BP returns wrong #solutions; DMDGPValidator /
discretization-subset logic wrong). Root causes:
1. Remaining bugs are genuine **algorithm-correctness** bugs, not mechanical ones.
2. **No ground-truth oracle** — tests and code are both LLM-generated; triage always blamed the code and
   treated possibly-wrong tests as truth → impossible target.
3. **Per-file isolated repair** (`pipeline.py:561-579`) can't fix coupled files (`bp_algorithm.py` ↔
   `graph_structures.py`) — separate LLM calls, no shared reconciliation.
4. **No stagnation detection** — loop re-ran identical triage+repair until it hit `MAX_VALIDATION_ATTEMPTS`.

Proposed directions (not yet designed): (a) a no-progress detector comparing this attempt's failing set to the
previous one; on a repeat, let triage flip to suspecting the **test**, not only the code; (b) repair coupled
files in a **single** LLM call with the full failing context instead of one isolated call per file.

### C. Minor, low priority
`validation.py:_make_relative_file` emitted a malformed `/tests//test_bp_algorithm.py` (leading + double
slash) in attempt-1 `failed_files`. Didn't cause the failure; clean up the path normalisation when convenient.
