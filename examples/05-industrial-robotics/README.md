# 工业机器人渠道市场

- 用户需求：请检索工业机器人相关渠道和供应商，不限定地区。
- 决策用途：全国渠道伙伴发现
- 本轮结果：**本轮检查通过**
- 实际工具调用：1；失败 0
- 章节覆盖率：100%（不代表证据质量）

## 预期业务检查（不自动宣称通过）

- 无地址时不传空地址参数
- 综合搜索模式生效
- 命中数量与展示记录区分
- 洞察基于主营/地址等返回证据

## 本轮自动检查发现


## 使用局限

- 全国检索第一页不能代表完整市场
- 关键词匹配会存在非核心业务企业

## 证据与复现

- [审计结果](result.json)
- [工具调用、结果形态与响应摘要哈希](calls.json)
- [JSON](report.json) / [HTML](report.html) / [Markdown](report.md)

```bash
python3 factory-channel-skill/scripts/compose_report.py --search '工业机器人' --page-size 10 --output factory-channel-skill/output/05-industrial-robotics/report.json --report-output factory-channel-skill/output/05-industrial-robotics/report.html
```

## 逐场景业务复核

本轮真实产物的全部清单检查均有当前字段证据，且报告保留样本/缺失/关系边界。

- **pass** 无地址时不传空地址参数：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":10565,"args":{"matchKeyword":"工业机器人","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人","matchKeyword":"工业机器人","keywordType":"name","match_raw":"工业机器人","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"10565","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"上海思奉贸易有限公司","主营产品":"工业自动化控制设、联轴器、KUKA库卡、模块、电动螺丝刀、vahle、过滤器、泵阀、电磨、进口贸易、夹具、编码器、气动工具、传感器、焊接配件、滤芯、德国机械产品及备件、电阻、工控原件、dold继电器、变送器、滚筒、液压工具、BEKO贝克欧、PLC、电动气动工具、制动器、电源、电机、可控硅、继电器、五金、进口泵阀、ATLAS阿特拉、焊接设备、RDP传感器、钳工工具、bartec、焊机设备、工业机器人、工业阀、GEMU盖米泵阀、电焊机、工业泵、工装夹具、工件夹具、工控产品、仪器仪表、机械设备、hbm、gemu、KUKA机器人、atlas、焊机、电动工具、气动打磨机、阻尼器、称重传感器、气缸、FRONIUS焊、变压器、光栅、自动化控制设备","成立时间":"2015-04-02","注册资本":"1000.000000万人民币"},{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1067764,"markdown_bytes":12077}
- **pass** 综合搜索模式生效：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":10565,"args":{"matchKeyword":"工业机器人","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人","matchKeyword":"工业机器人","keywordType":"name","match_raw":"工业机器人","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"10565","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"上海思奉贸易有限公司","主营产品":"工业自动化控制设、联轴器、KUKA库卡、模块、电动螺丝刀、vahle、过滤器、泵阀、电磨、进口贸易、夹具、编码器、气动工具、传感器、焊接配件、滤芯、德国机械产品及备件、电阻、工控原件、dold继电器、变送器、滚筒、液压工具、BEKO贝克欧、PLC、电动气动工具、制动器、电源、电机、可控硅、继电器、五金、进口泵阀、ATLAS阿特拉、焊接设备、RDP传感器、钳工工具、bartec、焊机设备、工业机器人、工业阀、GEMU盖米泵阀、电焊机、工业泵、工装夹具、工件夹具、工控产品、仪器仪表、机械设备、hbm、gemu、KUKA机器人、atlas、焊机、电动工具、气动打磨机、阻尼器、称重传感器、气缸、FRONIUS焊、变压器、光栅、自动化控制设备","成立时间":"2015-04-02","注册资本":"1000.000000万人民币"},{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1067764,"markdown_bytes":12077}
- **pass** 命中数量与展示记录区分：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":10565,"args":{"matchKeyword":"工业机器人","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人","matchKeyword":"工业机器人","keywordType":"name","match_raw":"工业机器人","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"10565","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"上海思奉贸易有限公司","主营产品":"工业自动化控制设、联轴器、KUKA库卡、模块、电动螺丝刀、vahle、过滤器、泵阀、电磨、进口贸易、夹具、编码器、气动工具、传感器、焊接配件、滤芯、德国机械产品及备件、电阻、工控原件、dold继电器、变送器、滚筒、液压工具、BEKO贝克欧、PLC、电动气动工具、制动器、电源、电机、可控硅、继电器、五金、进口泵阀、ATLAS阿特拉、焊接设备、RDP传感器、钳工工具、bartec、焊机设备、工业机器人、工业阀、GEMU盖米泵阀、电焊机、工业泵、工装夹具、工件夹具、工控产品、仪器仪表、机械设备、hbm、gemu、KUKA机器人、atlas、焊机、电动工具、气动打磨机、阻尼器、称重传感器、气缸、FRONIUS焊、变压器、光栅、自动化控制设备","成立时间":"2015-04-02","注册资本":"1000.000000万人民币"},{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1067764,"markdown_bytes":12077}
- **pass** 洞察基于主营/地址等返回证据：该项由当前调用参数、报告同名字段、样本与局限说明共同核对。 当前冻结快照：{"technical_status":"passed","successful_data_calls":1,"calls":[{"tool":"channel_insight_channel_search","status":"data","rows":10,"total":10565,"args":{"matchKeyword":"工业机器人","keywordType":"综合搜索","pageIndex":1,"pageSize":10}}],"subject":{"enterprise":"工业机器人","matchKeyword":"工业机器人","keywordType":"name","match_raw":"工业机器人","resolved":false,"resolve_reason":"未指定企业（渠道检索模式）","search_mode":true,"mode":"search","requires_confirmation":false,"candidates":[],"fuzzy_requested":false},"metrics":[{"label":"渠道/供应商","value":"10565","hint":"渠道搜索命中数"}],"core_counts":{"sections":1,"channel_search":10},"core_samples":{"channel_search":[{"渠道/供应商名称":"上海思奉贸易有限公司","主营产品":"工业自动化控制设、联轴器、KUKA库卡、模块、电动螺丝刀、vahle、过滤器、泵阀、电磨、进口贸易、夹具、编码器、气动工具、传感器、焊接配件、滤芯、德国机械产品及备件、电阻、工控原件、dold继电器、变送器、滚筒、液压工具、BEKO贝克欧、PLC、电动气动工具、制动器、电源、电机、可控硅、继电器、五金、进口泵阀、ATLAS阿特拉、焊接设备、RDP传感器、钳工工具、bartec、焊机设备、工业机器人、工业阀、GEMU盖米泵阀、电焊机、工业泵、工装夹具、工件夹具、工控产品、仪器仪表、机械设备、hbm、gemu、KUKA机器人、atlas、焊机、电动工具、气动打磨机、阻尼器、称重传感器、气缸、FRONIUS焊、变压器、光栅、自动化控制设备","成立时间":"2015-04-02","注册资本":"1000.000000万人民币"},{"渠道/供应商名称":"佛山市金杰铖贸易有限公司","主营产品":"机器配件、电源板、计算机板、机器手臂、工业机器、齿轮减速机、扩展板、通讯基板、接口板、组装机、伺服板、弧焊板、机械臂、扩展大板、通讯线、机器人、外部轴卡、动力线、电源模块、机械手、控制电源、柜主板、驱动模块、安全板、示教器","成立时间":"2012-10-18","注册资本":"100.0万人民币"}]},"quality":{"total_sections":1,"populated_sections":1,"empty_sections":0,"coverage_pct":100},"caliber_products":["渠道搜索"],"source_server":"factory-channel-mcp-server","source_products":[{"name":"渠道搜索","product_id":"66b71b498dd25dbfbe8b0acd"}],"limit":"仅为渠道/供应商关键词检索当前页样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。","html_bytes":1067764,"markdown_bytes":12077}

## 离线浏览器检查

[Ego Lite 离线图表、页面溢出和脚本检查](browser-check.json)