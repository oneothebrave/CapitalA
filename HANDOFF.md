# CapitalA 开发交接

更新日期：2026-10-12。此文档是迁移时的进度快照，后续开发应结合实际代码和测试更新。

## 1. 接力入口

项目仓库：<https://github.com/oneothebrave/CapitalA>。当前开发分支为 `master`，跟踪 `origin/master`。整理前基线提交为 `9336776`（`Add Jev`）；本次整理后的提交以 `git log -1` 为准。

建议阅读顺序：

1. 本文：当前完成范围、启动和下一步。
2. [AGENTS.md](AGENTS.md)：开发约束。
3. [第一版需求与架构](docs/us-stock-quant-research-architecture-v1.md)：系统目标和路线。
4. [数据采集层设计](docs/data-ingestion-layer-sources-v1.md)：来源规划及第 11 节已实现契约。
5. [后端说明](backend/README.md)：运行命令、配置和接口。

## 2. 当前阶段

项目目标是单股美股量化研究：输入 ticker，获取行情、SEC 公告、财报和 ticker 绑定新闻，生成有依据、可追溯、可回测的研究结论。

实际处于“项目骨架 + 数据采集通用契约”阶段，还没有可用的股票研究闭环，也没有真实采集数据。

| 模块 | 当前状态 |
| --- | --- |
| 工程环境 | Python 3.13+、uv、FastAPI；`pyproject.toml` 和 `uv.lock` 已提交 |
| API | 健康检查可用；股票分析为 HTTP 501 占位接口 |
| 采集契约 | 请求、原始文件、错误、manifest 模型及同步 provider 协议已实现 |
| 文件存储 | 原始 payload、SHA-256 hash、唯一文件名和 manifest JSON 写入已实现 |
| 时间过滤 | 带时区时间校验及 `available_at <= cutoff` 文件筛选已实现 |
| ticker 注册表 | 未实现；只有 `reference_data/` 包占位 |
| 实际采集 | SEC、行情、新闻等具体 provider 和采集 job 均未实现 |
| 标准化、特征、评分、报告、回测、调度 | 只有包占位文件 |
| 数据库、AI、交互入口 | 未接数据库或 AI API；没有前端或 CLI |

主要代码入口：

- `backend/app/main.py`：创建 FastAPI 应用。
- `backend/app/core/config.py`：配置读取和默认数据目录。
- `backend/app/api/routes/`：健康检查及股票分析占位。
- `backend/app/data_ingestion/manifest.py`：审计模型和截止时间过滤。
- `backend/app/data_ingestion/providers/base.py`：provider 协议。
- `backend/app/data_ingestion/storage.py`：原始文件和 manifest 保存。
- `backend/tests/`：7 项现有测试。

## 3. 在新设备运行

准备 Git、uv 和 Python 3.13+，配置能够访问该 GitHub 仓库的身份。无数据源凭证也可以启动当前骨架和运行测试。

以下命令用于全新目录，PowerShell 和常见终端均可逐条执行：

```text
git clone --branch master https://github.com/oneothebrave/CapitalA.git
cd CapitalA/backend
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked uvicorn app.main:app --reload
```

服务默认地址为 `http://127.0.0.1:8000`，API 文档为 `http://127.0.0.1:8000/docs`。若端口占用，可在启动命令末尾加 `--port 8001`。

| 检查 | 预期结果 |
| --- | --- |
| `GET /api/v1/health` | HTTP 200，`{"status":"ok","service":"us-stock-quant-research"}` |
| `GET /api/v1/stocks/NVDA/analysis` | HTTP 501，`status` 为 `not_implemented` |
| pytest | 当前 7 项测试通过 |
| Ruff | `All checks passed!` |

应用默认标题为 `CapitalA`。健康检查中的 service 字符串仍是 `us-stock-quant-research`，这是现有响应值。

## 4. 配置和迁移数据

从 `backend/` 启动：配置读取当前工作目录的 `.env` 及 `QUANT_` 前缀环境变量。`.env` 非必需；需要自定义时参考 `backend/.env.example`，该示例的应用名称会覆盖代码默认标题。

默认数据目录按代码位置解析到仓库根目录下的 `data/`，可通过 `QUANT_DATA_DIR` 设置为绝对路径。原始文件保存在 `data/raw/`，manifest 按需生成在 `data/manifests/ingestion_runs/`。

截至本次交接，仓库默认 `data/` 下仅有 4 个 `.gitkeep`，没有实际采集数据；`backend/` 只有 `.env.example`，没有本地 `.env`。检查范围不包含仓库以外的自定义数据目录。

迁移原则：

- 在新设备按锁文件重建 `.venv`，不迁移虚拟环境、uv 缓存或测试缓存。
- `.env`、凭证和生成数据不进入 Git；将来如有真实数据，要将原始文件和 manifest 配套迁移。
- 目前 `raw_storage_path` 写入的是机器本地路径；换目录或换系统后，旧 manifest 需要核对或重定位。代码尚无自动路径迁移工具。
- 根目录的 `scripts/` 和 `notebooks/` 是本机空目录，Git 不跟踪，克隆后不会出现；需要时再建立。
- 当前未配置 CI、Docker 或部署脚本。运行验证需要在新设备本地执行。

## 5. 必须延续的决策

- 第一版只支持美股 ticker；不解析自然语言公司名、人物、产品或主题，不做全市场新闻发现。
- 采用模块化单体；采集、标准化、特征、评分、回测和报告分层。
- 优先使用可解释规则评分，权重是待验证假设。
- 原始数据保留，结果可重算，结论可追溯。
- 回测依据真实可用时间；区分发布、采集和策略可使用时间，不使用后来修订的数据冒充历史输入。
- 骨架使用文件系统；PostgreSQL、DuckDB 和前端/CLI 尚未定案。
- AI 仅用于结构化事件分析和报告表达。TypeSafe AI / Jev 是候选事件分类器，正式接入前需历史样本评测、概率校准和基线对照；没有安装 SDK 或接入 API。
- Agent 模拟研究实验已写入长期规划，不属于第一版 MVP。

## 6. 下一步工作

下一步是 ticker 注册表，尚无已批准的详细实现方案。用户此前要求开发前先规划，不确定事项先确认；本次交接不代表已确认数据供应商或注册表细节。

建议先明确并记录以下范围：

1. 注册表的最小字段：ticker、稳定证券 ID、交易所、公司名、CIK、证券类型、上市状态和历史有效期。
2. SEC ticker/CIK 映射及交易所证券目录的来源、关联规则和更新方式；区分个股分析标的与 SPY/QQQ 等基准 ETF。
3. ticker 格式、类别股表示、无效/退市代码和无法获得 CIK 的处理方式。
4. 文件系统中的注册表快照与来源审计格式。

确认后复用已有采集契约，实现注册表及必要的基础映射采集，增加离线 fixture 测试。实际 provider 接入前需要确定超时、限流、重试和可用时间规则。

后续主顺序为：行情及公司行动 → SEC filings / fundamentals → ticker 绑定新闻 → 标准化与特征 → 简单评分 → 单股报告 → 单股回测。详细路线以架构文档为准。

## 7. 未定选型

- 行情与公司行动数据供应商、历史覆盖和复权方式。
- 新闻数据供应商及使用范围。
- 是否接入 OpenAI API、TypeSafe AI / Jev，使用哪个模型和评测门槛。
- 后续数据库使用 DuckDB、PostgreSQL 或两者结合。
- 主要入口采用 CLI、前端或两者结合。
- 报告输出格式、默认回测周期、执行价格、成本和滑点参数。
- Agent 实验的观察周期与权重更新规则，留待后续阶段。

## 8. 已知限制与验证边界

- `available_artifacts()` 必须由调用方显式执行；填写请求截止时间不会自动过滤，保存原始数据也不会拒绝截止时间之后的材料。
- `available_at` 未传入时使用采集时间；各真实来源的可用时间推导及版本管理尚未实现。
- 模型预留了来源时间和记录 ID，但存储函数尚未完整传递所有这些字段。
- hash 用于审计，尚无自动去重、失败重试、限流或增量同步。
- `finish()` 无错误时可把空任务标为成功，真实 job 必须增加覆盖检查；同一 run id 的 manifest 重写会覆盖旧文件。
- 存储路径参数尚无完整输入校验；正式接入用户或供应商参数前需补充。
- `httpx` 当前属于开发依赖，若 provider 使用它，要明确加入运行依赖。
- 当前测试只覆盖离线存储、manifest、时区/截止时间及健康检查，不能证明真实数据源可用或回测无未来函数。

2026-10-12 在原设备核实：`uv sync --locked` 成功；Python 3.13.12、uv 0.11.7；pytest 7 passed，Ruff 通过。使用 TestClient 另行确认健康接口返回 200、股票分析占位接口返回 501。pytest 有 1 条来自 Starlette TestClient 的 `httpx` 弃用警告，不影响测试结果，可在后续依赖维护时处理。

## 9. 本次文档清理

删除 `docs/data-ingestion-minimal-skeleton.md`。其有效契约说明已合并到数据采集层文档第 11 节；其中“新增 jobs 目录并优先接 SEC job”的旧计划与当前目录及开发优先级不一致。

保留需求架构、数据采集层设计、根 README、后端 README 和 AGENTS.md，各自承担范围设计、详细契约、入口、运行说明和开发约束。修正数据库/前端已选定的过时表述及采集层直接计算事件特征的职责混淆。补充 manifest 运行产物的 Git 忽略规则。
