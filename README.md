# CapitalA

本项目是一个面向美股的量化研究与智能研判系统。第一版只支持用户输入美股 ticker，系统后续将基于行情、SEC 公告、财报、新闻等数据生成可解释、可回测、可追溯的单股研究结论。

开发前请先阅读：

- [HANDOFF.md](HANDOFF.md)：换设备接力、当前进度和下一步。
- [AGENTS.md](AGENTS.md)：项目开发约束。
- [需求与架构](docs/us-stock-quant-research-architecture-v1.md)：第一版范围和后续路线。
- [数据采集层设计](docs/data-ingestion-layer-sources-v1.md)：数据来源规划和已实现的采集契约。
- [后端说明](backend/README.md)：运行命令、配置和接口。

## 当前阶段

当前已完成项目骨架及数据采集层通用契约：

- 后端使用 Python、uv、FastAPI
- 健康检查可用；股票分析接口仍返回 HTTP 501
- 已实现采集请求、原始文件保存、SHA-256 校验、采集 manifest 和可用时间过滤
- 尚无 ticker 注册表、真实数据 provider 或采集任务
- 特征、评分、报告、回测、任务调度仍是目录占位
- 使用文件系统存储，未接 PostgreSQL、DuckDB 或 AI API
- 尚无前端或 CLI；下一步为 ticker 注册表

## 后端启动

```bash
cd backend
uv sync --locked
uv run --locked uvicorn app.main:app --reload
```

健康检查：

```text
GET http://127.0.0.1:8000/api/v1/health
```

运行测试：

```bash
cd backend
uv run --locked pytest
uv run --locked ruff check .
```

需要 Git、uv 和 Python 3.13+。跨设备安装应保留 `backend/uv.lock`，在新设备重建虚拟环境。
