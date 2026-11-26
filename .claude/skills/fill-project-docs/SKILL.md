---
name: fill-project-docs
description: Work through the open questions list (.sandcastle/OPEN-QUESTIONS.md) with the user one question at a time, writing each answer into PROJECT.md, the glossary or an ADR and deleting it from the list. Use right after sandpipe onboard, or when sandpipe doctor's project knowledge check says open questions remain.
---

# Fill in the project docs

`sandpipe onboard` drafts `.sandcastle/PROJECT.md` from the code and puts what it couldn't settle into the **open questions list** `.sandcastle/OPEN-QUESTIONS.md`. The pipeline's agents can only follow conventions and intent that are written down, so this session turns each open question into a written answer.

**Language.** These instructions are in English, but ask questions and write docs in the project's language: if PROJECT.md's section titles are Chinese (`## 概况`, `## 必须停下`), use Chinese; if they're English (`## Overview`, `## Stop and ask`), use English.

## 1. Read the list

Read `.sandcastle/OPEN-QUESTIONS.md`. Blank lines and `#` headings are ignored; every other line is one item:

```
- [category] question → where to write it
```

The category is `规范` / `convention` (how things are done here) or `意图` / `intent` (why, what matters, what is off limits). If the file doesn't exist, tell the user to run `sandpipe onboard --questions-only` first and stop. If it has no items, skip to step 3. If a line doesn't match the format, show it to the user and fix it with them before going on.

Also read `.sandcastle/PROJECT.md`, and `CONTEXT.md` or `GLOSSARY.md` if either exists, so you don't ask about something already written down.

## 2. Work through the items, one question at a time

Take the items in order. For each one:

1. **Look up facts yourself.** If the answer can be found in the code, config, git history or existing docs (a command, a file layout, which library is used), find it and show the user what you found instead of asking. Only ask about what nobody can read off the code: preferences, business rules, red lines, reasons.
2. **Ask one question and wait.** Give your recommended answer, with what you saw in the code that suggests it. Follow up if the answer is vague or uses a fuzzy term, but stay on this item.
3. **"Not needed" counts as answered.** If the user says it doesn't apply, the item is done. Where the target section would otherwise look unfinished, write that explicitly (e.g. "无" / "None").
4. **Write the answer immediately**, at the place given below (the `→` part of the item is a hint; these rules win when they disagree).
5. **Delete that line from the list** right after writing. Don't batch: if the session stops halfway, the list shows exactly what is left. Keep the file even when its last item is gone; an empty list means "done", a missing one means "never generated".

### Where each answer goes

| Kind of answer | Where |
|---|---|
| Convention (code style, tests, commits) | PROJECT.md: `编码规范` / `测试` / `提交` (English: `Coding standards` / `Testing` / `Commits`) |
| Red line (what an agent must never do on its own) | PROJECT.md: `必须停下` / `Stop and ask` |
| Term or business rule | The existing `CONTEXT.md` or `GLOSSARY.md`; if neither exists, create `GLOSSARY.md` at the repo root. A business rule goes into the definition of the term it constrains, not into a separate file |
| Reason for a design | An ADR in `docs/adr/` only if all three tests below hold; otherwise one or two sentences in PROJECT.md `领域与文档` / `Domain and docs` |

PROJECT.md rules: edit the existing section and use only the existing section titles; never invent a new `##` title or add a second heading for a section (the Chinese and English titles count as the same section, so don't add `## Stop and ask` to a file that has `## 必须停下`). doctor fails on either. Keep entries short and concrete; agents read this file on every run.

Glossary format (one entry per term; definitions say what it *is*, one or two sentences, no implementation details; list rejected synonyms under `_Avoid_`):

```md
**Order**:
A request from a customer to buy one or more products.
_Avoid_: purchase, transaction
```

ADR tests, all three must hold:

1. **Hard to reverse**: changing course later costs real work.
2. **Surprising without context**: a reader of the code would wonder why it was done this way.
3. **A real trade-off**: there were genuine alternatives and this one was picked for specific reasons.

ADRs are numbered `docs/adr/NNNN-slug.md` (scan for the highest number and add one). A title plus a short paragraph of context, decision and reason is enough; add rejected options or consequences only when they matter. If `docs/adr/README.md` is an index, add the new ADR to it.

**References.** When you create the glossary file or an ADR, add a reference to it in PROJECT.md `领域与文档` / `Domain and docs` (one line: path and what it's for), so agents know to read it.

## 3. Core terms (optional)

When the list is empty, ask the user whether to also sweep the code for core domain terms. Only if they agree: find up to 10 terms that are specific to this project (names of entities, states, roles that recur in the code and UI; not general programming words), propose a definition for each, and let the user correct them one at a time. Write each confirmed term into the glossary as above, challenging terms that clash with entries already there.

## 4. Self-check

Run `sandpipe doctor`. Fix any `fail` it reports for the files you touched (most likely a duplicated or misspelled PROJECT.md section) and run it again. The project knowledge check should now show fewer open questions, or none.

## 5. Commit

List every file you changed or created, with a one-line summary of each change. Wait for the user to confirm, then commit them to the current branch with a message in the project's commit style (see PROJECT.md `提交` / `Commits`). Don't push.

## 6. Tell the user when it takes effect

- PROJECT.md changes take effect immediately: the pipeline renders its prompts from the local file at startup (a pipeline that is already running needs a restart).
- The glossary and ADRs only reach the agents in the sandbox after they are pushed to the base branch (`baseBranch` in `.sandcastle/sandcastle.config.ts`, usually `main`), because sandbox worktrees are created from the remote base branch. Remind the user to push (or merge) before running the pipeline on tickets that depend on them.
