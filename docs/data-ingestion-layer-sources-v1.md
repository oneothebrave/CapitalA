# 数据采集层信息媒介设计 v1

维护日期：2026-10-12。本文同时记录采集层目标设计和当前已实现的通用契约；未实现项不得视为现有功能。项目进度见 [HANDOFF.md](../HANDOFF.md)。

## 1. 目的

本文档定义第一版数据采集层的信息来源、获取媒介、数据对象、优先级和工程契约。

第一版系统目标是：用户输入一个美股 ticker，系统基于行情、SEC 公告、财报、新闻等数据，生成可解释、可回测、可追溯的单股研究结论。

因此，数据采集层的核心职责不是做投资判断，而是稳定、可追溯、按真实可用时间保存原始信息，为后续标准化、特征工程、评分、回测和报告生成提供可信输入。

## 2. 设计依据

采集层遵守以下要求。

### 2.1 区分“信息媒介”“数据对象”“供应商”

以下三类概念应分别建模：

- 信息媒介：API、批量文件、RSS、网页、SEC EDGAR、交易所目录、公司 IR 页面等。
- 数据对象：ticker、OHLCV、10-K、10-Q、新闻、公司行动、基准指数等。
- 数据供应商：行情 API、新闻 API、基本面数据商等。

数据采集层按“权威来源 + 获取媒介 + 数据对象 + 第一版优先级”组织，不先锁定具体商业供应商。

### 2.2 强化 point-in-time 约束

所有会进入回测或评分的数据，必须记录策略真实可用时间。尤其是：

- SEC 文件不能只用 `filing_date`，还要记录 SEC 接收/发布相关时间。
- 新闻不能只用网页展示时间，还要记录采集时间和策略允许使用时间。
- 财务数据不能只使用“最新聚合值”，回测时必须能回到当时可见的 filing 和 XBRL 事实。
- 公司行动必须记录 announcement date、ex-date、effective date 等不同时间语义。

### 2.3 公司行动应前置为核心数据

复权、拆股、分红、ticker 变更会直接影响行情连续性、收益计算和回测可信度。

公司行动应与行情数据一起作为第一版核心采集对象。

### 2.4 SEC company facts 不能替代原始 filing

SEC company facts 很适合作为结构化入口，但它是聚合后的 XBRL 事实视图。对回测来说，仅依赖聚合数据容易产生“后来修正的数据被历史使用”的风险。

要求：

- 原始 10-K、10-Q、8-K、XBRL/inline XBRL 必须保存。
- `companyfacts` 可以用于快速提取和校验。
- 回测和特征生成应能追溯到具体 `accession_number`、form type、period end、accepted time 和原始 filing。

### 2.5 新闻采集必须限定为 ticker 绑定

第一版不做全市场新闻扫描，也不做“新闻先行反推股票”。

要求：

- 新闻入口必须从已注册 ticker 出发。
- 每条新闻必须记录 ticker 绑定方式和置信度。
- 对转载、聚合、通讯社同步稿要做去重标识。
- 社交媒体、论坛、长尾网页暂不进入第一版核心范围。

### 2.6 OpenAI API 不是第一版采集媒介

如果后续接入 OpenAI API，它应属于新闻结构化、事件抽取、报告生成或摘要表达能力，不是原始数据采集媒介。

在数据采集层只保存原始新闻、公告、财报材料；LLM 处理结果应放在 normalization、features 或 reports 层，并保留输入版本。TypeSafe AI / Jev 同样属于候选事件分类器，具体约束见架构文档第 10.5.1 节。

## 3. 数据采集层边界

### 3.1 采集层负责

- 从外部媒介拉取或接收原始数据。
- 保存原始响应、原始文件、下载元数据和采集日志。
- 记录数据来源、授权来源、请求参数、响应状态、payload hash。
- 记录 `published_at`、`ingested_at`、`available_at` 等时间字段。
- 建立 ticker、CIK、交易所、证券状态等基础映射。
- 为后续标准化层提供可重放的数据输入。

### 3.2 采集层不负责

- 不输出买入、卖出、持有等交易判断。
- 不计算最终因子和评分。
- 不生成投资报告。
- 不做新闻主题扩散和受益股挖掘。
- 不把 LLM 输出当作原始事实。
- 不在第一版支持自然语言股票名、人物、产品或产业链主题输入。

## 4. 第一版应接入的信息媒介

### 4.1 官方监管媒介：SEC EDGAR

用途：获取上市公司公告、财务披露、XBRL 财务事实、公司基本注册信息。

主要媒介：

- SEC EDGAR company submissions API。
- SEC XBRL company facts API。
- SEC XBRL company concept API。
- SEC EDGAR Archives 原始 filing 文件。
- SEC daily index / bulk data 文件。
- SEC 公司 filing RSS 订阅，作为增量发现机制。

主要数据对象：

- 10-K 年报。
- 10-Q 季报。
- 8-K 重大事件公告。
- S-1、S-3 等注册文件。
- DEF 14A 代理声明。
- Forms 3、4、5 内部人交易。
- 13F 机构持仓，第一版可延后。
- XBRL / inline XBRL 财务事实。
- 公司名称、CIK、ticker、交易所、SIC 等基础信息。

必须保存的字段：

- `cik`
- `ticker`
- `accession_number`
- `form_type`
- `filing_date`
- `report_date`
- `accepted_at` 或 SEC 可获得的接收/发布时间
- `ingested_at`
- `available_at`
- `source_url`
- `raw_storage_path`
- `payload_hash`

第一版优先级：必须。

设计注意：

- `filing_date` 不是唯一的可用时间。
- 结构化财务数据必须能追溯到具体 filing。
- 对 amended filing，例如 10-K/A、10-Q/A，需要单独记录修订关系。

### 4.2 交易所与证券目录媒介

用途：构建 ticker 注册表、过滤非股票标的、识别上市状态、处理 symbol change。

主要媒介：

- Nasdaq Trader symbol directory。
- Nasdaq listed securities 文件。
- Other exchange listed securities 文件。
- 交易所 daily list、adds/deletes、symbol change、security status 文件。
- NYSE / Nasdaq 交易日历与特殊交易日公告。

主要数据对象：

- ticker。
- security name。
- exchange。
- test issue 标识。
- ETF / fund / common stock 类型识别。
- listing status。
- symbol change。
- delisting。
- round lot。
- file creation time。

必须保存的字段：

- `symbol`
- `security_name`
- `exchange`
- `security_type`
- `is_test_issue`
- `is_etf_or_fund`
- `listing_status`
- `effective_date`
- `source_file_time`
- `ingested_at`
- `available_at`

第一版优先级：必须。

设计注意：

- 第一版只支持 ticker 输入，但 ticker 本身会变更，因此内部应预留稳定实体 ID。
- CUSIP 等字段可能存在授权限制，不应作为第一版必需字段。
- ticker 注册表应支持历史映射，而不是只保存当前 ticker。

### 4.3 行情数据媒介

用途：获取价格、成交量、复权价格，为特征工程和回测提供基础序列。

主要媒介：

- 行情数据商 REST API。
- 行情数据商批量文件，例如 CSV、Parquet、S3、FTP。
- 交易所官方历史数据或授权数据包。
- WebSocket 实时流，第一版一般不需要。

主要数据对象：

- 日线 open、high、low、close、volume。
- adjusted close 或完整复权因子。
- split、dividend、distribution。
- 交易日历。
- 基准 ETF 或指数价格。
- 分钟线，第一版可延后。

必须保存的字段：

- `ticker`
- `trade_date`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `adjusted_close` 或 `adjustment_factor`
- `source`
- `provider_symbol`
- `ingested_at`
- `available_at`
- `raw_storage_path`

第一版优先级：必须。

设计注意：

- 未最终确认行情数据源前，应抽象 provider 接口。
- 原始未复权价格和复权数据都要保留。
- 回测使用哪一种价格序列必须显式记录。
- 对盘前盘后、分钟线和盘口数据，第一版只预留接口，不强制接入。

### 4.4 公司行动媒介

用途：保证复权、收益计算、ticker 生命周期和回测结果可信。

主要媒介：

- 行情数据商 corporate actions API。
- 交易所公司行动公告。
- Nasdaq ex-date / symbol change / daily list。
- SEC 8-K 和其他公告。
- 公司 IR 新闻稿。

主要数据对象：

- stock split。
- reverse split。
- cash dividend。
- special dividend。
- spin-off。
- merger。
- ticker change。
- delisting。
- share class change。

必须保存的字段：

- `ticker`
- `event_type`
- `announcement_date`
- `ex_date`
- `record_date`
- `payment_date`
- `effective_date`
- `ratio`
- `cash_amount`
- `currency`
- `source`
- `ingested_at`
- `available_at`

第一版优先级：必须。

设计注意：

- 公司行动不是普通新闻，不能只以新闻文本形式保存。
- 复权逻辑应能追溯到每一个公司行动事件。
- symbol change 和 delisting 对 ticker 注册表有直接影响。

### 4.5 财务与基本面数据媒介

用途：提取收入、利润、现金流、资产负债、股本等基本面输入。

主要媒介：

- SEC XBRL / inline XBRL 原始 filing。
- SEC company facts API。
- SEC company concept API。
- 商业基本面数据商 API，作为后续可选补充。

主要数据对象：

- income statement。
- balance sheet。
- cash flow statement。
- revenue。
- gross profit。
- operating income。
- net income。
- EPS。
- shares outstanding。
- cash and equivalents。
- debt。
- operating cash flow。
- capex。
- free cash flow 所需原始项。

必须保存的字段：

- `cik`
- `ticker`
- `accession_number`
- `taxonomy`
- `concept`
- `unit`
- `value`
- `period_start`
- `period_end`
- `fy`
- `fp`
- `form_type`
- `filed_at`
- `accepted_at`
- `available_at`

第一版优先级：必须，但以 SEC 为主。

设计注意：

- TTM、YoY、QoQ、margin 等属于特征层，不应在采集层直接固化。
- 商业数据商的 normalized fundamentals 可以用于补充，但不应替代原始 SEC 证据链。
- segment revenue、geography revenue 等字段结构复杂，第一版可作为增强项。

### 4.6 公司 IR 媒介

用途：获取公司主动发布的财报材料和管理层说明。

主要媒介：

- 公司 Investor Relations 网站。
- 公司新闻稿页面。
- 公司 IR RSS，若存在。
- 8-K exhibits 中的 earnings release。
- Business Wire、PR Newswire、GlobeNewswire 等新闻稿分发渠道。

主要数据对象：

- earnings release。
- earnings presentation。
- shareholder letter。
- investor day presentation。
- guidance update。
- management prepared remarks。
- webcast / transcript，第一版可选。

必须保存的字段：

- `ticker`
- `company_name`
- `document_type`
- `title`
- `published_at`
- `source_url`
- `file_url`
- `file_type`
- `ingested_at`
- `available_at`
- `raw_storage_path`

第一版优先级：建议。

设计注意：

- 公司 IR 材料常常和 SEC 8-K 附件重复，需要去重。
- PDF、HTML、PPT 等原始文件应先保存，解析放到后续层。
- IR 页面结构差异大，不适合作为第一阶段唯一关键路径。

### 4.7 新闻与事件媒介

用途：获取 ticker 绑定的新闻、公告型事件和外部事件。

主要媒介：

- 授权新闻数据商 API。
- 财经新闻 RSS 或 API。
- 新闻稿分发平台。
- 公司 IR 新闻稿。
- SEC 8-K。

主要数据对象：

- company news。
- earnings news。
- M&A。
- litigation。
- management change。
- product launch。
- regulatory event。
- analyst rating change，第一版可选。
- guidance raise / cut。

必须保存的字段：

- `ticker`
- `provider_article_id`
- `title`
- `summary`
- `body` 或 `raw_text`
- `source`
- `source_url`
- `author`
- `published_at`
- `ingested_at`
- `available_at`
- `ticker_binding_method`
- `ticker_binding_confidence`
- `dedupe_key`
- `raw_storage_path`

第一版优先级：最小闭环需要 ticker 绑定新闻；具体供应商待定，来源不足时必须在报告中标明覆盖缺失。

设计注意：

- 第一版不做全市场新闻扫描。
- 不采集社交媒体、论坛和非授权网页作为核心信号。
- 转载稿需要去重，否则会夸大事件影响。
- 新闻标题和正文只是原始输入，情绪、事件分类、影响方向属于后续层。

### 4.8 市场基准与宏观媒介

用途：为单股研究提供市场背景、基准收益和风险环境。

主要媒介：

- 与股票行情相同的数据源，用于 SPY、QQQ、IWM、行业 ETF。
- 指数数据商，用于 S&P 500、Nasdaq Composite、Dow Jones 等。
- Cboe，用于 VIX 历史数据。
- FRED，用于利率、宏观经济时间序列。
- U.S. Treasury，用于国债收益率。

主要数据对象：

- SPY、QQQ、IWM 日线行情。
- 行业 ETF 日线行情。
- VIX。
- 10Y Treasury yield。
- Fed Funds Rate。
- CPI、PCE、unemployment 等宏观序列，第一版可选。

必须保存的字段：

- `series_id`
- `symbol`
- `date`
- `value`
- `source`
- `ingested_at`
- `available_at`
- `revision_time`，如果来源支持历史版本

第一版优先级：SPY / QQQ 必须，宏观数据可延后。

设计注意：

- 宏观数据经常修订，若用于回测，应优先考虑带 vintage 的数据源。
- 第一版单股系统不应被宏观数据库建设拖慢。

### 4.9 预期、日历和衍生研究媒介

用途：增强财报前后事件研究和市场预期对比。

主要媒介：

- earnings calendar 数据商。
- 公司 IR 日历。
- 交易所日历。
- 分析师预期数据商。

主要数据对象：

- earnings date。
- report time，盘前、盘后或盘中。
- consensus EPS。
- consensus revenue。
- analyst rating。
- price target。

第一版优先级：可选。

设计注意：

- 分析师预期和评级通常授权限制更强，不应作为第一版核心依赖。
- 财报日期对回测很有用，但可以先通过 SEC filing 和公司 IR 反推，再逐步引入专门日历源。

## 5. 第一版采集优先级

### 5.1 必须接入

1. ticker 注册表和 CIK 映射。
2. 交易所证券目录。
3. 日线 OHLCV。
4. 复权数据或复权因子。
5. 公司行动。
6. SEC submissions。
7. SEC 原始 filings。
8. SEC XBRL / company facts。
9. SPY / QQQ 基准行情。

### 5.2 新闻与增强来源

1. ticker 绑定新闻，属于第一版最小闭环，具体来源待定。
2. 公司 IR earnings release。
3. 8-K exhibits。
4. earnings presentation。
5. VIX。

### 5.3 可延后

1. earnings call transcript。
2. 分析师评级和目标价。
3. consensus estimates。
4. 分钟线。
5. 盘前盘后行情。
6. 宏观 vintage 数据。
7. 13F。

### 5.4 第一版暂不接入

1. 社交媒体。
2. Reddit、论坛、评论区。
3. 全市场新闻扫描。
4. 新闻主题反推股票。
5. 供应链图谱。
6. 人物、产品、主题映射。
7. 期权流和暗池数据。
8. 卫星、信用卡、招聘等另类数据。

## 6. 统一采集记录协议

以下是目标元数据协议，不代表每个字段已经实现。当前模型与存储函数的实际契约见第 11 节。

```text
source_type
source_name
provider
provider_dataset
provider_record_id
retrieval_method
request_url
request_params_hash
response_status
source_url
source_published_at
source_updated_at
accepted_at
ingested_at
available_at
as_of_date
ticker
cik
accession_number
raw_storage_path
payload_hash
schema_version
ingestion_job_id
license_scope
quality_flags
dedupe_key
```

核心时间字段定义：

- `published_at`：外部来源声称的信息发布时间。
- `accepted_at`：监管或交易所系统接收/发布该信息的时间，适用于 SEC 等媒介。
- `ingested_at`：本系统实际采集到数据的时间。
- `available_at`：策略、回测或评分允许使用该数据的最早时间。

原则：

- 如果不确定真实可用时间，`available_at` 应保守取晚。
- `available_at` 的推导规则必须版本化。
- 不允许后续层直接使用没有可用时间的数据进入回测。

## 7. 文件系统存储

当前采用文件系统。`RawStorage` 已实现下列动态目录规则；所有具体数据源仍待接入。

已实现的路径结构：

```text
data/
  raw/
    <source_type>/
      <provider_dataset>/
        <TICKER 或 CIK0000000000>/
          <UTC 时间>-<UUID>.<扩展名>
  manifests/
    ingestion_runs/
      <job_name>/
        <run_id>.json
  normalized/
  features/
  reports/
```

有 ticker 时按大写 ticker 分目录；没有 ticker 但有 CIK 时使用补齐十位的 CIK；二者均缺失时直接保存在 dataset 目录。目录按需创建，`source_name` 当前只写入元数据，不参与文件路径。

dataset 名称由后续 provider 定义，例如 `submissions`、`daily_bars`、`ticker_cik` 和 `articles`，目前还没有固定的全局 dataset 注册表。

原始文件及 manifest 均属于本地运行产物，不提交 Git。迁移真实数据时两者必须配套保留；当前 `raw_storage_path` 使用本地路径，跨设备需要核对或重定位。未来 `source_snapshots/` 等目录尚未实现。

后续每次真实采集任务应生成 manifest，目标记录包括：

- job name。
- job version。
- run id。
- start time。
- end time。
- input parameters。
- source snapshot。
- output file list。
- failed records。
- retry count。
- data quality warnings。

## 8. 数据源选择标准

具体供应商尚未确定。开发到相关模块前，应按以下标准评估并记录选择理由。

1. 是否允许商业或生产使用。
2. 是否支持历史数据。
3. 是否支持 point-in-time 或可构造 point-in-time。
4. 是否提供公司行动和复权因子。
5. 是否提供稳定的唯一 ID。
6. 是否提供增量同步能力。
7. 是否有明确 rate limit。
8. 是否允许缓存原始响应。
9. 是否有清晰 SLA。
10. 是否可被替换，避免业务逻辑绑定供应商私有字段。

## 9. 建议的工程实现顺序

1. 通用接口、原始数据落盘和 manifest 已完成，继续复用现有契约。
2. 实现 ticker 注册表采集任务。
3. 实现 SEC CIK/ticker 映射采集任务。
4. 实现交易所 symbol directory 采集任务。
5. 实现日线行情采集 provider 抽象。
6. 实现公司行动采集 provider 抽象。
7. 实现 SEC submissions 和 filing 下载任务。
8. 实现 SEC XBRL/company facts 采集任务。
9. 实现 SPY/QQQ 基准行情采集任务。
10. 实现 ticker 绑定新闻采集任务。
11. 实现公司 IR 材料采集任务。
12. 为每类采集任务补充重试、限流、去重、payload hash 和 manifest。

## 10. 官方参考媒介

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC data APIs](https://data.sec.gov/)
- [SEC Developer Resources](https://www.sec.gov/about/developer-resources)
- [Nasdaq Trader Symbol Directory Definitions](https://nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs)
- [Nasdaq Trader Symbol Lookup](https://nasdaqtrader.com/trader.aspx?id=symbollookup)
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/fred/)
- [Cboe VIX Historical Data](https://www.cboe.com/tradable_products/vix/vix_historical_data)

## 11. 当前已实现的最小采集契约

本节合并原 `data-ingestion-minimal-skeleton.md` 中仍有效的技术说明，以当前代码为准。

### 11.1 模型与接口

| 文件 | 已实现内容 |
| --- | --- |
| `backend/app/data_ingestion/manifest.py` | `IngestionRequest`、`RawArtifact`、`IngestionError`、`IngestionRunManifest` |
| `backend/app/data_ingestion/providers/base.py` | `IngestionProvider.fetch(request)` 同步协议及 `ProviderFetchResult` 响应封装 |
| `backend/app/data_ingestion/storage.py` | `RawStorage.save_raw_payload()` 及 `write_manifest()` |
| `backend/app/data_ingestion/__init__.py` | 对外导出上述模型和存储工具 |
| `backend/app/storage/file_store.py` | 通用文件路径及创建目录助手 |

`ProviderFetchResult` 包含原始 `payload`、`media_type`、`source_url`、`provider_record_id` 和 `metadata`。provider 仅负责取数据，存储函数负责落盘，manifest 负责审计；标准化、特征和评分由后续层处理。

### 11.2 原始文件与时间

`save_raw_payload()` 支持 bytes、字符串、字典和列表。bytes 直接保存，字符串使用 UTF-8，JSON 对象按固定键顺序序列化后保存；hash 是落盘内容的 SHA-256，不一定是供应商 HTTP 响应字节的 hash。必须保留原始响应字节时，应传入 bytes。

每次保存生成新的 UUID 文件名，返回 `RawArtifact`，包含来源、路径、hash、字节数、ticker/CIK、`ingested_at` 和 `available_at` 等字段。hash 已用于审计，但尚无自动去重或防重复下载逻辑。

未指定 `available_at` 时，存储函数保守使用本次 `ingested_at`。时间模型使用带时区类型，拒绝无时区时间；真实数据的 `available_at` 推导规则仍需在各 provider/任务中定义和版本化。

存储函数不会根据请求截止时间拒绝原始数据落盘。调用方必须显式使用 `manifest.available_artifacts(data_cutoff_at)`，筛选 `available_at <= data_cutoff_at` 的文件。仅在 `IngestionRequest` 中填写截止时间不会自动执行过滤。

### 11.3 Manifest 与任务编排

manifest 包含任务名称/版本、run id、请求、时间、原始文件列表、错误、警告和 metadata。`finish()` 可显式指定终态；未指定时，有文件及错误则为 `partial_success`，仅有错误则为 `failed`，无错误则为 `success`。空结果也可得到 `success`，真实任务需自行检测数据覆盖完整性。

`write_manifest()` 将审计记录写成 JSON；重复写同一 `run_id` 会覆盖该 manifest。原始文件保留与审计记录生命周期管理尚待真实任务设计。

后续任务应完成以下流程，目前没有实际执行这些步骤的 job：

```text
构造 IngestionRequest 和 IngestionRunManifest
        ↓
provider.fetch(request)
        ↓
RawStorage.save_raw_payload()
        ↓
manifest.add_artifact() / add_error()
        ↓
manifest.finish() → write_manifest()
        ↓
按可用时间筛选后交给 normalization 层
```

### 11.4 已有验证与待补充项

`backend/tests/test_data_ingestion_skeleton.py` 有 6 项离线测试，覆盖 JSON 落盘及 hash、manifest 序列化、成功/失败记录、截止时间过滤和无时区时间拒绝。另有 1 项 API 健康检查测试。真实网络采集没有测试，也没有实现。

接入真实 provider 前需要补充请求超时、限流、重试策略、数据完整性检测、来源时间传递，以及路径参数和落盘前的输入校验。`RawArtifact` 虽声明来源发布/修订/接收时间及记录 ID，当前存储函数未提供全部对应参数，不能宣称已完整传播这些字段。

`httpx` 当前只在开发依赖组；后续 provider 如果使用它，应明确声明为运行依赖。下一步实现 ticker 注册表和基础映射，不沿用旧文档中优先增加 SEC job 的过时安排。
