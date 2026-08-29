# 美股量化研究系统第一版需求与架构文档

## 1. 项目定位

本项目的目标是构建一个面向美股的量化研究与智能研判系统。

系统不直接承诺预测股价涨跌，也不定位为自动交易机器人。第一阶段目标是对指定股票进行结构化研究，结合行情、财报、SEC 公告、新闻等数据，生成可解释、可回测、可追溯的定性判断。

核心产出包括：

- 趋势评分
- 新闻/公告事件评分
- 基本面评分
- 风险评分
- 综合判断报告
- 回测验证结果

系统原则：

- 没有数据，不输出强结论
- 所有结论必须能追溯到数据和特征
- 大模型用于信息抽取和报告表达，不直接凭空给交易判断
- 回测结果用于验证历史有效性，不代表未来收益保证

## 2. 第一版市场选择

第一版先做美股。

选择美股的原因：

- SEC EDGAR 披露体系标准化，适合结构化处理
- 财报、公告、新闻覆盖更完整
- 美股公司 ticker、CIK、财务 XBRL 数据映射相对清晰
- 更适合先验证研究框架和数据链路

A 股后续可以作为第二市场接入，但不放入第一版范围。A 股需要额外处理政策预期、题材轮动、涨跌停、T+1、龙虎榜、监管问询、游资风格等本土市场特征。

## 3. 第一版功能边界

第一版只支持股票代码输入。

支持：

```text
NVDA
AAPL
TSLA
MSFT
```

不支持：

```text
英伟达
Nvidia
Jensen Huang
Blackwell
AI 芯片
数据中心受益股
某个主题利好哪些股票
```

第一版不做泛化实体识别，也不做主题到股票的自动映射。

但系统内部仍需要维护最小股票注册表，用于数据获取和标准化：

```text
ticker: NVDA
exchange: NASDAQ
company_name: NVIDIA Corporation
cik: 0001045810
sector: Technology
industry: Semiconductors
```

第一版新闻处理边界：

- 只抓与输入 ticker 明确绑定的新闻
- 只抓该公司 SEC filings
- 只处理该 ticker 相关财报、公告和公司新闻
- 不根据人物、产品、供应链、行业主题主动扩展股票范围
- 新闻源如果没有明确 ticker/company 关联，默认不进入主分析链路

## 4. 系统总流程

```text
用户输入 ticker
        ↓
股票注册表校验 ticker / CIK / 公司信息
        ↓
数据采集层
行情 / 财报 / SEC 公告 / 新闻 / 行业数据
        ↓
原始数据层
保存原始 JSON、HTML、文本、行情数据
        ↓
标准化数据层
统一 ticker、CIK、时间戳、币种、字段格式
        ↓
特征工程层
趋势、动量、波动、成交量、估值、财务、新闻情绪、事件类型
        ↓
研究与回测层
验证信号过去是否有效
        ↓
信号评分层
趋势分、新闻事件分、基本面分、风险分、综合分
        ↓
报告生成层
输出定性判断、依据、风险、置信度
```

## 5. 数据模式

系统需要支持三种数据模式。

### 5.1 严格数据模式

只使用用户提供的数据。

适合：

- 研究复现
- 回测验证
- 对固定样本做离线分析

优点：

- 可复现
- 边界清楚
- 成本低
- 适合调试

缺点：

- 数据可能过期
- 不能覆盖最新事件
- 数据缺失时结论受限

### 5.2 自动研究模式

用户只输入 ticker，系统主动获取公开数据后分析。

适合：

- 分析现实中的当前股票
- 每日自动更新
- 构建长期研究平台

系统需要自动获取：

- 最新股价与历史行情
- 成交量与波动数据
- SEC 公告
- 财报数据
- 相关新闻
- 行业与指数表现

### 5.3 混合模式

用户数据为主，外部数据用于补充和校验。

适合：

- 用户已有专有数据
- 需要用公开数据补齐新闻、公告、行情
- 研究报告需要引用最新信息

## 6. 新闻时间跨度与权重

新闻不应只设置一个统一时间窗口。应按研究周期分层处理。

### 6.1 新闻时间层级

```text
长期背景层：6-24 个月
中期趋势层：1-3 个月
短期催化层：1-10 天
盘中事件层：当天/小时级
```

长期背景层用于识别行业趋势和公司长期逻辑，例如 AI 基础设施需求、数据中心投资、电力需求、芯片供需变化等。

短期催化层用于捕捉近期价格波动触发因素，例如财报、评级调整、监管事件、重大订单、产品发布、诉讼、管理层变动等。

### 6.2 初始权重建议

短线判断，1-5 个交易日：

```text
近期新闻：50%
中期新闻/公告：25%
长期主题：25%
```

波段判断，1-4 周：

```text
近期新闻：30%
中期新闻/公告：40%
长期主题：30%
```

中期判断，1-6 个月：

```text
近期新闻：15%
中期新闻/公告：35%
长期主题：50%
```

这些权重只是初始假设，后续必须通过回测校准。

### 6.3 新闻评分公式

新闻影响分不应只看发布时间，也不应只做情绪分类。建议使用：

```text
新闻影响分 =
事件强度 × 来源可信度 × 新颖性 × 时间衰减 × 股票相关度
```

解释：

- 事件强度：财报、业绩指引、回购、并购、诉讼等强事件高于普通评论
- 来源可信度：公司公告、SEC、交易所、权威媒体高于社交媒体
- 新颖性：重复转载降权，首次披露升权
- 时间衰减：越近权重通常越高，但长期主题可保留慢衰减
- 股票相关度：第一版只接受明确绑定 ticker/company 的新闻

## 7. 数据采集层

模块建议：

```text
data_ingestion/
  market_data/
  sec_filings/
  fundamentals/
  news/
  reference_data/
```

### 7.1 market_data

职责：

- 获取美股历史日线行情
- 获取成交量
- 处理拆股、分红、复权
- 获取基准指数和行业 ETF 数据

第一版最低要求：

- 支持最近 1-5 年日线数据
- 支持 open、high、low、close、adjusted close、volume
- 支持 SPY / QQQ 作为基准

### 7.2 sec_filings

职责：

- 根据 CIK 获取 SEC filings
- 处理 10-K、10-Q、8-K
- 保存 filing 元数据和原文链接
- 提取 filing 发布时间、报告期、表单类型

SEC EDGAR 提供 submissions 和 XBRL company facts API，可作为第一版官方财报和公告数据源。

### 7.3 fundamentals

职责：

- 从 SEC XBRL 或数据供应商获取财务指标
- 标准化收入、利润、毛利率、经营现金流、负债、股本等字段
- 构建季度和年度财务时间序列

第一版重点指标：

- revenue
- gross profit
- operating income
- net income
- operating cash flow
- free cash flow
- total assets
- total liabilities
- shares outstanding

### 7.4 news

职责：

- 获取与 ticker 明确关联的新闻
- 保存标题、正文、来源、发布时间、URL
- 去重
- 标准化时区
- 提取摘要、情绪、事件类型、影响方向

第一版不做：

- 全市场新闻扫描
- 主题到股票映射
- 人物到股票映射
- 产品到股票映射
- 社交媒体情绪扫描

### 7.5 reference_data

职责：

- 维护 ticker、CIK、交易所、公司名称、行业等基础映射
- 为数据采集提供标准标识

第一版可以先使用本地表或轻量数据库表。

## 8. 数据存储层

建议第一版采用：

```text
PostgreSQL：结构化主库
DuckDB：本地研究、批量分析、回测加速
文件系统：保存原始 JSON、HTML、新闻正文、报告
```

数据分层：

```text
raw_data：
原始 JSON、HTML、新闻正文、公告原文，不覆盖

normalized_data：
清洗后的行情、财报、新闻、公告

feature_store：
每天每只股票的特征快照

research_results：
回测结果、实验参数、模型版本

reports：
生成过的分析报告
```

设计要求：

- 原始数据必须保留
- 标准化结果可以重算
- 特征必须带计算日期和数据截止时间
- 回测必须记录参数和代码版本
- 报告必须能追溯到使用的数据快照

## 9. 标准化与时间对齐

这是量化系统最容易出错的部分。

必须统一：

- ticker
- CIK
- 交易日历
- 时区
- 财报发布时间
- 新闻发布时间
- 行情复权方式
- 数据可见时间

第一版必须避免未来函数。

示例：

```text
如果系统在 2024-05-01 收盘后生成信号，
只能使用 2024-05-01 当时已经公开的数据。
不能使用之后修正的财报、之后发布的新闻、之后确认的趋势。
```

每条数据至少应记录：

```text
event_time：事件发生时间
published_at：公开发布时间
ingested_at：系统采集时间
available_at：策略可使用时间
```

回测时必须使用 `available_at` 判断数据是否可用。

## 10. 特征工程层

模块建议：

```text
features/
  price_features.py
  volume_features.py
  fundamental_features.py
  filing_features.py
  news_features.py
  risk_features.py
```

### 10.1 价格特征

- 1 日、5 日、20 日、60 日收益率
- 均线位置
- 均线斜率
- 新高/新低
- 最大回撤
- 相对 SPY / QQQ 强弱

### 10.2 量能特征

- 成交量相对 20 日均值
- 放量上涨
- 放量下跌
- 缩量回调
- 异常成交量

### 10.3 基本面特征

- 收入同比/环比增长
- 利润同比/环比增长
- 毛利率变化
- 经营现金流变化
- 负债率变化
- 每股指标变化

### 10.4 估值特征

- PE
- PS
- EV/EBITDA
- 估值历史分位
- 与同行估值比较

第一版如果估值数据源不足，可以先弱化估值特征。

### 10.5 新闻/公告特征

新闻不只做情绪，要提取事件。

事件类型示例：

- earnings_result
- guidance_update
- analyst_rating
- product_launch
- major_contract
- regulation
- lawsuit
- management_change
- merger_acquisition
- buyback
- dividend

每条新闻或公告输出：

```text
sentiment: positive / neutral / negative
event_type: earnings_result
impact_horizon: short / medium / long
impact_direction: positive / neutral / negative
importance: 0-100
confidence: 0-100
evidence: 摘要证据
```

### 10.6 风险特征

- 财报日临近
- 波动率异常
- 估值过高
- 新闻负面集中
- 监管/诉讼事件
- 价格远离均线
- 大盘风险上升

## 11. 回测系统

回测系统不是预测系统，而是验证系统。

它回答：

```text
如果这套信号规则在历史上真实运行，会表现如何？
```

必须模拟：

- 当时可见的数据
- 信号生成
- 买卖规则
- 交易价格
- 手续费
- 滑点
- 仓位限制
- 调仓周期
- 现金变化
- 持仓变化

第一版回测要求：

- 支持单只股票
- 支持日线级别
- 支持固定规则信号
- 支持买入、卖出、空仓
- 支持交易成本参数
- 输出交易明细
- 输出绩效指标

核心指标：

- 总收益
- 年化收益
- 最大回撤
- 波动率
- Sharpe Ratio
- 胜率
- 盈亏比
- 交易次数
- 换手率
- 与 SPY / QQQ 的相对收益

回测必须记录：

```text
strategy_name
strategy_version
feature_snapshot
start_date
end_date
universe
transaction_cost
slippage
benchmark
code_version
created_at
```

## 12. 信号评分层

第一版使用可解释多因子评分，不优先使用复杂深度学习模型。

建议评分项：

```text
trend_score
momentum_score
volume_score
fundamental_score
valuation_score
news_score
event_score
risk_score
composite_score
```

初始综合分可以使用规则权重：

```text
composite_score =
trend_score × 25%
+ fundamental_score × 20%
+ news_event_score × 20%
+ industry_score × 15%
+ valuation_score × 10%
- risk_penalty × 10%
```

注意：

- 第一版权重是研究假设
- 权重必须允许配置
- 权重必须通过回测校准
- 报告中必须说明信号强弱和风险来源

## 13. 报告生成层

报告生成层可以使用 LLM，但必须基于结构化输入。

LLM 输入：

- ticker
- 公司基础信息
- 行情特征
- 财务特征
- 新闻/公告摘要
- 评分结果
- 回测统计
- 风险标签

LLM 输出：

- 综合判断
- 核心依据
- 行情与技术面
- 基本面与估值
- 新闻/公告影响
- 行业与宏观背景
- 风险因素
- 未来观察点
- 置信度

报告要求：

- 不得编造数据
- 不得输出无依据强结论
- 必须区分事实、推断和假设
- 必须说明数据截止时间
- 必须说明主要风险
- 必须说明结论推翻条件

## 14. 推荐开发架构

第一版建议采用模块化单体，不建议一开始拆微服务。

建议目录结构：

```text
backend/
  app/
    api/
    core/
    data_ingestion/
      market_data/
      sec_filings/
      fundamentals/
      news/
      reference_data/
    normalization/
    features/
    scoring/
    backtesting/
    reports/
    jobs/
    storage/
  tests/
  scripts/
  notebooks/
frontend/
  src/
docs/
```

推荐技术栈：

```text
Python：数据处理、特征工程、回测、NLP
FastAPI：后端 API
PostgreSQL：结构化主库
DuckDB：本地研究和批量分析
Pandas / Polars：数据处理
SQLAlchemy：数据库访问
React / Next.js：前端
APScheduler / Prefect / Dagster：任务调度
```

MVP 可以更简单：

```text
Python + FastAPI + DuckDB + 文件系统 + 简单前端
```

数据库和外部服务可以逐步增强，不应在第一版过早复杂化。

当前骨架阶段已确认：

- 包管理工具使用 `uv`
- 后端框架使用 `FastAPI`
- 暂不接 PostgreSQL
- 暂不接 DuckDB，只预留后续接入空间
- 先使用文件系统目录保存原始数据、标准化数据、特征结果和报告
- 暂不创建 `frontend/`
- 后续再决定主要交互入口是前端、CLI，还是两者结合
- 初始化 git 仓库

## 15. 第一版最小闭环

输入：

```text
一个美股 ticker，例如 NVDA
```

系统自动获取：

- 最近 1-5 年日线行情
- 最近财报数据
- 最近 SEC filings
- 最近 30-90 天 ticker 绑定新闻
- SPY / QQQ 基准表现

系统计算：

- 价格趋势特征
- 量能特征
- 财务变化特征
- 新闻/公告事件特征
- 风险特征

系统输出：

- 趋势评分
- 新闻/公告评分
- 基本面评分
- 风险评分
- 综合评分
- 单股研究报告
- 简单回测结果

## 16. 后续阶段规划

### 16.1 第二阶段

- 支持股票池
- 支持行业对比
- 支持 watchlist
- 支持每日自动更新
- 支持评分历史追踪
- 支持报告历史归档
- 预留 agent 模拟研究实验的账户、持仓、交易和绩效记录结构

### 16.2 第三阶段

- 支持主题识别
- 支持公司别名识别
- 支持人物、产品、供应链映射
- 支持新闻优先扫描
- 支持主题到受益/受损股票映射
- 支持多 agent 因子权重对照实验

### 16.3 第四阶段

- 支持机器学习模型
- 支持滚动训练
- 支持样本外验证
- 支持组合回测
- 支持模拟盘
- 支持基于 walk-forward 和模拟盘复盘的权重更新机制

## 17. Agent 模拟研究实验系统

该功能来自后续扩展想法，不属于第一版 MVP 的必要范围。

### 17.1 功能定位

Agent 模拟研究实验系统用于比较不同因子权重和交易规则在模拟环境中的表现。

它不是自动交易系统，也不能用“一周盈利”直接证明某个股票分析结论正确。更合理的定位是：

```text
用可审计的模拟账户、交易记录和复盘流程，
观察不同权重配置在不同市场状态下的风险调整后表现，
再决定是否需要调整因子权重假设。
```

该系统应服务于研究验证，而不是直接输出收益承诺。

### 17.2 基本想法

系统允许创建若干个 agent。每个 agent 分配：

- 相同数量的少量股票，例如每个 agent 2 只。
- 相同起始资金，例如 10,000 美元或 10,000 元等指定币种。
- 一套明确的因子权重配置。
- 一套明确的交易约束。
- 一个固定观察周期。

每个 agent 基于系统已有数据、特征和评分进行模拟交易，记录买入、卖出、持仓、现金和净值变化。观察期结束后，系统比较不同 agent 的表现，并生成复盘材料。

### 17.3 必须修正的关键假设

原始想法中“盈利说明分析正确，亏损说明权重错误”过于简化。专业实现时必须修正为：

- 盈利不一定说明分析正确，可能只是大盘上涨或短期噪声。
- 亏损不一定说明权重错误，可能是市场整体下跌、事件尚未兑现或持有周期过短。
- 一周样本太短，只能作为短期行为观察，不能作为大幅调权依据。
- 少量股票样本容易受个股偶然事件影响，不能直接推导稳定规律。
- agent 如果完全自由买卖，会导致结果不可解释，必须记录完整决策链。

因此，评估必须使用：

- 相对 SPY / QQQ 的超额收益。
- 风险调整后收益。
- 最大回撤。
- 波动率。
- 换手率。
- 交易次数。
- 胜率和盈亏比。
- 持仓集中度。
- 决策是否遵守当时可见数据的 `available_at` 约束。

### 17.4 Agent 类型建议

早期不建议让 agent 自由生成完全不同策略。更可控的方式是让 agent 使用同一套评分框架，但采用不同权重。

示例：

```text
Agent A：趋势权重高
Agent B：基本面权重高
Agent C：新闻/公告事件权重高
Agent D：风险控制权重高
Agent E：均衡权重
```

这样可以把实验问题收敛为：

```text
在同一批股票、同一数据可见性、同一交易成本和同一执行规则下，
哪一类因子权重表现更稳定？
```

### 17.5 标准实验流程

推荐流程：

```text
1. 选择股票池和观察周期。
2. 为每个 agent 分配相同数量股票和相同起始资金。
3. 固定每个 agent 的因子权重、调仓频率和交易约束。
4. 每个交易日或指定周期生成特征快照。
5. agent 基于当时 available_at 之前可见的数据生成交易决策。
6. 模拟撮合成交，记录手续费、滑点、成交价格和现金变化。
7. 每次交易保存决策依据、使用的数据快照和评分明细。
8. 观察期结束后计算绝对收益、超额收益和风险指标。
9. 复盘表现差异，判断是否需要调整权重假设。
10. 权重调整必须进入新一轮样本外验证，不能直接覆盖历史最优结果。
```

### 17.6 必须记录的数据

每个 agent 需要记录：

```text
agent_id
agent_name
strategy_version
factor_weights
assigned_tickers
initial_cash
cash
positions
portfolio_value
benchmark
created_at
```

每次决策需要记录：

```text
decision_id
agent_id
ticker
decision_time
data_cutoff_time
feature_snapshot_id
score_breakdown
action
target_position
reason
confidence
```

每次模拟交易需要记录：

```text
order_id
agent_id
ticker
side
quantity
submitted_at
filled_at
fill_price
commission
slippage
cash_before
cash_after
position_after
```

每次评估需要记录：

```text
evaluation_id
agent_id
period_start
period_end
absolute_return
benchmark_return
excess_return
max_drawdown
volatility
sharpe_ratio
win_rate
turnover
trade_count
created_at
```

### 17.7 权重更新原则

权重调整不能只看单周盈亏。建议遵守：

- 短期模拟结果只用于观察，不用于大幅调权。
- 至少结合多个历史 walk-forward 窗口。
- 调整后的权重必须在样本外周期验证。
- 不允许把历史最优参数直接作为未来默认参数。
- 权重更新要记录旧权重、新权重、调整原因和验证窗口。
- 同一股票不一定存在长期固定最优权重，应考虑市场状态变化。

更合理的目标不是寻找“某只股票永远最佳的权重”，而是寻找：

```text
在某种市场状态和数据条件下，
某类因子权重是否更有效。
```

例如：

- 财报前后，新闻/公告事件权重可能更高。
- 趋势行情中，价格动量权重可能更高。
- 基本面拐点阶段，财务增长和指引变化权重可能更高。
- 高波动下跌阶段，风险控制权重可能更高。

### 17.8 建议模块

后续可增加：

```text
agent_simulation/
  agents.py
  strategy_profiles.py
  portfolio_accounting.py
  simulated_orders.py
  execution.py
  performance.py
  weight_review.py
```

职责：

- `agents.py`：定义 agent、分配股票和资金。
- `strategy_profiles.py`：定义不同因子权重配置。
- `portfolio_accounting.py`：维护现金、持仓和净值。
- `simulated_orders.py`：记录模拟订单。
- `execution.py`：模拟成交、手续费和滑点。
- `performance.py`：计算收益、回撤、波动、超额收益等指标。
- `weight_review.py`：生成复盘结论和权重调整建议。

### 17.9 风险与边界

- 模拟盘表现不代表未来实盘收益。
- 高频调权容易过拟合。
- 少量股票、短周期实验容易被噪声主导。
- agent 之间必须使用一致的数据可见性和交易成本假设。
- 所有 agent 决策必须能追溯到具体特征、评分规则和数据快照。
- LLM 可以用于复盘表达，但不能凭空决定权重调整。

## 18. 主要风险

### 18.1 数据风险

- 免费行情数据可能不稳定
- 新闻源可能缺失或重复
- 财报字段在不同公司间不完全一致
- 历史新闻时间戳可能不准确

### 18.2 研究风险

- 过拟合
- 未来函数
- 样本选择偏差
- 幸存者偏差
- 权重调参导致历史表现虚高
- 短周期 agent 模拟实验可能把随机波动误判为因子有效性

### 18.3 模型风险

- LLM 可能误读新闻
- 情绪分类不能等同于股价影响
- 事件影响方向可能依赖市场预期
- 报告表达可能显得过度确定

### 18.4 实盘风险

- 回测收益不代表未来收益
- agent 模拟盘收益不代表未来收益
- 交易成本和滑点会侵蚀收益
- 财报日和突发事件可能导致跳空
- 中国大陆用户交易美股还涉及合规、外汇、税务和券商限制

## 19. 第一版开发优先级

建议按以下顺序开发：

```text
1. 项目骨架
2. ticker 注册表
3. 行情数据采集
4. SEC filings / fundamentals 采集
5. ticker 绑定新闻采集
6. 数据标准化与存储
7. 价格和量能特征
8. 新闻/公告事件特征
9. 简单评分模型
10. 单股报告生成
11. 单股回测系统
12. API 和前端展示
```

优先级判断：

- 先保证数据链路正确
- 再做特征
- 再做评分
- 再做报告
- 最后优化模型

## 20. 当前明确决策

- 第一版做美股
- 第一版只支持 ticker 输入
- 第一版不做泛化实体识别
- 第一版不做新闻优先全市场扫描
- 第一版先做单股分析
- 第一版使用可解释规则评分
- 第一版必须包含回测验证
- 第一版使用模块化单体架构
- 第一版 LLM 只用于新闻/公告结构化和报告生成
- agent 模拟研究实验属于后续扩展，不进入第一版 MVP

## 21. 待确认问题

后续开发前需要继续确认：

- 第一版使用哪个行情数据源
- 新闻数据源选择免费源还是付费 API
- 是否需要接入 OpenAI API 做新闻结构化和报告生成
- 后续持久化数据库使用 DuckDB、PostgreSQL，还是两者结合
- 后续主要交互入口使用前端、CLI，还是两者结合
- 报告输出格式是 Markdown、HTML，还是前端页面
- 回测周期默认使用 1 年、3 年还是 5 年
- agent 模拟实验的默认观察周期、交易成本、滑点模型和权重更新规则
