# AI assistance disclosure

The user supplied the research question, two conditions, fixed claim, outcomes, five problem types and intended bugs, scope, and validation requirements. ChatGPT drafted the JSON pilot fixtures, candidate implementations, expected outputs, prompt builder, validation helpers and pytest suite, README, experiment plan, and packaging. ChatGPT ran local validation and recorded actual results; no judge observations were generated or invented.

All 35 task records identify AI-assisted review (`reviewed_with_ai_assistance`). This status describes review performed with AI assistance; it does not mean independent human verification. Independent human verification remains pending for every task. The tasks are custom examples drafted with AI assistance, not copied benchmark tasks. No novelty is claimed. The ordinary-case conflict for the sum task was identified and documented instead of changing the requested bug or mislabeling zero as an ordinary positive input.

No LLM APIs were called by this project; no model was downloaded, key requested, billing enabled or deployment performed. AI assistance in this conversation is distinct from running an LLM judge experiment. See the execution log and JSON report for the actual local environment and checks.

## User-requested Stage  1 requirement revision
ChatGPT amended the valid-input requirement, replaced the p05 xfail with actual assertions, retained all other checks, preserved the original validation report, and reran validation. The five JSON pilot files were left byte-for-byte unchanged, verified against the original report hashes. The revision changes no human-review statuses and involves no LLM API calls or main-study data.
