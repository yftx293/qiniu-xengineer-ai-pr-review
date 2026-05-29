# CodeLens AI PR Review Assistant

CodeLens 是一个面向开发者的 AI Pull Request 代码评审助手。本项目选择七牛云 × XEngineer 暑期实训营题目三：AI PR Review 助手。

用户输入 GitHub PR 链接后，系统会自动获取 PR 基本信息和代码变更内容，并生成 PR 变更总结、风险代码识别结果和 Review 建议，帮助开发者提升 Pull Request Review 的效率与质量。

## 1. 项目背景

在日常开发中，Pull Request Review 往往存在以下问题：

- Review 人需要手动阅读大量 diff，耗时较长。
- 安全风险、异常处理、依赖变更、测试缺失等问题容易被遗漏。
- Review 建议不够结构化，沟通成本较高。
- 新人开发者难以快速理解 PR 的主要变更和潜在风险。

因此，本项目希望通过 AI 辅助分析和规则风险识别，帮助开发者更高效地完成 PR Review。

## 2. 核心功能规划

当前计划实现以下功能：

- GitHub PR 链接解析
- PR 基本信息获取
- PR 变更文件与 diff 获取
- PR 变更总结生成
- 风险代码识别
- Review 建议生成
- Markdown Review 报告复制
本项目第一阶段先完成 GitHub PR 数据获取与基础 Review 流程，后续逐步补充风险识别、AI 总结和前端展示能力。
## 3. 技术栈

前端：

- React
- Vite
- TypeScript

后端：

- Python
- FastAPI
- Pydantic
- Requests

外部服务：

- GitHub REST API
- OpenAI-compatible LLM API

## 4. 项目结构

```text
qiniu-xengineer-ai-pr-review/
├─ README.md
├─ docs/
│  ├─ design.md
│  └─ pr-plan.md
├─ backend/
│  ├─ README.md
│  └─ app/
├─ frontend/
│  ├─ README.md
│  └─ src/
└─ screenshots/