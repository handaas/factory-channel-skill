# 工业机器人配件候选登记字段完整度

- 用户需求：请检索工业机器人配件相关渠道/供应商候选，检查当前页企业名称、成立时间和注册资本是否足以进入工商复核队列；主营产品只用于确认基本相关性。
- 决策用途：评估候选记录能否支持后续工商核验，而不是判断供货能力。
- 本轮结果：**本轮检查通过**
- 实际工具调用：1；失败 0
- 章节覆盖率：100%（不代表证据质量）

## 预期业务检查（不自动宣称通过）

- channel_search 至少有一条实际返回记录
- 至少一条记录同时具备非空候选名称、成立时间和注册资本
- 计入完整度的记录还必须有非空主营产品以确认基本相关性
- 完整度结论必须按实际字段逐条计算，不能用总量或请求词代替
- 不得据登记字段认定资质、供货能力或授权关系

## 本轮自动检查发现


## 使用局限

- 注册资本原值不等于实际经营或履约能力
- 精确关键词可能使样本较小

## 证据与复现

- [审计结果](result.json)
- [工具调用、结果形态与响应摘要哈希](calls.json)
- [JSON](report.json) / [HTML](report.html) / [Markdown](report.md)

```bash
python3 factory-channel-skill/scripts/compose_report.py --search '工业机器人配件' --page-size 10 --output factory-channel-skill/output/11-robot-parts-registration-completeness/report.json --report-output factory-channel-skill/output/11-robot-parts-registration-completeness/report.html
```

## 逐场景业务复核

本轮真实产物的全部清单检查均有当前字段证据，且报告保留样本/缺失/关系边界。

- **pass** channel_search 至少有一条实际返回记录：同一条佛山市金杰铖记录同时有名称、成立时间2012-10-18、注册资本100万元和机器配件/机械臂/机器人主营产品；当前页10条、总数145，报告未据登记字段认定资质或供货能力。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":145,"args":{"matchKeyword":"工业机器人配件","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人配件","matchKeyword":"工业机器人配件","keywordType":"name","match_raw":"工业机器人配件","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"145","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"},{"渠道/供应商名称":"广州铭心自动化设备有限公司","主营产品":"发那科机器人配件、机器人维修回收、工业机器人配件、机器人配件销、发那科、库卡机器人配件、协作机器人、工业机器人回收、PLC、工业机器人保养、驱动器、库卡、工业机器人、ABB机器人、安川机器人、电子制造设备、工业机器人调试、ABB、ABB机器人配件、安川、发那科机器人、示教器","成立时间":"2017-06-23","注册资本":"500.000000万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1066174,"markdown_bytes":10481}
- **pass** 至少一条记录同时具备非空候选名称、成立时间和注册资本：同一条佛山市金杰铖记录同时有名称、成立时间2012-10-18、注册资本100万元和机器配件/机械臂/机器人主营产品；当前页10条、总数145，报告未据登记字段认定资质或供货能力。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":145,"args":{"matchKeyword":"工业机器人配件","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人配件","matchKeyword":"工业机器人配件","keywordType":"name","match_raw":"工业机器人配件","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"145","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"},{"渠道/供应商名称":"广州铭心自动化设备有限公司","主营产品":"发那科机器人配件、机器人维修回收、工业机器人配件、机器人配件销、发那科、库卡机器人配件、协作机器人、工业机器人回收、PLC、工业机器人保养、驱动器、库卡、工业机器人、ABB机器人、安川机器人、电子制造设备、工业机器人调试、ABB、ABB机器人配件、安川、发那科机器人、示教器","成立时间":"2017-06-23","注册资本":"500.000000万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1066174,"markdown_bytes":10481}
- **pass** 计入完整度的记录还必须有非空主营产品以确认基本相关性：同一条佛山市金杰铖记录同时有名称、成立时间2012-10-18、注册资本100万元和机器配件/机械臂/机器人主营产品；当前页10条、总数145，报告未据登记字段认定资质或供货能力。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":145,"args":{"matchKeyword":"工业机器人配件","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人配件","matchKeyword":"工业机器人配件","keywordType":"name","match_raw":"工业机器人配件","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"145","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"},{"渠道/供应商名称":"广州铭心自动化设备有限公司","主营产品":"发那科机器人配件、机器人维修回收、工业机器人配件、机器人配件销、发那科、库卡机器人配件、协作机器人、工业机器人回收、PLC、工业机器人保养、驱动器、库卡、工业机器人、ABB机器人、安川机器人、电子制造设备、工业机器人调试、ABB、ABB机器人配件、安川、发那科机器人、示教器","成立时间":"2017-06-23","注册资本":"500.000000万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1066174,"markdown_bytes":10481}
- **pass** 完整度结论必须按实际字段逐条计算，不能用总量或请求词代替：同一条佛山市金杰铖记录同时有名称、成立时间2012-10-18、注册资本100万元和机器配件/机械臂/机器人主营产品；当前页10条、总数145，报告未据登记字段认定资质或供货能力。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":145,"args":{"matchKeyword":"工业机器人配件","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人配件","matchKeyword":"工业机器人配件","keywordType":"name","match_raw":"工业机器人配件","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"145","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"},{"渠道/供应商名称":"广州铭心自动化设备有限公司","主营产品":"发那科机器人配件、机器人维修回收、工业机器人配件、机器人配件销、发那科、库卡机器人配件、协作机器人、工业机器人回收、PLC、工业机器人保养、驱动器、库卡、工业机器人、ABB机器人、安川机器人、电子制造设备、工业机器人调试、ABB、ABB机器人配件、安川、发那科机器人、示教器","成立时间":"2017-06-23","注册资本":"500.000000万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1066174,"markdown_bytes":10481}
- **pass** 不得据登记字段认定资质、供货能力或授权关系：同一条佛山市金杰铖记录同时有名称、成立时间2012-10-18、注册资本100万元和机器配件/机械臂/机器人主营产品；当前页10条、总数145，报告未据登记字段认定资质或供货能力。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":145,"args":{"matchKeyword":"工业机器人配件","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人配件","matchKeyword":"工业机器人配件","keywordType":"name","match_raw":"工业机器人配件","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"145","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"},{"渠道/供应商名称":"广州铭心自动化设备有限公司","主营产品":"发那科机器人配件、机器人维修回收、工业机器人配件、机器人配件销、发那科、库卡机器人配件、协作机器人、工业机器人回收、PLC、工业机器人保养、驱动器、库卡、工业机器人、ABB机器人、安川机器人、电子制造设备、工业机器人调试、ABB、ABB机器人配件、安川、发那科机器人、示教器","成立时间":"2017-06-23","注册资本":"500.000000万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1066174,"markdown_bytes":10481}

## 离线浏览器检查

[Ego Lite 离线图表、页面溢出和脚本检查](browser-check.json)