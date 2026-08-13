# MCP 工具参考 — factory-channel-mcp-server

本 skill 连接的 MCP server：`handaas-mcp-server/factory-channel-mcp-server`（“渠道信息分析洞察”）。

> **重要**：`channel_insight_channel_analysis` 入参为 `matchKeyword`（**企业全称** / 注册号 / 统一社会信用代码 / 企业 id）+ `keywordType`；当用户只给企业关键词时，必须先调关键词模糊查询补全全称。`channel_insight_channel_search` 属于渠道检索类工具，入参为渠道关键词。

## 通用约定

- `keywordType` 枚举：`name`（企业名称）/ `nameId`（企业 id）/ `regNumber`（注册号）/ `socialCreditCode`（统一社会信用代码）。
- 分页：`pageIndex` 从 1 开始；`pageSize` 单页最多 50。

---

## 工具清单

### 1. `channel_insight_channel_analysis` — 渠道分析（与同行对比）

用途：按企业主体返回渠道结构分析，并与同行对比。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | string | 是 | 企业名称 / 注册号 / 统一社会信用代码 / 企业 id |
| `keywordType` | string | 否 | 主体类型：name / nameId / regNumber / socialCreditCode |

返回：`channelCount`（渠道总数）、`peerAvgChannelCount`（同行平均渠道数）、`channelRank`（渠道数量同行排名）、`topChannelType`（主要渠道类型）、`supplierCount`（供应商总数）、`peerAvgSupplierCount`（同行平均供应商数）、`regionCount`（覆盖区域数）、`channelGrowthRate`（渠道增长率）、`updateTime`（数据更新时间）等。

product_id：`66f3d8bf64bd2be52d68a0fe`。

---

### 2. `channel_insight_fuzzy_search` — 关键词模糊查询企业

用途：根据企业名称 / 人名 / 品牌 / 产品 / 岗位等关键词模糊查询企业列表，用于补全企业全称。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | string | 是 | 匹配关键词 |
| `pageIndex` | int | 否 | 分页开始位置（默认 1） |
| `pageSize` | int | 否 | 单页最多 50 |

返回：`total` + 企业列表（`name`、`nameId`、`regCapitalValue`、`foundTime`、`operStatus`、`address`、`legalRepresentative`、`enterpriseType`、`catchReason` 命中原因等）。

product_id：`675cea1f0e009a9ea37edaa1`。

---

### 3. `channel_insight_channel_search` — 渠道/供应商搜索

用途：按渠道关键词 / 地址 / 主体类型查询渠道与供应商记录（渠道检索模式）。

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `matchKeyword` | string | 是 | 渠道/供应商关键词 |
| `address` | string | 否 | 地址过滤（可选） |
| `keywordType` | string | 否 | 主体类型：name / nameId / regNumber / socialCreditCode |
| `pageIndex` | int | 否 | 从 1 开始（默认 1） |
| `pageSize` | int | 否 | 单页最多 50（默认 10） |

返回（list + `total`）：`channelName`（渠道/供应商名称）、`channelType`（类型）、`region`（所在区域）、`address`（地址）、`contactPerson`（联系人）、`contactPhone`（联系电话）、`mainProduct`（主营产品）等。

product_id：`66b71b498dd25dbfbe8b0acd`。

---

## 推荐调用顺序（报告编排）

- **企业渠道分析模式**：
  1. （若仅有关键词）`channel_insight_fuzzy_search` → 取 `name` 作为全称。
  2. `channel_insight_channel_analysis` → 渠道结构分析 + 同行对比。
- **渠道检索模式**：
  1. `channel_insight_channel_search`（按 `matchKeyword` + 可选 `address`）→ 渠道/供应商明细。

> 两种模式可组合：同一份报告同时呈现企业渠道分析与渠道检索结果。
