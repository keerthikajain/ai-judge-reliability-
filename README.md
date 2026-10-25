# AI Judge Reliability — Stage 1

Local scaffolding and debugging examples only. No LLM calls, credentials, models, billing, or deployment. All 35 task records identify AI-assisted review (`reviewed_with_ai_assistance`); independent human verification remains pending for every task.

## Windows PowerShell
Extract the ZIP contents directly into `D:\ai-judge-reliability`. The archive has no extra enclosing folder. Do not overwrite existing files: if Windows reports a conflict, cancel and compare first.

With Python 3.12 installed, run:

```powershell
Set-Location 'D:\ai-judge-reliability'
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.run_validation
```

No environment activation or PowerShell execution-policy change is needed. Installing pytest needs package-index access; running validation after installation is local. The validation command runs pytest and writes `outputs/pilot/stage1_validation.json`. To run just tests: `.\.venv\Scripts\python.exe -m pytest -q -ra`.

## Contents and decisions
- `data/pilot/p01.json` through `p05.json`: human-readable cases, private solutions and metadata. Separate files make individual review easy.
- `src/prompts.py`: keyword-only statement/code/fixed-claim allowlist. It accepts no complete dataset record and emits no correctness label.
- `src/validation.py`: executes these trusted local snippets and checks exact output types as well as values, using fresh input copies.
- `tests/test_stage1.py`: schema, signatures, reference results, intended bugs, and prompt checks.
- `src/run_validation.py`: actual pytest results, case outputs, versions and source hashes.
- `experiment_plan.md`: draft design and outstanding choices.
- `AI_ASSISTANCE.md`: disclosure of generated work.
- `outputs/pilot/execution_log.txt`: creation-time execution record.

These snippets use exec solely for our trusted local fixtures. The helpers are not a security sandbox for arbitrary code.

## Revised valid-input requirement
Each faulty solution must pass at least one valid test input. This may be an ordinary or boundary case.

The p05 range(1, n) bug fails every positive n and passes n=0. The previous ordinary-case requirement conflicted with that bug. It is now replaced by actual assertions; there is no p05 xfail. All five candidates must pass at least one specified valid input and fail their named counterexample. The existing ordinary-case checks for p01-p04 remain in place.

Original evidence is preserved in `outputs/pilot/history/stage1_validation_before_requirement_revision.json` and `outputs/pilot/execution_log.txt`. The revised run is recorded in `outputs/pilot/revision_execution_log.txt` and the current JSON report. Read those files for actual test counts. AI-assisted review is not independent human verification; independent human verification remains pending.

The included report is from the creation environment, not your Windows machine. Re-running overwrites the report with your actual local results. Passing fixture tests says nothing about LLM judge behaviour.
