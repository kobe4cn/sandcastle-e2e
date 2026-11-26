---
name: prep-ticket
description: Before implementing a GitHub issue, split it into tickets that fit one implement session and add an Implementation guide to each, written from an Explore subagent's report. Use before /implement, or when the user asks to split or prepare a ticket.
argument-hint: "[issue number; omit to pick the next ready ticket]"
---

# Prep a ticket for /implement

The rules (size limit, vertical slices, guide template) are in `ticket-sizing.md` next to this file. Read it first. Write ticket bodies in the language of the existing issues.

Project facts (commands, test layout, docs, red lines):
- If `.sandcastle/PROJECT.md` exists, read its 测试 and 领域与文档 sections. That file is the **project notes** below.
- Otherwise the project notes are whichever of `CLAUDE.md`, `AGENTS.md`, `README.md` and `CONTRIBUTING.md` exist; skim them for test commands, test layout and where design docs / ADRs live. If they say nothing about tests, the Explore subagent finds the layout from the existing test files.

The ready label is `ready-for-agent`, unless `.sandcastle/sandcastle.config.ts` sets `labels.readyForAgent`; then use that name everywhere below. Check with `gh label list` that it exists; if it doesn't, ask the user which label marks agent-ready issues.

Keep this session light: never read source files in full here. All exploration goes through the Explore subagent.

## 1. Pick the ticket

- With an argument, use that issue: `gh issue view <n> --json number,title,body,labels,comments`.
- Without an argument, list open issues with the ready label. Take the lowest-numbered one whose `## Blocked by` issues are all closed, skipping spec / tracking issues that have `## Split into`.
- If a blocker is still open, check with `git log --oneline --grep "#<blocker>"` whether it was already implemented. If it was, tell the user it can be closed. Don't close it yourself.

## 2. Decide whether it needs work

- **≤3 acceptance criteria, ≤4 `Change` lines, and has `## Implementation guide`**: it's ready, unless the guide was written before its blockers landed or leaves a decision open ("如果 #x 决定…"). Spot-check two `file:line` references in the guide with `grep -n`. If they're stale, or either condition applies, refresh the guide (step 3) without splitting. Otherwise stop and say it's ready.
- **≤3 acceptance criteria, no guide**: add a guide (steps 3 and 5) without splitting. If the report shows more than 4 existing files to change, split instead.
- **More than 3 acceptance criteria, or more than 4 existing files to change**: split it and give each child a guide (steps 3–6).

## 3. Explore

Launch an `Explore` subagent with breadth "medium". Wait for its report, and don't explore the same code yourself meanwhile. Fill in this prompt:

```
仓库 <repo path>。我要给 GitHub issue #<n>（正文附后）<拆成几张小票，并且给每张票 / 补上>
一段「实现指引」，让之后实现它的 agent 不用自己探索代码。只读代码、不改文件，搜索广度 medium。

## 票的内容
<ticket body, or your draft of the slices>

## 请回答（只给结论，不贴文件内容或大段代码）
对每一块分别给出：
- 要改 / 新建的文件，精确到 `file:起止行`（要改的函数或区块的行范围）
- 可复用的已有接口：一行函数签名；表结构 / 类型的字段名
- 数据现在从哪来、存在哪（表、JSON 字段、类型定义）
- 相关的校验、权限、路由入口（loader / action 的位置）
- 相关的架构决定 / 设计文档（按 <项目说明文件> 里写的文档位置去查）
- 测试放哪个文件、可复用的 helper、可照着写的一个已有用例（按 <项目说明文件> 里写的测试布局去查；没写就看已有测试文件，给出文件 + 用例名）
- 种子数据或测试数据里会影响验收的事实
- 非显而易见的坑（会被校验拦下、缺失的属性、隐私或权限约束）
- 各块之间的依赖，每块要改几个已有文件，以及每块预计新增行数（含测试）

输出控制在 1500 字以内，用条目列出。
```

Replace `<项目说明文件>` with the project notes' paths. Add questions specific to the ticket, e.g. the seed tables named in its acceptance criteria.

## 4. Draw the slices

From the report, split the ticket into vertical slices. Each slice has ≤3 acceptance criteria, changes ≤4 existing files, and adds about ≤800 lines including tests. Every original acceptance criterion must land in exactly one child. Order the slices by their dependencies.

## 5. Write each guide

Use the template in `ticket-sizing.md` next to this file. Before publishing, `grep -n` two or three of the references to confirm the line numbers. Don't leave decisions to the implementer: settle each one now, write the outcome into the guide (or an ADR), and if it needs a human, ask the user before publishing.

## 6. Publish

Write bodies to temp files and pass them with `--body-file`.

- Create children blockers-first with `gh issue create --label <ready label>`. Each child body has `## Parent` #<n>, `## What to build`, `## Acceptance criteria`, `## Blocked by` (the parent's blockers and/or sibling numbers), and `## Implementation guide`.
- Parent: append `## Split into` with a checklist of children, and remove the ready label.
- Dependents: find open issues whose `## Blocked by` lists the parent (`gh issue list --state open --search "#<n>" --json number,body`). Repoint them to the right child, or comment if it's only a mention.
- Guide only (no split): append the section with `gh issue edit <n> --body-file`.

## 7. Report

Report in Chinese:
- A table of child tickets: number, title, AC count, blockers.
- The pitfalls the report surfaced.
- Which ticket to `/implement` first.
- Anything the user must decide, such as closing an implemented blocker.

Suggest `/clear` before `/implement` so the build session starts from the ticket alone.
