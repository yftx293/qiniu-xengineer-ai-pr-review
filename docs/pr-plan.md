# PR 开发计划

本项目按照小步提交、持续交付的方式进行开发。每个 PR 尽量只完成一个独立功能，合并后保证 main 分支可运行。

## 阶段一：项目初始化

- PR 1：docs: add project plan and architecture draft

## 阶段二：后端基础能力

- PR 2：feat: initialize backend service
- PR 3：feat: parse GitHub PR url
- PR 4：feat: fetch GitHub PR metadata and changed files

## 阶段三：核心分析能力

- PR 5：feat: add diff parser
- PR 6：feat: implement rule-based risk analyzer
- PR 7：feat: integrate AI review generation

## 阶段四：前端展示能力

- PR 8：feat: initialize frontend review page
- PR 9：feat: display review summary and risk table
- PR 10：feat: add markdown report copy feature

## 阶段五：收尾与文档

- PR 11：fix: improve error handling
- PR 12：docs: add final README and demo video link

## 比赛冲刺阶段补充计划

- PR 7（新）：docs: finalize README, architecture, and demo materials
- PR 8（新）：test: add backend unit and route coverage
- PR 9（新）：feat: add analysis trace and explainability output
- PR 10（新）：feat: polish frontend dashboard for demo presentation

## PR 描述模板要求

每个新 PR 描述统一包含以下结构：

- 标题
- 背景
- 本次只解决什么问题
- 实现思路
- 影响范围
- 测试方式
- 截图或结果示例
- 是否影响主流程
