# CodeLens AI PR Review Assistant - Frontend (Phase 6 Bugfix)

## 当前功能
前端提供 React + Vite + TypeScript Review 工作台，支持：
- 输入 GitHub PR URL 发起分析
- 可选输入 GitHub Token（`password` 输入框）
- 勾选是否启用 AI Review（`use_ai`）
- 展示 PR 信息、变更统计、风险概览、风险详情、AI Review、Markdown 报告
- 一键复制 Markdown 报告（含降级复制方案）
- loading / error / empty state

## 安装依赖
```bash
npm install
```

## 启动开发环境
```bash
npm run dev
```

默认地址：`http://127.0.0.1:5173`

## 构建
```bash
npm run build
```

## 环境变量
在 `frontend/.env` 中配置（可从 `.env.example` 复制）：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 使用步骤（建议顺序）
1. 先启动后端（默认 `http://127.0.0.1:8000`）。
2. 再启动前端（默认 `http://127.0.0.1:5173`）。
3. 输入 GitHub PR URL。
4. 建议填写 GitHub Token（未认证请求容易触发 GitHub API rate limit）。
5. 选择是否启用 AI Review。
6. 点击“开始分析”。
7. 结果返回后可点击“复制 Markdown 报告”。

## 复制说明
- 前端优先使用系统 Clipboard API 自动复制 Markdown 报告。
- 若浏览器阻止自动复制，会提示手动复制；可点击“全选”后复制。

## 安全说明
- GitHub Token 推荐填写，以减少 GitHub API 限流问题。
- Token 只会通过请求体发送到本地后端，不会保存到 localStorage/sessionStorage/cookie。
- 不要把 GitHub Token 或 LLM API Key 写入前端代码、README 或提交记录。
