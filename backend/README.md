# CapitalA Backend

CapitalA 后端。项目面向美股量化研究与智能研判，第一版只支持 ticker 输入。

## 技术选择

- Python 3.13+
- uv
- FastAPI
- pytest

## 本地开发

安装依赖：

```bash
uv sync --locked
```

启动服务：

```bash
uv run --locked uvicorn app.main:app --reload
```

运行测试：

```bash
uv run --locked pytest
uv run --locked ruff check .
```

以上命令在 `backend/` 目录执行。完整迁移步骤见根目录 [HANDOFF.md](../HANDOFF.md)。

## 当前接口

```text
GET /api/v1/health
GET /api/v1/stocks/{ticker}/analysis
```

`/api/v1/health` 返回 HTTP 200；`/api/v1/stocks/{ticker}/analysis` 返回 HTTP 501，目前只对输入去空格并转为大写，没有 ticker 有效性校验或分析能力。

开发服务默认地址为 `http://127.0.0.1:8000`，交互式 API 文档位于 `/docs`。

## 配置与存储

配置定义在 `app/core/config.py`，从进程环境变量及当前工作目录的 `.env` 读取 `QUANT_` 前缀字段。无 `.env` 也可启动。示例配置见 `.env.example`，其中应用名称会覆盖代码默认的 `CapitalA`。

默认数据目录为仓库根目录下的 `data/`；可通过 `QUANT_DATA_DIR` 指定绝对路径。原始文件写入 `data/raw/`，采集 manifest 按需写入 `data/manifests/ingestion_runs/`。

原始数据和 manifest 必须配套保留。两者均不进入 Git；已有 manifest 的 `raw_storage_path` 当前为机器本地路径，迁移真实数据时需要核对或重定位。

## 已实现模块

- `data_ingestion/manifest.py`：采集请求、原始文件元数据、错误记录、任务状态和可用时间过滤。
- `data_ingestion/providers/base.py`：同步 `fetch(request)` 协议；没有具体 provider。
- `data_ingestion/storage.py`：原始 payload 保存、SHA-256 hash 及 manifest JSON 写入。
- `storage/file_store.py`：通用路径与目录助手。

详细契约、限制和后续实现顺序见 [数据采集层设计](../docs/data-ingestion-layer-sources-v1.md)。
