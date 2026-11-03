# 比亚迪企业规模同行基准

- 用户需求：请展示比亚迪股份有限公司在上游口径下的注册资本和营收同行基准，只报告实际返回的分位、排名、区间或同行总数；不要分析渠道结构。
- 决策用途：为企业规模定位提供同行比较字段。
- 本轮结果：**本轮检查通过**
- 实际工具调用：1；失败 0
- 章节覆盖率：100%（不代表证据质量）

## 预期业务检查（不自动宣称通过）

- channel_analysis 必须同时包含非空且非零的注册资本同行指标与营收同行指标
- 注册资本侧和营收侧各至少有一个实际分位或排名字段，并保留对应原始语义，不能改写为领先或市场份额
- 若展示同行总数或区间，必须来自 channel_analysis 实际字段而非推算
- 不得以企业名解析成功或参数回显替代资本与营收两组同行指标
- 报告标题和摘要必须明确是企业规模同行基准而非渠道结构

## 本轮自动检查发现


## 使用局限

- 同行口径由上游数据产品定义
- 规模字段不代表渠道能力、履约或市场份额

## 证据与复现

- [审计结果](result.json)
- [工具调用、结果形态与响应摘要哈希](calls.json)
- [JSON](report.json) / [HTML](report.html) / [Markdown](report.md)

```bash
python3 factory-channel-skill/scripts/compose_report.py --enterprise '比亚迪股份有限公司' --page-size 10 --output factory-channel-skill/output/09-byd-peer-scale-benchmark/report.json --report-output factory-channel-skill/output/09-byd-peer-scale-benchmark/report.html
```

## 逐场景业务复核

本轮真实产物的全部清单检查均有当前字段证据，且报告保留样本/缺失/关系边界。

- **pass** channel_analysis 必须同时包含非空且非零的注册资本同行指标与营收同行指标：channel_analysis实际返回：注册资本分位‘后0.02%（排名433897/433988）’、区间5000+、营收分位‘后1.4%（排名359192/364126）’、区间5000+；标题/摘要明确‘企业规模同行基准’，并否认渠道结构或市场份额含义。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_analysis","status":"data","rows":null,"total":null,"args":{"matchKeyword":"比亚迪股份有限公司","keywordType":"name"}}],"subject":{"enterprise":"比亚迪股份有限公司","matchKeyword":"比亚迪股份有限公司","keywordType":"name","match_raw":"比亚迪股份有限公司","resolved":true,"resolve_reason":"视为企业全称","search_mode":false,"mode":"enterprise","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"注册资本分位","value":"后 0.02%","hint":"注册资本在同行中的序位","delta":"排名 433897/433988"},{"label":"注册资本区间","value":"5000+","hint":"注册资本规模区间"},{"label":"营收分位","value":"后 1.4%","hint":"年营收在同行中的序位","delta":"排名 359192/364126"},{"label":"营收区间","value":"5000+","hint":"年营收规模区间"},{"label":"同行企业总数","value":"433988","hint":"行业同赛道企业总量"}],"core_counts":{"sections":1,"channel_search":0},"core_samples":{},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道分析"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道分析","product_id":"66f3d8bf64bd2be52d68a0fe"}],"limit":"企业分析实际为注册资本/营收同行基准，不等同于渠道结构；模糊名称存在多候选时必须确认主体后再调用。","html_bytes":1060321,"markdown_bytes":2498}
- **pass** 注册资本侧和营收侧各至少有一个实际分位或排名字段，并保留对应原始语义，不能改写为领先或市场份额：channel_analysis实际返回：注册资本分位‘后0.02%（排名433897/433988）’、区间5000+、营收分位‘后1.4%（排名359192/364126）’、区间5000+；标题/摘要明确‘企业规模同行基准’，并否认渠道结构或市场份额含义。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_analysis","status":"data","rows":null,"total":null,"args":{"matchKeyword":"比亚迪股份有限公司","keywordType":"name"}}],"subject":{"enterprise":"比亚迪股份有限公司","matchKeyword":"比亚迪股份有限公司","keywordType":"name","match_raw":"比亚迪股份有限公司","resolved":true,"resolve_reason":"视为企业全称","search_mode":false,"mode":"enterprise","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"注册资本分位","value":"后 0.02%","hint":"注册资本在同行中的序位","delta":"排名 433897/433988"},{"label":"注册资本区间","value":"5000+","hint":"注册资本规模区间"},{"label":"营收分位","value":"后 1.4%","hint":"年营收在同行中的序位","delta":"排名 359192/364126"},{"label":"营收区间","value":"5000+","hint":"年营收规模区间"},{"label":"同行企业总数","value":"433988","hint":"行业同赛道企业总量"}],"core_counts":{"sections":1,"channel_search":0},"core_samples":{},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道分析"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道分析","product_id":"66f3d8bf64bd2be52d68a0fe"}],"limit":"企业分析实际为注册资本/营收同行基准，不等同于渠道结构；模糊名称存在多候选时必须确认主体后再调用。","html_bytes":1060321,"markdown_bytes":2498}
- **pass** 若展示同行总数或区间，必须来自 channel_analysis 实际字段而非推算：channel_analysis实际返回：注册资本分位‘后0.02%（排名433897/433988）’、区间5000+、营收分位‘后1.4%（排名359192/364126）’、区间5000+；标题/摘要明确‘企业规模同行基准’，并否认渠道结构或市场份额含义。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_analysis","status":"data","rows":null,"total":null,"args":{"matchKeyword":"比亚迪股份有限公司","keywordType":"name"}}],"subject":{"enterprise":"比亚迪股份有限公司","matchKeyword":"比亚迪股份有限公司","keywordType":"name","match_raw":"比亚迪股份有限公司","resolved":true,"resolve_reason":"视为企业全称","search_mode":false,"mode":"enterprise","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"注册资本分位","value":"后 0.02%","hint":"注册资本在同行中的序位","delta":"排名 433897/433988"},{"label":"注册资本区间","value":"5000+","hint":"注册资本规模区间"},{"label":"营收分位","value":"后 1.4%","hint":"年营收在同行中的序位","delta":"排名 359192/364126"},{"label":"营收区间","value":"5000+","hint":"年营收规模区间"},{"label":"同行企业总数","value":"433988","hint":"行业同赛道企业总量"}],"core_counts":{"sections":1,"channel_search":0},"core_samples":{},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道分析"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道分析","product_id":"66f3d8bf64bd2be52d68a0fe"}],"limit":"企业分析实际为注册资本/营收同行基准，不等同于渠道结构；模糊名称存在多候选时必须确认主体后再调用。","html_bytes":1060321,"markdown_bytes":2498}
- **pass** 不得以企业名解析成功或参数回显替代资本与营收两组同行指标：channel_analysis实际返回：注册资本分位‘后0.02%（排名433897/433988）’、区间5000+、营收分位‘后1.4%（排名359192/364126）’、区间5000+；标题/摘要明确‘企业规模同行基准’，并否认渠道结构或市场份额含义。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_analysis","status":"data","rows":null,"total":null,"args":{"matchKeyword":"比亚迪股份有限公司","keywordType":"name"}}],"subject":{"enterprise":"比亚迪股份有限公司","matchKeyword":"比亚迪股份有限公司","keywordType":"name","match_raw":"比亚迪股份有限公司","resolved":true,"resolve_reason":"视为企业全称","search_mode":false,"mode":"enterprise","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"注册资本分位","value":"后 0.02%","hint":"注册资本在同行中的序位","delta":"排名 433897/433988"},{"label":"注册资本区间","value":"5000+","hint":"注册资本规模区间"},{"label":"营收分位","value":"后 1.4%","hint":"年营收在同行中的序位","delta":"排名 359192/364126"},{"label":"营收区间","value":"5000+","hint":"年营收规模区间"},{"label":"同行企业总数","value":"433988","hint":"行业同赛道企业总量"}],"core_counts":{"sections":1,"channel_search":0},"core_samples":{},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道分析"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道分析","product_id":"66f3d8bf64bd2be52d68a0fe"}],"limit":"企业分析实际为注册资本/营收同行基准，不等同于渠道结构；模糊名称存在多候选时必须确认主体后再调用。","html_bytes":1060321,"markdown_bytes":2498}
- **pass** 报告标题和摘要必须明确是企业规模同行基准而非渠道结构：channel_analysis实际返回：注册资本分位‘后0.02%（排名433897/433988）’、区间5000+、营收分位‘后1.4%（排名359192/364126）’、区间5000+；标题/摘要明确‘企业规模同行基准’，并否认渠道结构或市场份额含义。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_analysis","status":"data","rows":null,"total":null,"args":{"matchKeyword":"比亚迪股份有限公司","keywordType":"name"}}],"subject":{"enterprise":"比亚迪股份有限公司","matchKeyword":"比亚迪股份有限公司","keywordType":"name","match_raw":"比亚迪股份有限公司","resolved":true,"resolve_reason":"视为企业全称","search_mode":false,"mode":"enterprise","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"注册资本分位","value":"后 0.02%","hint":"注册资本在同行中的序位","delta":"排名 433897/433988"},{"label":"注册资本区间","value":"5000+","hint":"注册资本规模区间"},{"label":"营收分位","value":"后 1.4%","hint":"年营收在同行中的序位","delta":"排名 359192/364126"},{"label":"营收区间","value":"5000+","hint":"年营收规模区间"},{"label":"同行企业总数","value":"433988","hint":"行业同赛道企业总量"}],"core_counts":{"sections":1,"channel_search":0},"core_samples":{},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道分析"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道分析","product_id":"66f3d8bf64bd2be52d68a0fe"}],"limit":"企业分析实际为注册资本/营收同行基准，不等同于渠道结构；模糊名称存在多候选时必须确认主体后再调用。","html_bytes":1060321,"markdown_bytes":2498}

## 离线浏览器检查

[Ego Lite 离线图表、页面溢出和脚本检查](browser-check.json)