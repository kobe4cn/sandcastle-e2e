// Sandcastle 项目配置：编排脚本里随项目变的部分（由 sandcastle-pipeline onboard 生成，按需修改）。
// 字段说明见 sandcastle-pipeline 的 docs/config.md。
import { defineProject } from "sandcastle-pipeline";

export default defineProject({
  // forge: githubForge(),  // 默认 GitHub（宿主机的 gh）
  // 试跑期：只开 PR 不合并、一次一张。按 docs/onboarding-checklist.md 走完前几张票再打开自动合并、调高并行数。
  autoMerge: false,
  // 同时实现几张票：受测试依赖的服务（连接数）与机器负载限制
  maxParallel: 1,

  install: {
    // 沙箱建好后装依赖（容器是 linux，宿主机拷进来的原生包可能用不了）
    onSandboxReady: "uv sync",
  },

  isolation: {
    env: (runId) => ({
      // 手动跑 CLI 时用每张票自己的库，不在 worktree 里生成 ledger.db
      LEDGER_DB: `/tmp/ledger-${runId}.db`,
      SANDCASTLE_RUN_ID: runId,
    }),
    // cleanup: async (runId) => { /* 关沙箱后删掉这张票的测试库 */ },
  },

  gate: {
    // 合并门槛：退出码 0 算通过。输出约定（GATE_TIER / GATE_FLAKY）见 src/profile.ts 的 GateConfig，可以不用。
    script: () => "uv run mypy . && uv run ruff check . && uv run pytest",
    testFile: /\S*test_\S+\.py/,
    typecheck: "uv run mypy .",
  },

  // 几张票会同时往末尾追加的索引文件（CHANGELOG、测试目录……），列在这里的不算「改同一个文件」，可以并行。
  appendOnlyFiles: [],
});
