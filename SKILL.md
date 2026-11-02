---
name: factory-channel-report
description: Use for generating a professional factory channel analysis report (渠道信息分析报告) from the HandaaS factory-channel MCP — covering 渠道分析（与同行对比）and 渠道/供应商搜索. Trigger when users ask for “渠道信息分析报告”, “渠道分析报告”, “查一家公司的渠道”, “渠道分析”, “供应商分析”, “渠道对比”, “渠道/供应商搜索”, or “企业渠道画像”. Infer the canonical enterprise name (auto-fuzzy-completing a keyword), pick the right MCP tools, and produce HTML + Markdown + JSON reports automatically. Also supports channel search mode (by keyword + address) independent of a specific enterprise. MCP 服务名称触发词：渠道资源管理。
---

# 渠道信息分析报告

## 用户契约

把“渠道信息分析报告”作为面向用户的调用短语。`factory-channel-report` 仅为内部包名。

当本 skill 处于激活状态：

1. 不要向用户索要 product_id、MCP 工具名、API 字段、内部参数或凭证信息；只接受企业名称、统一社会信用代码、注册号或企业 ID，或渠道检索关键词 / 地址。
2. 接受自然目标，例如“查一下某某公司的渠道”“分析这家企业的渠道结构”“给我一份某某公司的渠道对比报告”“按关键词搜一下供应商”。
3. 当用户只给企业关键词时，先调用关键词模糊查询；仅唯一候选或企业全称精确命中时继续。多候选必须返回 requires_confirmation 并停止主体分析。
4. 注册资本/营收分位仅描述上游同行序位，不解释为履约、抗风险、市场份额或销售网络；搜索记录未返回地址时不生成地域分布结论。
5. 企业主体与渠道搜索同时请求时按组合模式生成标题、摘要和口径；任一维度失败必须显式披露部分成功，不得退化为单一渠道检索或全空叙述。
6. 优先使用 MCP 连接（`FACTORY_CHANNEL_MCP_URL` Remote MCP 或本地 `handaas-mcp-server/factory-channel-mcp-server`）；不要让用户处理签名或凭证。
7. 同时产出 HTML（可分享交付）、Markdown（知识库 / wiki）、JSON（系统集成）三类产物。
8. 报告正文必须是专业研究报告风格：只见渠道事实与结构化数据，绝不出现工具名、入参、product_id、内部字段或空表。
9. 绝不打印 `secret_id`、`secret_key`、签名、token 或原始签名请求。
10. 默认 dry-run；真实付费 / 凭证调用需用户明确要求且 MCP 连接配置完整。
11. 数据为空时明确说明数据范围 / 口径，不渲染空表、不臆造事实。


- MCP 返回的嵌套 JSON 字符串（如金额 `{"coinType":"人民币","value":430000000.0}`、地址 `{"city":"杭州市",...}`）必须解析为可读文本（如"4.30 亿 人民币"、"浙江省杭州市"），绝不在报告正文、表格或指标中输出原始 JSON 字符串。
- 报告所有章节标题、指标卡标签必须用中文；`core_analysis.sections` 的 `title` 字段必须中文，不可显示英文 key（如 `holders`、`investments`）。
- 指标值必须可读化：金额格式为"X 亿/万 + 币种"，地址拼接省市区，比率显示百分号。详见 `references/report-output.md` 的「数据格式约束」。

## 付费调用纪律（先规划后查询）

每次真实调用均按接口/页计费，必须先规划再查询，不得默认全量拉取：

1. 每一次业务/工具调用、每一页都可能收费。想算 total / 页数不是无限制取全量的授权。
2. 调用前先推导：需要哪些结论、需要哪些数据维度、工具与参数计划、必要页数与最大调用预算。total 未知时，第一个必要的明细页同时完成 total 发现并直接作为报告数据，绝不为此多付一次（首屏响应必须复用，不重复拉取）。
3. 优先用统计 / 画像 / 聚合接口回答能回答的问题（企业渠道分析优先）；明细接口（渠道/供应商搜索）仅取结论、图表、代表性记录或用户明确的全量/计数需求所需的行数。只有用户明确要全面报告时才跑全面管线，绝不因为工具存在就全部调用。
4. 在 schema 允许范围内用合理的大 pageSize（≤50），取得所需证据 / 样本即停，且不超出显式预算。更多调用必须有"缺失结论"的正当理由，不能只为填满章节。不得用样本分布冒充全量结论。
5. 复用当前任务 / 报告内的相同请求（含首屏规划数据）；不要为渲染重跑 compose/MCP，用已保存 JSON 本地重渲染。不自动重试、不重复拉取同一统计或明细、不并行独立拉取相同数据。任何补充查询必须先列缺口并复用已返回记录。
6. `total_pages` / `remaining_pages` 是按请求 pageSize 的估算；短而非空页面仍有剩余记录时在预算内继续。只有稳定有效的 total 等于实际扫描条数才算完整采集；错误、提前空页、重复页、total 变化/缺失、数量溢出均视为不完整。显式预算 / 样本停止即部分采集，绝不宣称全量。
7. 预算不足以支撑用户要求的关键结论时：先说明证据缺口与预计需要追加的调用数，再请求扩大授权（提高 `--max-pages`）；不静默降级结论，也不擅自扩大计费范围。

分页收集默认一次明细调用预算 `--max-pages 1`（渠道/供应商搜索接口）；明细接口的 total、实际取数、完整性披露写入报告 `data_source.pagination`，报告级去重统计写入 `data_source.call_usage`。

## MCP 服务入口

- MCP 服务当前名称：渠道资源管理（连接仍使用原服务目录标识）。

- 上游 MCP 项目：`handaas-mcp-server/factory-channel-mcp-server`（位于 `HANDAAS_MCP_SERVER_ROOT` 或本仓库同级目录）。
- Remote MCP：设置环境变量 `FACTORY_CHANNEL_MCP_URL`（streamable-http），可选 `FACTORY_CHANNEL_MCP_TOKEN`。
- 本地 MCP：设置 `HANDAAS_MCP_SERVER_ROOT` 指向 `handaas-mcp-server` 仓库根目录；该 server 自己的 `.env` 提供 `INTEGRATOR_ID` / `SECRET_ID` / `SECRET_KEY`。
- 首次真实查询前，运行 `scripts/mcp_client.py ping` 与 `scripts/mcp_client.py list-tools` 验证连通。

## 按需加载 references

- 不清楚该 MCP 有哪些工具、参数、返回字段、何时调用：`references/mcp-tools-reference.md`。
- 报告结构、章节、质量底线、渲染工作流：`references/report-output.md`。

## 意图路由

| 用户意图 | 内部工作流 |
| --- | --- |
| 查一家公司的渠道结构 / 与同行对比 | 企业渠道分析模式；`compose_report.py --enterprise ...` |
| 按关键词搜渠道 / 供应商 | 渠道检索模式；`compose_report.py --search ...` |
| 按关键词 + 地址过滤搜渠道 | 渠道检索模式；`compose_report.py --search ... --address ...` |
| 组合（既看企业渠道又搜供应商） | `compose_report.py --enterprise ... --search ...` |
| 只给企业关键词（不是全称） | 先 `channel_insight_fuzzy_search` 补全全称，再查渠道分析 |
| 只要 JSON / 只要 HTML / 只要 Markdown | 用 `--output`（JSON）或 `--report-output`（HTML+MD），或 `render_report.py` 重渲染 |
| 连接 / 工具不存在 / 传参错误 | `mcp_client.py ping` / `list-tools` 排查；报脱敏后的缺失项 |

## Golden path for 渠道信息分析报告

1. **确定模式**：若用户提供企业主体走“企业渠道分析模式”；若提供检索关键词走“渠道检索模式”；两者也可组合。
2. **解析企业全称**（企业渠道分析模式）：若输入含“公司/集团/有限/院/厂/中心/事务所/合作社/合伙”等后缀视为全称；否则调 `channel_insight_fuzzy_search` 取首个命中。
3. **调用渠道工具**：`channel_insight_channel_analysis`（渠道分析，入参 `matchKeyword`（企业全称）+ `keywordType`，返回与同行对比）、`channel_insight_channel_search`（渠道/供应商搜索，入参 `matchKeyword` + 可选 `address` + `keywordType`，分页，默认 1 页预算；按 total 驱动、在 `--max-pages` 预算内翻页，超出预算披露未纳入条数而非宣称全量）。
4. **组装统一报告**：核心分析含渠道分析（KV）、渠道搜索明细（表）（按检索命中的维度呈现，空维度自动跳过）。
5. **渲染三件套**：`compose_report.py --enterprise ... --output ... --report-output ...` 直接产出 JSON + HTML + Markdown；或 `render_report.py --input ... --output ...` 重渲染。
6. **返回路径**：返回 JSON、HTML、Markdown 文件路径，以及企业全称映射与数据口径（含模式标注）。

## 脚本速查

```bash
# 校验连接配置（脱敏）
python scripts/validate_config.py --allow-placeholders

# 连通性自测
python scripts/mcp_client.py ping
python scripts/mcp_client.py list-tools

# 干跑（不调真实 API，用样例数据组装报告骨架）
python scripts/compose_report.py \
  --enterprise "示例科技有限公司" \
  --dry-run \
  --output output/channel.json \
  --report-output output/channel.html

# 企业渠道分析模式（真实查询）
python scripts/compose_report.py \
  --enterprise "示例科技有限公司" \
  --output output/channel.json \
  --report-output output/channel.html

# 渠道检索模式：按关键词 + 地址
python scripts/compose_report.py \
  --search "半导体" \
  --address "深圳" \
  --output output/channel_search.json \
  --report-output output/channel_search.html

# 明确授权扩大渠道搜索明细预算（先按 total 估算页数，确认必要后提高）
python scripts/compose_report.py \
  --search "半导体" \
  --max-pages 3 \
  --output output/channel_search.json

# 手动调单个工具
python scripts/mcp_client.py call-tool \
  --tool channel_insight_channel_analysis \
  --arguments-json '{"matchKeyword": "示例科技有限公司", "keywordType": "name"}'

# 重渲染已有 JSON
python scripts/render_report.py --input output/channel.json --output output/channel.html
python scripts/render_report.py --input output/channel.json --output output/channel.md
```

## 输出字段

- `subject`：企业全称、匹配关键词、主体类型、是否自动补全、是否渠道检索模式。
- `abstract` / `summary`：封面摘要与详细摘要。
- `metrics`：渠道总数、同行平均渠道数、渠道数量同行排名、供应商总数、覆盖区域数、渠道/供应商命中数等指标卡。
- `caliber`：匹配对象、匹配方式（含模式标注）、数据范围、产品、局限。
- `core_analysis`：渠道分析（KV）、渠道搜索明细（表）。
- `representative_records`：代表性渠道/供应商记录。
- `insights`：结构化解读（渠道规模 / 同行排名 / 渠道结构 / 渠道检索规模）。
- `data_source`：MCP server、数据产品、生成时间、是否 dry-run、模式（enterprise / channel_search）、渠道搜索分页披露（`pagination`）与调用复用统计（`call_usage`）。

若 API 调用失败，明确报出缺失的配置 / 缺失的工具 / MCP 错误 / 参数校验错误 / 上游网络错误，给出 dry-run 命令或配置步骤，绝不暴露密钥。
