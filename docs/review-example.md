# 示例 Review 报告

以下内容用于展示 CodeLens 的典型输出形态，帮助评委快速理解作品的最终价值。该示例为演示用途，字段结构与系统当前能力保持一致。

---

# AI PR Review Report

## 1. PR 基本信息

- 标题: Refactor login flow and add token validation
- 作者: demo-user
- 状态: open
- 分支: feat/login-refactor -> main
- 文件数: 4
- additions / deletions: 86 / 24

## 2. 变更总结

本次 PR 主要重构了登录流程，新增了 token 校验逻辑，并调整了部分错误处理分支。整体改动集中在认证链路，虽然结构更清晰，但也引入了认证与异常处理层面的潜在回归风险。

## 3. 主要变更

- `backend/app/services/auth_service.py`：新增 token 校验逻辑
- `backend/app/routes/login.py`：调整登录接口的错误返回结构
- `frontend/src/components/LoginForm.tsx`：同步适配新的错误提示
- `backend/tests/test_login.py`：补充登录异常路径测试

## 4. 风险概览

- total: 3
- high: 1
- medium: 2
- low: 0
- has_blocking_risk: true

## 5. 风险详情

| Severity | Confidence | File | Type | Evidence | Suggestion |
| --- | --- | --- | --- | --- | --- |
| High | High | backend/app/services/auth_service.py:42 | Hardcoded Secret | SECRET_KEY = "demo-secret" | 建议改为从环境变量读取，不要在代码中硬编码敏感信息 |
| Medium | High | backend/app/routes/login.py:68 | Swallowed Exception | except Exception: pass | 建议补充日志记录和明确错误处理分支 |
| Medium | Medium | PR-level | Missing Tests | total_changed=110 | 建议补充端到端测试或更多负向用例覆盖 |

## 6. Review 建议

- 优先处理硬编码敏感信息问题，避免将密钥直接写入代码仓库
- 对登录失败和 token 失效场景补充更完整的测试覆盖
- 对异常吞掉位置增加日志和明确的失败返回，降低排障难度

## 7. 分析链路

- context_source: github_api_pr_and_files
- ai_status: completed
- patch 截断文件数: 0
- rule_hits_by_type:
  - Hardcoded Secret: 1
  - Missing Tests: 1
  - Swallowed Exception: 1

## 8. 分析限制

- GitHub API 可能受未认证 rate limit 影响
- 超长 patch 会被截断，极大 PR 的上下文可能不完整
- AI 结果仅作辅助参考，最终仍需人工确认

## 9. 说明

本报告由规则分析和可选 AI 生成，仅作为辅助 Review 参考，最终仍需人工确认后再做合并决策。

---

## 如何在演示中使用这份示例

- 用它说明“最终输出不是一段散文，而是一份结构化报告”
- 用它展示风险等级、建议、置信度和分析链路这些差异化能力
- 用它辅助介绍“规则分析 + AI 生成”的混合方案为什么更适合代码评审场景
