# Open questions

- [intent] PROJECT.md's Overview doesn't mention budgets / `status` at all: what is a "budget" in this domain (strictly monthly? per category only? may `remaining` go negative and how should overspend be shown)? → GLOSSARY.md
- [intent] The project has no glossary for core terms (expense, category, budget, spent / remaining, month as `YYYY-MM`) → GLOSSARY.md
- [intent] What currency are the "cents" in, and is there an upper bound on a single amount or budget that the tool should reject? → PROJECT.md「Coding standards」
- [intent] Should `categories` (and other category listings) include categories that only exist in `budgets`, or only those used by expenses? → PROJECT.md「Domain and docs」
- [intent] Default dates (`add` without `--on`, `status` without `--month`) use the local `date.today()`: is local time the intended rule, or should a timezone be fixed? → PROJECT.md「Coding standards」
- [intent] Since this repo doubles as the sandcastle-pipeline e2e project, are there limits on feature scope (e.g. keep it stdlib-only and tiny, no new persistence/output formats) beyond the existing red lines? → PROJECT.md「Overview」
- [intent] May pipeline agents edit `.github/workflows/ci.yml` (including the `CI_MODE` pass/fail/slow switch) or anything under `.sandcastle/`, or must they stop? → PROJECT.md「Stop and ask」
- [convention] Ordering of list-style output is inconsistent (`report` sorts by total desc then name, `report --average` / `budget list` / `status` sort by name): which order should new commands use? → PROJECT.md「Coding standards」
- [convention] Notes are free text but output is tab-separated: should tabs/newlines in `--note` be rejected or escaped? → PROJECT.md「Coding standards」
- [convention] PROJECT.md says the merge gate runs `uv run mypy .` while the detected command is `uv run mypy` (`files = ["src"]`) and CI only runs pytest: which exact commands form the merge gate? → PROJECT.md「Commands」
- [convention] Ruff's default rule set doesn't enforce E501, and `cli.py` already has lines over 100 chars: is the 100-column limit a hard rule for new code, and are extra ruff rules expected? → PROJECT.md「Coding standards」
- [convention] Should the `version` in `pyproject.toml` be bumped when adding user-visible commands, or left to a human? → PROJECT.md「Commits」
- [convention] Commit subjects on main end with `(#N)`: is that added by squash-merge, or should agents reference the issue number themselves (and is there a branch naming convention)? → PROJECT.md「Commits」
