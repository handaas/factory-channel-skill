#!/usr/bin/env python3
"""Compose a factory channel analysis report by orchestrating the channel MCP.

Calls the upstream factory-channel-mcp-server tools and assembles a structured
JSON payload rendered into a professional HTML / Markdown report. Supports
``--dry-run`` which returns a well-formed skeleton from the bundled sample data
WITHOUT contacting the MCP.

Two analysis modes are supported:
  - Enterprise mode (default, requires ``--enterprise``): returns the
    enterprise's channel analysis (vs peers) using
    `channel_insight_channel_analysis`.
  - Channel search mode (``--search`` + optional ``--address``): returns
    channel / supplier records matching a keyword using
    `channel_insight_channel_search`.

This file never prints secrets; MCP credentials live in the server's own .env.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any, Dict, List, Mapping, Optional

from common import REPORT_BANNER, REPORT_TYPE, json_dumps, load_json_file, print_json
import mcp_client
from render_report import render_html, render_markdown, html_to_pdf

SAMPLE_PATH = pathlib.Path(__file__).resolve().parent.parent / "assets" / "report.example.json"

# Factory-channel MCP tools.
T_FUZZY = "channel_insight_fuzzy_search"
T_ANALYSIS = "channel_insight_channel_analysis"
T_SEARCH = "channel_insight_channel_search"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _is_api_error(value: Any) -> bool:
    """Detect MCP API error responses (not empty data, but actual failures like 405)."""
    if value is None:
        return False
    if isinstance(value, str):
        return any(s in value for s in ("接口调用失败", "查询失败", "状态码：4", "状态码：5"))
    if isinstance(value, dict):
        for v in value.values():
            if isinstance(v, str) and any(s in v for s in ("接口调用失败", "查询失败", "状态码：4", "状态码：5")):
                return True
    return False

def _first_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        if _is_api_error(value):
            return []
        # Treat upstream empty responses ({"text": "查询数据为空"}) and internal
        # skip markers ({"_error": "未指定..."}) as empty so tables don't render
        # a phantom all-"-" row.
        if set(value.keys()) <= {"text", "error", "code", "_error"} and not any(
            isinstance(value.get(k), list) for k in ("resultList", "list", "items", "data")
        ):
            return []
        for key in ("resultList", "list", "items", "data"):
            if isinstance(value.get(key), list):
                return value[key]
    if value in (None, "", {}):
        return []
    return [value]


def _first_record(value: Any) -> Dict[str, Any]:
    for record in _first_list(value):
        if isinstance(record, dict):
            return record
    if isinstance(value, dict):
        return value
    return {}


def _text(value: Any, limit: int = 0) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        t = json.dumps(value, ensure_ascii=False)
    else:
        t = str(value)
    t = " ".join(t.split())
    if limit and len(t) > limit:
        return t[: limit - 1].rstrip() + "…"
    return t


def _int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_call(tool: str, arguments: Dict[str, Any]) -> Any:
    try:
        result = mcp_client.call_tool(tool, arguments)
        if _is_api_error(result):
            return {"_error": "API错误"}
        return result
    except Exception as exc:
        return {"_error": str(exc)}


def _safe_total(payload: Any) -> Any:
    if isinstance(payload, dict):
        if _is_api_error(payload):
            return None
        return payload.get("total")
    return None


def _join_list(value: Any) -> str:
    items = _first_list(value)
    return "、".join(_text(t) for t in items if t) if items else ""


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #

def resolve_enterprise_name(raw: str) -> Dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        return {"keyword": "", "enterprise": "", "resolved": False, "reason": "关键词为空"}
    if any(suffix in raw for suffix in ("公司", "集团", "有限", "院", "厂", "中心", "事务所", "合作社", "合伙")):
        return {"keyword": raw, "enterprise": raw, "resolved": True, "reason": "视为企业全称"}
    fuzzy = _safe_call(T_FUZZY, {"matchKeyword": raw, "pageSize": 1})
    record = _first_record(fuzzy)
    name = str(record.get("name") or "").strip()
    if name:
        return {"keyword": raw, "enterprise": name, "resolved": True, "reason": "由关键词模糊查询补全", "fuzzy_total": _int(_safe_total(fuzzy)), "record": record}
    return {"keyword": raw, "enterprise": raw, "resolved": False, "reason": "模糊查询未命中企业全称，按关键词直查"}


# --------------------------------------------------------------------------- #
# Enterprise profile helpers (from fuzzy_search record)
# --------------------------------------------------------------------------- #

def _extract_profile(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract enterprise profile fields from a fuzzy_search record."""
    return {
        "name": _text(record.get("name")),
        "reg_capital": record.get("regCapitalValue"),
        "reg_capital_coin": _text(record.get("regCapitalCoinType")),
        "annual_turnover": _text(record.get("annualTurnover")),
        "oper_status": _text(record.get("operStatus")),
        "enterprise_type": _text(record.get("enterpriseType")),
        "found_time": _text(record.get("foundTime")),
        "legal_rep": _text(record.get("legalRepresentative")),
        "address": _text(record.get("address")),
        "homepage": _text(record.get("homepage")),
    }


def _format_capital(val: Any, coin: str = "") -> str:
    """Format capital value: 10995210218.0 -> '109.95 亿'."""
    try:
        v = float(val)
        if v >= 1e8:
            s = f"{v / 1e8:.2f} 亿"
        elif v >= 1e4:
            s = f"{v / 1e4:.2f} 万"
        else:
            s = f"{v:.0f}"
        if coin:
            s += f" {coin}"
        return s
    except (TypeError, ValueError):
        return _text(val) if val else "-"


def _enrich_metrics_with_profile(metrics: List[Dict[str, Any]], record: Any) -> List[Dict[str, Any]]:
    """Append enterprise profile metrics from a fuzzy_search record."""
    if not isinstance(record, dict):
        return metrics
    _prof = _extract_profile(record)
    if _prof.get("reg_capital") and _prof["reg_capital"] not in ("-", "", None):
        metrics.append({"label": "注册资本", "value": _format_capital(_prof["reg_capital"], _prof.get("reg_capital_coin", "")), "hint": "工商登记注册资本"})
    if _prof.get("found_time") and _prof["found_time"] != "-":
        metrics.append({"label": "成立时间", "value": _prof["found_time"], "hint": "工商登记成立日期"})
    if _prof.get("oper_status") and _prof["oper_status"] != "-":
        metrics.append({"label": "经营状态", "value": _prof["oper_status"], "hint": "工商登记经营状态"})
    if _prof.get("enterprise_type") and _prof["enterprise_type"] != "-":
        metrics.append({"label": "企业类型", "value": _prof["enterprise_type"], "hint": "工商登记企业类型"})
    if _prof.get("legal_rep") and _prof["legal_rep"] != "-":
        metrics.append({"label": "法定代表人", "value": _prof["legal_rep"], "hint": "工商登记法定代表人"})
    return metrics


def _derive_core_metrics(metrics: List[Dict[str, Any]], core: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Derive additional metrics from core analysis sections."""
    analysis = core.get("channel_analysis", {}) if isinstance(core, dict) else {}
    if isinstance(analysis, dict) and analysis:
        peer_total = analysis.get("注册资本同行总数") or analysis.get("营收同行总数")
        if peer_total and str(peer_total) not in ("-", "", "0", "None"):
            metrics.append({"label": "同行企业总数", "value": str(peer_total), "hint": "行业同赛道企业总量"})
        reg_range = analysis.get("注册资本区间")
        if reg_range and str(reg_range) not in ("-", "", "None"):
            metrics.append({"label": "注册资本区间", "value": str(reg_range), "hint": "行业注册资本区间定位"})
        rev_range = analysis.get("营收区间")
        if rev_range and str(rev_range) not in ("-", "", "None"):
            metrics.append({"label": "营收区间", "value": str(rev_range), "hint": "行业营收区间定位"})
    return metrics


# --------------------------------------------------------------------------- #
# Section builders
# --------------------------------------------------------------------------- #

def build_subject(raw: str, resolved: Mapping[str, Any], keyword_type: str, search_mode: bool) -> Dict[str, Any]:
    return {
        "enterprise": resolved.get("enterprise") or raw,
        "matchKeyword": resolved.get("enterprise") or raw,
        "keywordType": keyword_type,
        "match_raw": raw,
        "resolved": bool(resolved.get("resolved")) and not search_mode,
        "resolve_reason": resolved.get("reason", ""),
        "search_mode": search_mode,
    }


def build_caliber(subject: Mapping[str, Any], search_mode: bool) -> Dict[str, Any]:
    if search_mode:
        match_target = subject.get("match_raw") or "渠道检索（无指定企业）"
        match_type = "渠道检索模式：按渠道关键词 / 地址检索渠道与供应商，与特定企业主体无关"
    else:
        match_target = subject.get("enterprise") or subject.get("match_raw")
        match_type = f"渠道分析按企业主体匹配（keywordType={subject.get('keywordType', 'name')}），并与同行对比；支持企业名称/注册号/统一社会信用代码/企业 id"
    return {
        "match_target": match_target,
        "match_type": match_type,
        "data_scope": "渠道分析（与同行对比）、渠道/供应商搜索",
        "products": ["渠道分析", "渠道搜索"],
        "limit": "数据来自公开渠道信息；少量字段可能存在更新延迟。",
    }


def _kv_from(payload: Any, mapping: List[tuple]) -> Dict[str, Any]:
    p = payload if isinstance(payload, dict) else {}
    out: Dict[str, Any] = {}
    for key, label in mapping:
        val = p.get(key)
        if val not in (None, "", [], {}):
            out[label] = _text(val)
    return out


def _table_from(payload: Any, fields: List[tuple]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in _first_list(payload):
        if not isinstance(item, dict):
            continue
        row: Dict[str, Any] = {}
        for key, label in fields:
            row[label] = _text(item.get(key)) or "-"
        rows.append(row)
    return rows


def _concentration(rows: List[Mapping[str, Any]], name_key: str, value_key: str, top_n: int = 3) -> Dict[str, Any]:
    """Compute top-N concentration (CRn) and dominant category from {name,count} rows."""
    items = []
    for r in rows:
        try:
            items.append((r.get(name_key, "-"), float(str(r.get(value_key, 0)).replace(",", ""))))
        except (TypeError, ValueError):
            items.append((r.get(name_key, "-"), 0.0))
    total = sum(v for _, v in items)
    if not total:
        return {}
    items.sort(key=lambda x: x[1], reverse=True)
    cr = sum(v for _, v in items[:top_n]) / total * 100
    return {"top": items[0][0], "top_share": items[0][1] / total * 100, "cr": cr, "total": total, "n": len(items)}


def _reg_capital_text(value: Any) -> str:
    """regCapital 真实结构 {coinType, origin, value}：优先 origin 文本，回退 value+币种。"""
    if isinstance(value, dict):
        if value.get("origin"):
            return _text(value.get("origin"))
        coin = value.get("coinType") or ""
        val = value.get("value")
        if val is not None:
            return f"{coin}{_text(val)}".strip()
    return _text(value)


def _rank_pct(rank: Any, total: Any) -> Optional[str]:
    """分位文本：rank 表示"超过同行的数量"，分位 = (1 - rank/total)*100。

    rank=超过同行的数量，因此分位越接近 100% 表示越靠前。当百分比 <1% 时显示两位小数，
    避免大企业被误显示为"前 0.0%"。
    """
    r = _int(rank)
    t = _int(total)
    if r is None or not t or t <= 0:
        return None
    pct = (1 - r / t) * 100
    pct_str = f"{pct:.2f}%" if pct < 1 else f"{pct:.1f}%"
    return f"前 {pct_str}（排名 {r}/{t}）"


def build_core_analysis(analysis: Any, search: Any) -> Dict[str, Any]:
    # 渠道分析 KV — 真实字段：financialStat.{categoryCount, regCapitalRank,
    # regCapitalScope} + salesStat.{categoryCount, annualTurnoverRank,
    # annualTurnoverScope}.
    analysis_kv: Dict[str, Any] = {}
    a = analysis if isinstance(analysis, dict) and "_error" not in analysis else {}
    fin = a.get("financialStat") if isinstance(a.get("financialStat"), dict) else {}
    sales = a.get("salesStat") if isinstance(a.get("salesStat"), dict) else {}
    if fin.get("regCapitalScope"):
        analysis_kv["注册资本区间"] = _text(fin.get("regCapitalScope"))
    cap_pct = _rank_pct(fin.get("regCapitalRank"), fin.get("categoryCount"))
    if cap_pct:
        analysis_kv["注册资本分位"] = cap_pct
    if sales.get("annualTurnoverScope"):
        analysis_kv["营收区间"] = _text(sales.get("annualTurnoverScope"))
    sales_pct = _rank_pct(sales.get("annualTurnoverRank"), sales.get("categoryCount"))
    if sales_pct:
        analysis_kv["营收分位"] = sales_pct
    if fin.get("categoryCount") is not None:
        analysis_kv["注册资本同行总数"] = _text(fin.get("categoryCount"))
    if sales.get("categoryCount") is not None:
        analysis_kv["营收同行总数"] = _text(sales.get("categoryCount"))

    # 渠道/供应商搜索明细表 — 真实字段：name / mainProducts(list) / foundTime /
    # regCapital({coinType, origin, value}) / nameId。
    search_rows: List[Dict[str, Any]] = []
    for item in _first_list(search):
        if not isinstance(item, dict):
            continue
        search_rows.append({
            "渠道/供应商名称": _text(item.get("name")) or "-",
            "主营产品": _join_list(item.get("mainProducts")) or "-",
            "成立时间": _text(item.get("foundTime")) or "-",
            "注册资本": _reg_capital_text(item.get("regCapital")) or "-",
        })

    sections: List[Dict[str, Any]] = []
    if analysis_kv:
        sections.append({"key": "channel_analysis", "title": "渠道分析（与同行对比）", "kind": "kv", "note": "注册资本 / 年营收在同行中的分位与区间"})
    if search_rows or (isinstance(search, dict) and search.get("total") is not None):
        total = _safe_total(search)
        sections.append({"key": "channel_search", "title": "渠道/供应商明细", "kind": "table", "note": f"渠道/供应商记录 {total if total is not None else '若干'} 条，展示前 {len(search_rows)} 条", "columns": [("渠道/供应商名称", "渠道/供应商名称"), ("主营产品", "主营产品"), ("成立时间", "成立时间"), ("注册资本", "注册资本")]})

    return {
        "sections": sections,
        "channel_analysis": analysis_kv,
        "channel_search": search_rows,
    }


def build_records(core: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in core.get("channel_search") or []:
        rows.append({
            "渠道/供应商名称": item.get("渠道/供应商名称") or "-",
            "主营产品": item.get("主营产品") or "-",
            "成立时间": item.get("成立时间") or "-",
            "注册资本": item.get("注册资本") or "-",
        })
    return rows[:20]


def build_insights(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: List[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []
    metric_map = {m["label"]: str(m["value"]) for m in metrics}
    analysis_kv = core.get("channel_analysis") or {}

    if subject.get("search_mode"):
        search_total = metric_map.get("渠道/供应商")
        if search_total:
            insights.append({
                "feature": "渠道检索规模",
                "evidence": f"检索命中渠道/供应商 {search_total} 条。",
                "interpretation": "检索规模反映目标领域的渠道/供应商供给密度，是渠道寻源与供应商初筛的参考。",
            })
        search_rows = core.get("channel_search") or []
        if search_rows:
            insights.append({
                "feature": "供应商画像",
                "evidence": f"渠道/供应商明细 {len(search_rows)} 条。",
                "interpretation": "明细反映目标领域供应商的地域与主营产品分布，可结合主营产品筛选垂直领域优质供应商。",
            })
    else:
        # 真实分析维度：注册资本分位 / 营收分位 / 区间。
        cap_pct = analysis_kv.get("注册资本分位") or metric_map.get("注册资本分位")
        cap_scope = analysis_kv.get("注册资本区间") or metric_map.get("注册资本区间")
        if cap_pct or cap_scope:
            parts = []
            if cap_pct:
                parts.append(f"注册资本分位 {cap_pct}")
            if cap_scope:
                parts.append(f"区间 {cap_scope}")
            insights.append({
                "feature": "资金实力",
                "evidence": "、".join(parts) + "。",
                "interpretation": "注册资本分位反映企业在同行中的资金实力：分位越靠前代表资本实力越强，是供应链履约与抗风险能力的硬指标。",
            })
        sales_pct = analysis_kv.get("营收分位") or metric_map.get("营收分位")
        sales_scope = analysis_kv.get("营收区间") or metric_map.get("营收区间")
        if sales_pct or sales_scope:
            parts = []
            if sales_pct:
                parts.append(f"营收分位 {sales_pct}")
            if sales_scope:
                parts.append(f"区间 {sales_scope}")
            insights.append({
                "feature": "销售实力",
                "evidence": "、".join(parts) + "。",
                "interpretation": "营收分位反映企业在同行中的销售规模：分位越靠前代表市场占有率与销售网络越强。",
            })
        # 同行总数（行业体量）
        peer_total = analysis_kv.get("注册资本同行总数") or analysis_kv.get("营收同行总数")
        if peer_total:
            insights.append({
                "feature": "行业体量",
                "evidence": f"同行企业约 {peer_total} 家。",
                "interpretation": "同行总数反映所在赛道的竞争密度：同行越多说明赛道越拥挤，分位排名的含金量也越高。",
            })
    if not insights:
        insights.append({
            "feature": "数据完整性",
            "evidence": "部分维度未返回有效数据。",
            "interpretation": "建议核对匹配关键词是否为企业全称或检索条件，或检查 MCP 连接与上游数据产品覆盖范围。",
        })
    return insights


def build_metrics(analysis: Any, search: Any) -> List[Dict[str, Any]]:
    metrics: List[Dict[str, Any]] = []
    a = analysis if isinstance(analysis, dict) and "_error" not in analysis else {}
    fin = a.get("financialStat") if isinstance(a.get("financialStat"), dict) else {}
    sales = a.get("salesStat") if isinstance(a.get("salesStat"), dict) else {}

    # 真实结构：financialStat / salesStat 各含 categoryCount(同行总数)、rank、scope
    fin_rank = _int(fin.get("regCapitalRank"))
    fin_total = _int(fin.get("categoryCount"))
    sales_rank = _int(sales.get("annualTurnoverRank"))
    sales_total = _int(sales.get("categoryCount"))

    if fin_rank is not None and fin_total and fin_total > 0:
        pct = (1 - fin_rank / fin_total) * 100
        pct_str = f"{pct:.2f}%" if pct < 1 else f"{pct:.1f}%"
        metrics.append({"label": "注册资本分位", "value": f"前 {pct_str}", "hint": "注册资本在同行中的位置", "delta": f"排名 {fin_rank}/{fin_total}"})
    if fin.get("regCapitalScope"):
        metrics.append({"label": "注册资本区间", "value": _text(fin.get("regCapitalScope")), "hint": "注册资本规模区间"})
    if sales_rank is not None and sales_total and sales_total > 0:
        pct = (1 - sales_rank / sales_total) * 100
        pct_str = f"{pct:.2f}%" if pct < 1 else f"{pct:.1f}%"
        metrics.append({"label": "营收分位", "value": f"前 {pct_str}", "hint": "年营收在同行中的位置", "delta": f"排名 {sales_rank}/{sales_total}"})
    if sales.get("annualTurnoverScope"):
        metrics.append({"label": "营收区间", "value": _text(sales.get("annualTurnoverScope")), "hint": "年营收规模区间"})
    if isinstance(search, dict) and search.get("total") is not None:
        total = _safe_total(search) or len(_first_list(search))
        metrics.append({"label": "渠道/供应商", "value": _text(total), "hint": "渠道搜索命中数"})
    return [m for m in metrics if m.get("value") not in ("", None, "-")]


def build_abstract(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: List[Mapping[str, Any]]) -> str:
    if subject.get("search_mode"):
        name = subject.get("match_raw") or "目标渠道"
        parts = [f"本报告以“{name}”为检索范围，基于公开渠道数据，系统呈现渠道/供应商的检索结果。"]
    else:
        name = subject.get("enterprise") or subject.get("match_raw") or "目标企业"
        parts = [f"本报告以“{name}”为分析对象，基于公开渠道数据，系统呈现企业渠道结构并与同行对比，同时给出渠道/供应商检索明细。"]
    if metrics:
        kv = "、".join(f"{m['label']} {m['value']}" for m in metrics[:5])
        parts.append(f"关键指标包括：{kv}。")
    parts.append("报告围绕渠道规模、同行对比与渠道结构给出结构化解读，便于销售/采购渠道管理、供应商寻源与渠道策略决策参考。")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# Dry-run sample
# --------------------------------------------------------------------------- #

def build_dry_run_payload(raw: str, keyword_type: str) -> Dict[str, Any]:
    try:
        sample = load_json_file(SAMPLE_PATH)
    except Exception:
        sample = {}
    sample = sample if isinstance(sample, dict) else {}
    subject = sample.get("subject") or {"enterprise": raw, "matchKeyword": raw, "keywordType": keyword_type, "match_raw": raw}
    subject = {**subject, "match_raw": raw, "keywordType": keyword_type}
    core = sample.get("core_analysis") or {}
    metrics = sample.get("metrics") or []
    return _assemble(subject, core, metrics, dry_run=True, search_mode=bool(subject.get("search_mode")))


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #

def _assemble(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: List[Mapping[str, Any]], *, dry_run: bool, search_mode: bool = False) -> Dict[str, Any]:
    abstract = build_abstract(subject, core, metrics)
    records = build_records(core)
    insights = build_insights(subject, core, metrics)
    # Quality gate: count populated core-analysis sections.
    ca = core if isinstance(core, dict) else {}
    secs = ca.get("sections", [])
    if secs:
        total_secs = len(secs)
        populated = sum(1 for s in secs if isinstance(s, dict) and ca.get(s.get("key")) not in (None, "", [], {}))
    else:
        total_secs = max(1, len([k for k in ca if k != "sections"]))
        populated = sum(1 for k in ca if k != "sections" and ca.get(k) not in (None, "", [], {}))
    quality_report = {
        "total_sections": total_secs,
        "populated_sections": populated,
        "empty_sections": total_secs - populated,
        "coverage_pct": round(populated / max(1, total_secs) * 100),
    }
    if populated == 0:
        import sys
        print("⚠️ 质量门禁警告: 所有核心分析维度均无数据", file=sys.stderr)
    mode_label = "渠道检索" if search_mode else "企业渠道分析"
    title = f"{subject.get('enterprise') or subject.get('match_raw') or '目标'} 渠道信息分析报告（{mode_label}）"
    return {
        "report_type": REPORT_TYPE,
        "title": title,
        "banner": REPORT_BANNER,
        "subject": dict(subject),
        "abstract": abstract,
        "summary": abstract,
        "executive_summary": [item["interpretation"] for item in insights][:5] or [abstract[:120]],
        "metrics": list(metrics),
        "caliber": build_caliber(subject, search_mode),
        "core_analysis": dict(core),
        "representative_records": records,
        "insights": insights,
        "data_source": {
            "mcp_server": "factory-channel-mcp-server",
            "products": [
                {"name": "渠道分析", "product_id": "66f3d8bf64bd2be52d68a0fe"},
                {"name": "渠道搜索", "product_id": "66b71b498dd25dbfbe8b0acd"},
            ],
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "dry_run": dry_run,
            "quality_report": quality_report,
            "mode": "channel_search" if search_mode else "enterprise",
        },
    }


def build_payload(raw: str, keyword_type: str, search_keyword: Optional[str], address: Optional[str], page_size: int) -> Dict[str, Any]:
    search_mode = bool(search_keyword)
    resolved = resolve_enterprise_name(raw) if raw else {"enterprise": "", "resolved": False, "reason": "未指定企业（渠道检索模式）"}
    enterprise = resolved.get("enterprise") or raw

    analysis: Any = {"_error": "未指定企业，跳过渠道分析"} if not raw else _safe_call(T_ANALYSIS, {"matchKeyword": enterprise, "keywordType": keyword_type})

    # 渠道搜索：keywordType 在该接口是"搜索类型"枚举（综合搜索/主营产品），与企业主体
    # keywordType 不同；搜索模式默认"综合搜索"，address 为空时不传（接口不允许 None）。
    search: Any = {"_error": "未指定检索关键词，跳过渠道搜索"} if not search_keyword else _safe_call(
        T_SEARCH,
        {k: v for k, v in {
            "matchKeyword": search_keyword,
            "address": address,
            "keywordType": "综合搜索",
            "pageIndex": 1,
            "pageSize": page_size,
        }.items() if v is not None},
    )

    subject = build_subject(raw or (search_keyword or "渠道检索"), resolved, keyword_type, search_mode)
    core = build_core_analysis(analysis, search)
    metrics = build_metrics(analysis, search)
    _derive_core_metrics(metrics, core if isinstance(core, dict) else {})
    # --- Enterprise profile enrichment (from fuzzy_search) ---
    _enrich_metrics_with_profile(metrics, resolved.get("record") if isinstance(resolved, dict) else None)
    return _assemble(subject, core, metrics, dry_run=False, search_mode=search_mode)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Compose a factory channel analysis report via the channel MCP.")
    parser.add_argument("--enterprise", help="企业全称或关键词（企业渠道分析模式，关键词将自动模糊补全）")
    parser.add_argument("--keyword-type", default="name", help="主体类型：name/nameId/regNumber/socialCreditCode")
    parser.add_argument("--search", dest="search_keyword", help="渠道/供应商检索关键词（渠道检索模式）")
    parser.add_argument("--address", help="渠道检索地址过滤（配合 --search 使用）")
    parser.add_argument("--page-size", type=int, default=10, help="渠道搜索分页大小（最多 50）")
    parser.add_argument("--dry-run", action="store_true", help="不调用真实 MCP，使用样例数据组装报告骨架")
    parser.add_argument("--output", help="输出 JSON 路径；省略则打印到 stdout")
    parser.add_argument("--report-output", help="同时输出 HTML 报告（.html）与 Markdown 报告（.md）")
    parser.add_argument("--pdf-output", help="额外输出 PDF 报告（.pdf）；需要 Playwright + Chromium")
    args = parser.parse_args()

    if not args.enterprise and not args.dry_run and not args.search_keyword:
        parser.error("至少需要 --enterprise（企业渠道分析模式）或 --search（渠道检索模式）；或使用 --dry-run。")

    if args.dry_run:
        payload = build_dry_run_payload(args.enterprise or "示例科技有限公司", args.keyword_type)
    else:
        payload = build_payload(args.enterprise or "", args.keyword_type, args.search_keyword, args.address, args.page_size)

    if args.output:
        out = pathlib.Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json_dumps(payload, pretty=True), encoding="utf-8")
        print_json({"ok": True, "json": str(out), "dry_run": args.dry_run})
    else:
        print_json(payload)

    if args.report_output:
        base_out = pathlib.Path(args.report_output).expanduser()
        base_out.parent.mkdir(parents=True, exist_ok=True)
        html_path = base_out.with_suffix(".html") if base_out.suffix.lower() not in (".html", ".htm") else base_out
        md_path = html_path.with_suffix(".md")
        html_path.write_text(render_html(payload), encoding="utf-8")
        md_path.write_text(render_markdown(payload), encoding="utf-8")
        if args.pdf_output:
            pdf_path = pathlib.Path(args.pdf_output).expanduser()
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            html_to_pdf(render_html(payload), str(pdf_path))
        print_json({"ok": True, "html": str(html_path), "markdown": str(md_path), "pdf": str(pdf_path) if args.pdf_output else None, "dry_run": args.dry_run})


if __name__ == "__main__":
    main()
