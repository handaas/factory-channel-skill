# factory-channel-skill：已验收示例

本目录只展示 **4 个完全通过的真实正向场景**（最低要求4例）。

每例均为真实、非空、非缓存调用；技术检查、独立业务检查和离线浏览器检查全部通过。报告保持原实测字节，不把空数据、报错处理或仅生成页面计作通过。

| 场景 | 真实使用需求 | 报告 |
|---|---|---|
| [工业机器人渠道市场](05-industrial-robotics/README.md) | 请检索工业机器人相关渠道和供应商，不限定地区。 | [HTML](05-industrial-robotics/report.html) / [MD](05-industrial-robotics/report.md) / [JSON](05-industrial-robotics/report.json) |
| [比亚迪企业规模同行基准](09-byd-peer-scale-benchmark/README.md) | 请展示比亚迪股份有限公司在上游口径下的注册资本和营收同行基准，只报告实际返回的分位、排名、区间或同行总数；不要分析渠道结构。 | [HTML](09-byd-peer-scale-benchmark/report.html) / [MD](09-byd-peer-scale-benchmark/report.md) / [JSON](09-byd-peer-scale-benchmark/report.json) |
| [库卡机器人相关候选产品组合筛查](10-kuka-product-mix-screen/README.md) | 请检索与库卡机器人相关的渠道/供应商候选，比较当前页实际主营产品，区分整机、配件、维修或自动化组件线索；不要判断授权关系。 | [HTML](10-kuka-product-mix-screen/report.html) / [MD](10-kuka-product-mix-screen/report.md) / [JSON](10-kuka-product-mix-screen/report.json) |
| [工业机器人配件候选登记字段完整度](11-robot-parts-registration-completeness/README.md) | 请检索工业机器人配件相关渠道/供应商候选，检查当前页企业名称、成立时间和注册资本是否足以进入工商复核队列；主营产品只用于确认基本相关性。 | [HTML](11-robot-parts-registration-completeness/report.html) / [MD](11-robot-parts-registration-completeness/report.md) / [JSON](11-robot-parts-registration-completeness/report.json) |

- [逐例验收结果](results.json) · [业务复核](review.json) · [证据摘要](evidence-index.json)
- [完整测试记录](../test-records/live-replaced-20261027/README.md)仅用于审计，不属于可展示示例。
- 当前数据与结论限于原查询时点及公开样本；覆盖率不代表准确率或低风险。
