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
uv sync
```

启动服务：

```bash
uv run uvicorn app.main:app --reload
```

运行测试：

```bash
uv run pytest
```

## 当前接口

```text
GET /api/v1/health
GET /api/v1/stocks/{ticker}/analysis
```

`/api/v1/stocks/{ticker}/analysis` 当前只是占位接口，后续接入 ticker 注册表、数据采集、特征、评分和报告生成。
