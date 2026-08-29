# 数据采集层最小骨架技术说明

## 1. 背景

本文档说明第一版数据采集层的最小工程骨架。

该骨架的目标不是立即接入所有数据源，而是先建立统一的采集契约：

- 外部数据如何请求。
- 原始数据如何保存。
- 每次采集如何审计。
- 后续 SEC、行情、新闻、IR provider 如何接入。

第一版系统要求所有研究结论可解释、可回测、可追溯。因此，采集层必须优先保证原始数据和采集元数据可追踪，而不是直接生成投资判断。

## 2. 新增文件

### 2.1 `backend/app/data_ingestion/__init__.py`

作用：对外暴露数据采集层的核心模型和工具。

当前导出：

- `IngestionRequest`
- `RawArtifact`
- `IngestionError`
- `IngestionRunManifest`
- `RawStorage`
- `write_manifest`

后续其他模块可以从 `app.data_ingestion` 统一导入这些对象，避免依赖内部文件路径。

### 2.2 `backend/app/data_ingestion/manifest.py`

作用：定义采集审计 manifest 的 Pydantic 数据模型。

核心模型：

- `IngestionRequest`：描述一次外部请求的输入和来源信息。
- `RawArtifact`：描述一个已保存的原始文件或原始 payload。
- `IngestionError`：描述采集过程中的失败、异常和重试信息。
- `IngestionRunManifest`：描述一次采集任务的完整审计记录。

关键字段：

- `source_type`：数据来源类型，例如 `sec`、`market_data`、`news`。
- `source_name`：具体来源名称，例如 `sec_edgar`。
- `retrieval_method`：获取方式，例如 `api`、`bulk_file`、`rss`、`web_page`。
- `ingested_at`：系统实际采集到数据的时间。
- `available_at`：策略、回测或评分允许使用该数据的最早时间。
- `data_cutoff_at`：本次请求或回测允许看到的数据截止时间。
- `payload_hash`：原始内容的 SHA-256 hash，用于去重和审计。
- `raw_storage_path`：原始数据落盘位置。

### 2.3 `backend/app/data_ingestion/storage.py`

作用：提供文件系统存储能力。

当前包含：

- `RawStorage.save_raw_payload()`：保存 JSON、HTML、CSV、PDF、文本或 bytes 原始内容。
- `write_manifest()`：将一次采集任务的 manifest 写入 JSON 文件。

默认存储位置：

```text
data/
  raw/
  manifests/
    ingestion_runs/
```

保存原始数据时会自动：

- 序列化 payload。
- 计算 SHA-256 hash。
- 生成唯一文件名。
- 创建目录。
- 返回 `RawArtifact`。

`RawStorage.save_raw_payload()` 只负责保存原始数据，不按回测截止时间拒绝落盘。

后续特征生成、回测或研究任务需要通过 `manifest.available_artifacts(data_cutoff_at)` 筛选当时可见的数据：

```text
available_at <= data_cutoff_at
```

如果原始数据的 `available_at` 晚于本次请求允许看到的数据截止时间，可以被保存为原始数据，但不能进入那次回测或研究任务的可见数据集。

### 2.4 `backend/app/data_ingestion/providers/__init__.py`

作用：对外暴露 provider 相关接口。

当前导出：

- `IngestionProvider`
- `ProviderFetchResult`

### 2.5 `backend/app/data_ingestion/providers/base.py`

作用：定义所有外部数据 provider 的统一协议。

当前包含：

- `ProviderFetchResult`：provider 返回的原始响应封装。
- `IngestionProvider`：provider 协议接口。

后续 SEC、行情、新闻、IR 等具体 provider 都应实现：

```python
def fetch(self, request: IngestionRequest) -> ProviderFetchResult:
    ...
```


### 2.6 `backend/tests/test_data_ingestion_skeleton.py`

作用：验证最小骨架可以真实工作。

当前覆盖：

- `RawStorage.save_raw_payload()` 能保存 JSON 原始数据。
- 保存路径按 source、dataset、ticker 分层。
- `payload_hash` 与落盘文件内容一致。
- `manifest.available_artifacts(data_cutoff_at)` 能过滤晚于截止时间的数据。
- `IngestionRunManifest.finish()` 能正确结束任务。
- 失败任务能保存错误类型、重试标记和排查详情。
- `write_manifest()` 能写出可读取的 JSON 审计文件。

## 3. 模块职责划分

### 3.1 Provider

Provider 只负责“从外部媒介拿数据”。

例如：

- SEC provider 调用 `data.sec.gov`。
- 行情 provider 调用行情数据商 API。
- 新闻 provider 调用新闻 API。
- IR provider 下载公司 IR 页面或文件。

Provider 不负责：

- 标准化财务字段。
- 计算特征。
- 生成评分。
- 生成报告。

### 3.2 RawStorage

RawStorage 只负责“把原始数据保存下来”。

它不理解业务含义，不解析 10-K，也不解释新闻情绪。

### 3.3 Manifest

Manifest 负责“记录这次采集发生了什么”。

它是后续追溯、回测复现和数据质量排查的核心审计入口。

## 4. 标准采集流程

一次采集任务的推荐流程如下：

```text
1. Job 接收输入参数，例如 ticker=NVDA。
2. Job 构造 IngestionRequest。
3. Job 调用具体 provider.fetch(request)。
4. Provider 返回 ProviderFetchResult。
5. Job 调用 RawStorage.save_raw_payload() 保存原始 payload。
6. RawStorage 返回 RawArtifact。
7. Job 将 RawArtifact 加入 IngestionRunManifest。
8. Job 调用 manifest.finish() 标记成功、部分成功或失败。
9. Job 调用 write_manifest() 保存 manifest。
10. 后续 normalization 层读取 raw_storage_path 和 manifest 继续处理。
```

## 5. 示例代码

下面是一个最小任务的伪代码：

```python
from app.data_ingestion.manifest import IngestionError, IngestionRequest, IngestionRunManifest
from app.data_ingestion.storage import RawStorage, write_manifest


def ingest_sec_submissions(provider, ticker: str, cik: str):
    request = IngestionRequest(
        source_type="sec",
        source_name="sec_edgar",
        retrieval_method="api",
        url=f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json",
        ticker=ticker,
        cik=cik,
    )

    manifest = IngestionRunManifest(
        job_name="ingest_sec_submissions",
        source_type="sec",
        source_name="sec_edgar",
        request=request,
    )

    try:
        result = provider.fetch(request)
        artifact = RawStorage().save_raw_payload(
            source_type="sec",
            source_name="sec_edgar",
            provider_dataset="submissions",
            payload=result.payload,
            media_type=result.media_type,
            ticker=ticker,
            cik=cik,
            source_url=result.source_url,
            metadata=result.metadata,
        )
        manifest.add_artifact(artifact)
        manifest.finish()
    except Exception as exc:
        manifest.add_error(IngestionError(message=str(exc), retryable=True))
        manifest.finish("failed")

    write_manifest(manifest)
    return manifest
```

## 6. 后续实现顺序

建议下一步按以下顺序继续：

1. 增加一个 `jobs/` 目录，先实现 SEC submissions 采集任务。
2. 实现一个真实的 `SecProvider`。
3. 加入项目配置，例如 SEC User-Agent。
4. 增加单元测试，覆盖 manifest 序列化、raw payload 保存、hash 稳定性。
5. 再接入 ticker 注册表、交易所 symbol directory、日线行情和公司行动。

## 7. 设计约束

- 原始数据必须保留。
- 标准化数据和特征可以重算。
- `available_at` 缺失时必须保守处理。
- 后续层不得直接使用没有 manifest 的原始数据。
- Provider 可以替换，manifest 和 storage 契约应保持稳定。


