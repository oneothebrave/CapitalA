# CapitalA

本项目是一个面向美股的量化研究与智能研判系统。第一版只支持用户输入美股 ticker，系统后续将基于行情、SEC 公告、财报、新闻等数据生成可解释、可回测、可追溯的单股研究结论。

开发前请先阅读：

- `AGENTS.md`
- `docs/us-stock-quant-research-architecture-v1.md`

## 当前阶段

当前处于项目骨架阶段：

- 后端使用 Python、uv、FastAPI
- 暂不接 PostgreSQL
- 暂不创建前端
- 存储层先预留文件系统结构
- 数据源、报告格式、CLI/前端入口后续再定

## 后端启动

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

健康检查：

```text
GET /api/v1/health
```

运行测试：

```bash
cd backend
uv run pytest
```
