# PROJECT.md（sandcastle-e2e）

## 概况

`ledger`：基于 SQLite 的个人记账命令行工具（记一笔支出、列出、按类别汇总、删除）。同时是 sandcastle-pipeline 的端到端测试项目。

- 技术栈：Python ≥ 3.11，只用标准库（`argparse`、`sqlite3`、`decimal`），运行时无第三方依赖；包管理用 uv，构建用 hatchling。开发工具：pytest、ruff、mypy（strict）。
- 入口：`pyproject.toml` 的 `[project.scripts]` 把 `ledger` 命令指向 `ledger.cli:main`；运行方式 `uv run ledger add 12.50 food --note lunch`。
- `src/ledger/cli.py`：子命令定义（`build_parser()`）和分发（`main()` 里的 `if/elif` 链）。只做参数解析、调用、打印；业务校验放在 `db.py` / `money.py`。
- `src/ledger/db.py`：表结构（模块常量 `SCHEMA`）、`connect()`、`Expense` 数据类、增删查函数。所有 SQL 都在这里。
- `src/ledger/money.py`：`parse_amount()`（文本 → 整数分）、`format_cents()`（整数分 → 文本）。
- `src/ledger/report.py`：对 `list[Expense]` 做汇总的纯函数（`totals_by_category`、`monthly_totals`）。
- `tests/`：pytest 测试，一个源模块对应一个 `test_<模块>.py`。

## 运行环境

- 不需要任何外部服务。数据库是本地 SQLite 文件，路径取自环境变量 `LEDGER_DB`（默认当前目录的 `ledger.db`）。
- 测试一律用 `tmp_path` 下的临时库（见下面的夹具），不要在仓库目录里生成 `ledger.db`。

## 开发命令

- 类型检查：`uv run mypy .`（strict 模式；`pyproject.toml` 里 `files = ["src"]`，但合并门槛跑的是 `.`，所以 `tests/` 也要过类型检查）
- lint：`uv run ruff check .`（行宽 100）
- 跑单个测试文件：`uv run pytest tests/test_db.py`；全部：`uv run pytest`
- 改了 `pyproject.toml` 的依赖后跑 `uv lock` 重新生成 `uv.lock`，并把两个文件一起提交；不要手改 `uv.lock`。
- 项目没有配置格式化工具（没有 `ruff format` 配置），不要整文件重排格式。

## 测试

- 夹具在 `tests/conftest.py`：
  - `conn`：连到 `tmp_path/test.db` 的 `sqlite3.Connection`，已建表。测 `db.py` / `report.py` 用它，直接调 `db.add_expense(conn, date(...), ...)` 造数据。
  - `ledger_db`：用 `monkeypatch` 把 `LEDGER_DB` 指到临时文件。测 CLI 用它，配合 `capsys`，调 `main([...])` 断言返回码和 `stdout`/`stderr`。
- 找相似用例：新 CLI 子命令看 `tests/test_cli.py`；新查询看 `tests/test_db.py`；新汇总看 `tests/test_report.py`；金额解析看 `tests/test_money.py`。
- 多组输入用 `@pytest.mark.parametrize`（参考 `test_money.py`、`test_db.py::test_rejects_invalid`）。
- 测试函数要写完整类型标注（参数和 `-> None`），文件开头 `from __future__ import annotations`，和现有测试一致。
- 日期写死成固定值（如 `date(2026, 1, 1)`、`--on 2026-01-02`），不要依赖 `date.today()`。
- 新增测试文件放在 `tests/` 下、命名 `test_*.py` 即可被收集，没有别的地方需要登记。

## 编码规范

- 金额一律是整数「分」（`int`），只在 `money.py` 的边界做转换：输入用 `parse_amount()`，输出用 `format_cents()`。不要用 `float` 表示金额。
- 类别在写入和查询前都要 `strip().lower()`（见 `db.add_expense`、`db.list_expenses`），新增按类别的查询保持一致。
- SQL 只用 `?` 占位符传参，不要字符串拼接值。
- CLI 错误：打印 `error: <原因>` 到 `stderr`，返回非零码（参数/校验错误为 `2`，对象不存在为 `1`）；成功返回 `0`。`main()` 返回 `int`，不调用 `sys.exit`。
- CLI 列表类输出是制表符分隔的行，测试按整行精确断言；改动已有命令的输出格式要同步改测试，并在 PR 里说明。
- 每个模块顶部有一行模块 docstring，新模块照做。

## 领域与文档

- 没有术语表和 ADR。用户可见的用法写在 `README.md`：新增或改动 CLI 子命令、环境变量时同步更新 README 里的示例。

## 必须停下

- 需要修改已有 `expenses` 表的列或约束（`db.py` 的 `SCHEMA`）：项目没有迁移机制，`CREATE TABLE IF NOT EXISTS` 不会改动用户已有的 `ledger.db`。只新增独立的新表可以继续做。
- 需要引入运行时第三方依赖（`[project] dependencies` 目前为空）。

## 合并冲突

- `src/ledger/cli.py`：两边都新增子命令时，`build_parser()` 里的 `sub.add_parser` 块和 `main()` 里的 `elif args.cmd == ...` 分支都保留，各自顺序不变。
- `tests/conftest.py`、`README.md`：两边都追加的内容都保留。
- `uv.lock`：不要手工合并。先解决 `pyproject.toml` 的冲突，然后跑 `uv lock` 重新生成，再继续 rebase。

## 人工验收

宿主机上 `uv sync`，然后用临时库试命令，不碰自己的真实账本：`LEDGER_DB=/tmp/ledger-check.db uv run ledger add 12.50 food --note lunch`，再跑 `list` / `report` / 新增的子命令看输出。

## 提交

- 英文提交信息，参考 `git log -n 3 --format=%B origin/main`：第一行一句话概括做了什么（首字母大写、不加句号、不用 `feat:` 之类前缀）。
- 需要时空一行再写正文：关键决定、改动的文件、验证结果（mypy、ruff、跑过的测试文件）。
