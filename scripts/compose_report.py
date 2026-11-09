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
import copy
import datetime as dt
import json
import pathlib
import re as _re
from typing import Any, Dict, List, Mapping, Optional, Sequence

from common import (
    REPORT_BANNER,
    REPORT_TYPE,
    attach_pagination,
    call_tool_once,
    collect_detail_pages,
    json_dumps,
    load_json_file,
    paid_call_scope,
    print_json,
)
import mcp_client
from semantic_review import prepare_draft
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
        if value.get("_mcp_error") or value.get("_error") or value.get("isError") is True or value.get("error"):
            return True
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
    if isinstance(value, dict) and not _is_api_error(value):
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
        result = call_tool_once(mcp_client.call_tool, tool, arguments)
        if _payload_status(result) == "error":
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


def _payload_status(payload: Any) -> str:
    if _is_api_error(payload):
        return "error"
    if isinstance(payload, dict) and str(payload.get("text") or "").strip() == "查询数据为空":
        return "empty"
    if isinstance(payload, dict) and "text" in payload and not any(
        key in payload for key in ("resultList", "list", "items", "data", "total", "financialStat", "salesStat")
    ):
        return "error"
    if _first_list(payload) or _safe_total(payload) is not None:
        return "success" if (_first_list(payload) or _safe_total(payload) not in (0, "0")) else "empty"
    if isinstance(payload, dict) and payload:
        return "success"
    return "empty"


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
    fuzzy = _safe_call(T_FUZZY, {"matchKeyword": raw, "pageSize": 5})
    records = [r for r in _first_list(fuzzy) if isinstance(r, dict) and _text(r.get("name"))]
    total = _int(_safe_total(fuzzy))
    exact = [r for r in records if _text(r.get("name")).strip() == raw]
    if len(exact) == 1:
        record = exact[0]
        return {"keyword": raw, "enterprise": raw, "resolved": True, "reason": "模糊查询中存在唯一企业全称精确匹配", "fuzzy_total": total, "record": record, "fuzzy_requested": True}
    if len(records) == 1 and total == 1:
        record = records[0]
        return {"keyword": raw, "enterprise": _text(record.get("name")), "resolved": True, "reason": "模糊查询唯一候选补全", "fuzzy_total": total, "record": record, "fuzzy_requested": True}
    if records:
        return {
            "keyword": raw, "enterprise": raw, "resolved": False,
            "requires_confirmation": True,
            "reason": f"模糊查询存在多个候选（上游 total={total if total is not None else '未知'}），已停止主体分析",
            "fuzzy_total": total,
            "fuzzy_requested": True,
            "candidates": [_text(r.get("name")) for r in records[:5]],
        }
    return {"keyword": raw, "enterprise": raw, "resolved": False, "reason": "模糊查询未命中企业全称，按关键词直查", "fuzzy_requested": True}


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
    existing_labels = {str(metric.get("label")) for metric in metrics}
    if isinstance(analysis, dict) and analysis:
        peer_total = analysis.get("注册资本同行总数") or analysis.get("营收同行总数")
        if "同行企业总数" not in existing_labels and peer_total and str(peer_total) not in ("-", "", "0", "None"):
            metrics.append({"label": "同行企业总数", "value": str(peer_total), "hint": "行业同赛道企业总量"})
            existing_labels.add("同行企业总数")
        reg_range = analysis.get("注册资本区间")
        if "注册资本区间" not in existing_labels and reg_range and str(reg_range) not in ("-", "", "None"):
            metrics.append({"label": "注册资本区间", "value": str(reg_range), "hint": "行业注册资本区间定位"})
            existing_labels.add("注册资本区间")
        rev_range = analysis.get("营收区间")
        if "营收区间" not in existing_labels and rev_range and str(rev_range) not in ("-", "", "None"):
            metrics.append({"label": "营收区间", "value": str(rev_range), "hint": "行业营收区间定位"})
    return metrics


# --------------------------------------------------------------------------- #
# Section builders
# --------------------------------------------------------------------------- #

def build_subject(
    raw: str,
    resolved: Mapping[str, Any],
    keyword_type: str,
    search_mode: bool,
    enterprise_requested: Optional[bool] = None,
) -> Dict[str, Any]:
    has_enterprise = bool(enterprise_requested) if enterprise_requested is not None else bool(resolved.get("enterprise"))
    mode = "combined" if search_mode and has_enterprise else "search" if search_mode else "enterprise"
    return {
        "enterprise": resolved.get("enterprise") or raw,
        "matchKeyword": resolved.get("enterprise") or raw,
        "keywordType": keyword_type,
        "match_raw": raw,
        "resolved": bool(resolved.get("resolved")),
        "resolve_reason": resolved.get("reason", ""),
        "search_mode": search_mode,
        "mode": mode,
        "requires_confirmation": bool(resolved.get("requires_confirmation")),
        "candidates": list(resolved.get("candidates") or []),
        "fuzzy_requested": bool(resolved.get("fuzzy_requested")),
    }


def requested_products(subject: Mapping[str, Any], core: Optional[Mapping[str, Any]] = None) -> List[Dict[str, str]]:
    statuses_value = core.get("source_status") if isinstance(core, Mapping) else None
    statuses: Mapping[str, Any] = statuses_value if isinstance(statuses_value, Mapping) else {}
    products: List[Dict[str, str]] = []
    if subject.get("fuzzy_requested"):
        products.append({"name": "企业模糊查询", "product_id": "675cea1f0e009a9ea37edaa1"})
    if statuses.get("channel_analysis") not in (None, "not_requested", "requires_confirmation"):
        products.append({"name": "渠道分析", "product_id": "66f3d8bf64bd2be52d68a0fe"})
    if statuses.get("channel_search") not in (None, "not_requested"):
        products.append({"name": "渠道搜索", "product_id": "66b71b498dd25dbfbe8b0acd"})
    return products


def build_caliber(subject: Mapping[str, Any], search_mode: bool, core: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    mode = subject.get("mode") or ("search" if search_mode else "enterprise")
    product_names = [item["name"] for item in requested_products(subject, core)]
    if mode == "combined":
        match_target = subject.get("enterprise") or subject.get("match_raw")
        match_type = "组合查询：企业主体同行基准与渠道关键词/地址检索并行执行，两项结果和状态独立披露"
    elif mode == "search":
        match_target = subject.get("match_raw") or "渠道检索（无指定企业）"
        match_type = "渠道检索模式：按渠道关键词 / 地址检索渠道与供应商，与特定企业主体无关"
    else:
        match_target = subject.get("enterprise") or subject.get("match_raw")
        match_type = f"渠道分析按企业主体匹配（keywordType={subject.get('keywordType', 'name')}），并与同行对比；支持企业名称/注册号/统一社会信用代码/企业 id"
    if product_names == ["企业模糊查询"]:
        match_type = "仅执行企业模糊查询；主体未唯一确认，未调用渠道分析"
    sections = core.get("sections") if isinstance(core, Mapping) else None
    section_titles = [
        str(section.get("title")) for section in sections or []
        if isinstance(section, dict) and section.get("title")
    ]
    data_scope = "、".join(section_titles) if section_titles else "本次未形成有效分析章节"
    statuses_value = core.get("source_status") if isinstance(core, Mapping) else None
    statuses: Mapping[str, Any] = statuses_value if isinstance(statuses_value, Mapping) else {}
    if mode == "combined":
        search_note = "渠道检索受阻，未形成检索明细；" if statuses.get("channel_search") == "error" else "渠道检索仅为本次采集公开数据样本；"
        limit = f"企业同行基准与渠道检索两项并行、状态独立；{search_note}同行分位不等同于渠道结构，模糊主体仍需确认。"
    elif mode == "search":
        limit = "仅为渠道/供应商关键词检索本次采集样本，不包含企业同行基准；空结果或调用错误不构成企业分析结论。"
    else:
        limit = "企业分析实际为注册资本/营收同行基准，不等同于渠道结构；模糊名称存在多候选时必须确认主体后再调用。"
    return {
        "match_target": match_target,
        "match_type": match_type,
        "data_scope": data_scope,
        "products": product_names,
        "limit": limit,
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
    """Show the upstream ordinal rank without guessing which end is best."""
    r = _int(rank)
    t = _int(total)
    if r is None or not t or t <= 0:
        return None
    if r < 1 or r > t:
        return None
    return f"{r} / {t}"


def _trim_number(value: float) -> str:
    text = f"{value:,.2f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def _money_text(value: Any) -> str:
    """Normalise a capital string/dict without inventing a unit.

    ``1000.000000万人民币`` -> ``1,000 万人民币``;
    ``570707084.0 人民币`` -> ``5.71 亿 人民币``.
    """
    if isinstance(value, dict):
        if value.get("origin"):
            return _text(value.get("origin"))
        coin = _text(value.get("coinType"))
        raw_value = value.get("value")
    else:
        coin = ""
        raw_value = value
    if raw_value in (None, ""):
        return "-"
    raw = _text(raw_value)
    match = _re.match(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(亿|万)?\s*(.*)$", raw)
    if not match:
        return f"{raw} {coin}".strip()
    number = float(match.group(1))
    unit = match.group(2) or ""
    tail = match.group(3) or ""
    coin = coin or tail
    if unit:
        return f"{_trim_number(number)} {unit} {coin}".strip()
    if number >= 1e8:
        return f"{_trim_number(number / 1e8)} 亿 {coin}".strip()
    if number >= 1e4:
        return f"{_trim_number(number / 1e4)} 万 {coin}".strip()
    return f"{number:,.0f} {coin}".strip()


def _product_tag_summary(value: Any, keyword: str) -> tuple[str, Dict[str, Any]]:
    """Summarise upstream product tags while keeping the raw list in the row."""
    raw = _join_list(value) if isinstance(value, list) else _text(value)
    parts: List[str] = []
    seen = set()
    for part in _re.split(r"[、,，;；]", raw):
        tag = part.strip()
        if tag and tag not in seen:
            seen.add(tag)
            parts.append(tag)
    if not parts:
        return "", {"total": 0, "hits": 0, "others": 0}
    token = "".join(str(keyword or "").casefold().split())
    hits = [p for p in parts if token and token in "".join(p.casefold().split())]
    others = [p for p in parts if p not in hits]
    summary = f"上游标签 {len(parts)} 项"
    if hits:
        summary += f"，含关键词 {len(hits)} 项：{'、'.join(hits[:8])}"
    if others:
        summary += f"；其他标签 {len(others)} 项，如 {'、'.join(others[:4])}"
    if len(hits) > 8 or len(others) > 4:
        summary += "…"
    return summary, {"total": len(parts), "hits": len(hits), "others": len(others)}


def build_core_analysis(analysis: Any, search: Any, search_keyword: str = "") -> Dict[str, Any]:
    # 渠道分析 KV — 真实字段：financialStat.{categoryCount, regCapitalRank,
    # regCapitalScope} + salesStat.{categoryCount, annualTurnoverRank,
    # annualTurnoverScope}.
    analysis_kv: Dict[str, Any] = {}
    a = analysis if isinstance(analysis, dict) and "_error" not in analysis else {}
    fin_value = a.get("financialStat")
    sales_value = a.get("salesStat")
    fin: Dict[str, Any] = fin_value if isinstance(fin_value, dict) else {}
    sales: Dict[str, Any] = sales_value if isinstance(sales_value, dict) else {}
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
    token = "".join(str(search_keyword or "").casefold().split())
    for item in _first_list(search):
        if not isinstance(item, dict):
            continue
        raw_products = _join_list(item.get("mainProducts")) or "-"
        summary, tag_meta = _product_tag_summary(item.get("mainProducts"), search_keyword)
        name = _text(item.get("name")) or "-"
        search_rows.append({
            "渠道/供应商名称": name,
            "名称含关键词": "是" if token and token in "".join(name.casefold().split()) else "否",
            "主营产品": summary or "-",
            "主营产品原文": raw_products,
            "主营标签统计": tag_meta,
            "成立时间": _text(item.get("foundTime")) or "-",
            "注册资本": _money_text(item.get("regCapital")) or "-",
            "注册资本原文": _text(item.get("regCapital")) or "-",
        })

    sections: List[Dict[str, Any]] = []
    if analysis_kv:
        sections.append({"key": "channel_analysis", "title": "企业规模同行基准", "kind": "kv", "note": "注册资本 / 年营收在上游同行口径中的排名与区间；排名方向未说明，不代表渠道结构"})
    if search_rows or (isinstance(search, dict) and search.get("total") is not None):
        total = _safe_total(search)
        sections.append({"key": "channel_search", "title": "渠道/供应商明细", "kind": "table", "note": f"渠道/供应商记录 {total if total is not None else '若干'} 条，展示前 {len(search_rows)} 条；主营产品为上游标签摘要，原文保留在 JSON", "columns": [("渠道/供应商名称", "渠道/供应商名称"), ("名称含关键词", "名称含关键词"), ("主营产品（标签摘要）", "主营产品"), ("成立时间", "成立时间"), ("注册资本", "注册资本")]})

    return {
        "sections": sections,
        "channel_analysis": analysis_kv,
        "channel_search": search_rows,
        "source_status": {"channel_analysis": _payload_status(analysis), "channel_search": _payload_status(search)},
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


def build_insights(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    insights: List[Dict[str, Any]] = []
    metric_map = {m["label"]: str(m["value"]) for m in metrics}
    analysis_kv = core.get("channel_analysis") or {}

    if subject.get("search_mode"):
        search_total = metric_map.get("渠道/供应商")
        if search_total:
            insights.append({
                "feature": "渠道检索规模",
                "evidence": f"检索命中渠道/供应商 {search_total} 条。",
                "interpretation": "该数值仅是上游检索命中总数；不直接等同于供给密度、可合作数量或合格供应商数量。",
            })
        search_rows = core.get("channel_search") or []
        if search_rows:
            insights.append({
                "feature": "本次采集候选字段",
                "evidence": f"渠道/供应商明细 {len(search_rows)} 条。",
                "interpretation": "本次采集仅展示名称、主营产品摘要、成立时间与注册资本字段；未返回地址时不形成地域分布结论，也不据此认定优质或合格供应商。",
            })
            name_hits = sum(1 for row in search_rows if row.get("名称含关键词") == "是")
            tag_hits = sum(1 for row in search_rows if (row.get("主营标签统计") or {}).get("hits"))
            tag_only = sum(1 for row in search_rows if row.get("名称含关键词") == "否" and (row.get("主营标签统计") or {}).get("hits"))
            insights.append({
                "feature": "名称与主营标签命中",
                "evidence": f"本次展示 {len(search_rows)} 条中，名称含关键词 {name_hits} 条；主营标签含关键词 {tag_hits} 条，其中仅靠标签命中的 {tag_only} 条。",
                "interpretation": "名称或标签命中只说明关键词按字面出现在上游字段中；同义词（如 KUKA/库卡）与拆分词未合并，标签集合也常含跨行业词，不代表渠道商主营该产品，也不证明代理/授权关系。",
            })
    else:
        # 真实分析维度：上游只给序位排名，未给方向。
        cap_rank = analysis_kv.get("注册资本排名") or analysis_kv.get("注册资本分位") or metric_map.get("注册资本同行排名") or metric_map.get("注册资本分位")
        cap_scope = analysis_kv.get("注册资本区间") or metric_map.get("注册资本区间")
        if cap_rank or cap_scope:
            parts = []
            if cap_rank:
                parts.append(f"上游排名 {cap_rank}（上游未说明排名方向）")
            if cap_scope:
                parts.append(f"区间 {cap_scope}")
            insights.append({
                "feature": "注册资本同行位置",
                "evidence": "、".join(parts) + "。",
                "interpretation": "上游只返回序位数值且未说明排名方向；区间为最高档时，排名与区间的关系需向数据方核对，不解读为前/后百分比，也不等同于实际资金或履约能力。",
            })
        sales_rank = analysis_kv.get("营收排名") or analysis_kv.get("营收分位") or metric_map.get("营收同行排名") or metric_map.get("营收分位")
        sales_scope = analysis_kv.get("营收区间") or metric_map.get("营收区间")
        if sales_rank or sales_scope:
            parts = []
            if sales_rank:
                parts.append(f"上游排名 {sales_rank}（上游未说明排名方向）")
            if sales_scope:
                parts.append(f"区间 {sales_scope}")
            insights.append({
                "feature": "营收同行位置",
                "evidence": "、".join(parts) + "。",
                "interpretation": "上游只返回序位数值且未说明排名方向；该字段不等同于市场份额、销售网络或渠道能力。",
            })
        # 同行总数（行业体量）
        peer_total = analysis_kv.get("注册资本同行总数") or analysis_kv.get("营收同行总数")
        if peer_total:
            insights.append({
                "feature": "行业体量",
                "evidence": f"同行企业约 {peer_total} 家。",
                "interpretation": "同行总数仅是上游比较口径的样本规模，不直接证明赛道竞争强度或排名价值。",
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
    fin_value = a.get("financialStat")
    sales_value = a.get("salesStat")
    fin: Dict[str, Any] = fin_value if isinstance(fin_value, dict) else {}
    sales: Dict[str, Any] = sales_value if isinstance(sales_value, dict) else {}

    # 真实结构：financialStat / salesStat 各含 categoryCount(同行总数)、rank、scope
    fin_rank = _int(fin.get("regCapitalRank"))
    fin_total = _int(fin.get("categoryCount"))
    sales_rank = _int(sales.get("annualTurnoverRank"))
    sales_total = _int(sales.get("categoryCount"))

    if fin_rank is not None and fin_total and fin_total > 0:
        full_rank = _rank_pct(fin_rank, fin_total)
        short_rank = full_rank.split("（", 1)[0].strip() if full_rank else None
        metrics.append({"label": "注册资本同行排名", "value": short_rank, "hint": "上游序位，未说明排名方向", "delta": f"排名 {fin_rank}/{fin_total}"})
    if fin.get("regCapitalScope"):
        metrics.append({"label": "注册资本区间", "value": _text(fin.get("regCapitalScope")), "hint": "注册资本规模区间"})
    if sales_rank is not None and sales_total and sales_total > 0:
        full_rank = _rank_pct(sales_rank, sales_total)
        short_rank = full_rank.split("（", 1)[0].strip() if full_rank else None
        metrics.append({"label": "营收同行排名", "value": short_rank, "hint": "上游序位，未说明排名方向", "delta": f"排名 {sales_rank}/{sales_total}"})
    if sales.get("annualTurnoverScope"):
        metrics.append({"label": "营收区间", "value": _text(sales.get("annualTurnoverScope")), "hint": "年营收规模区间"})
    if isinstance(search, dict) and search.get("total") is not None:
        total = _safe_total(search)
        if total is None:
            total = len(_first_list(search))
        metrics.append({"label": "渠道/供应商", "value": _text(total), "hint": "渠道搜索命中数"})
    return [m for m in metrics if m.get("value") not in ("", None, "-")]


def build_abstract(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: Sequence[Mapping[str, Any]]) -> str:
    mode = subject.get("mode") or ("search" if subject.get("search_mode") else "enterprise")
    status_value = core.get("source_status")
    statuses: Mapping[str, Any] = status_value if isinstance(status_value, dict) else {}
    analysis_status = statuses.get("channel_analysis")
    search_status = statuses.get("channel_search")
    if mode == "combined":
        name = subject.get("enterprise") or subject.get("match_raw") or "目标企业"
        parts = [f"本报告以“{name}”为企业主体，并行执行企业规模同行基准与渠道关键词检索。"]
        if analysis_status == "success":
            parts.append("企业规模同行基准已返回。")
        elif analysis_status == "empty":
            parts.append("企业规模同行基准调用成功但结果为空。")
        else:
            parts.append("企业规模同行基准未形成有效结果。")
        if search_status == "success":
            parts.append(f"渠道检索已返回本次采集 {len(core.get('channel_search') or [])} 条明细。")
        elif search_status == "empty":
            parts.append("渠道检索调用成功但结果为空。")
        elif search_status == "error":
            parts.append("渠道检索调用受阻，未形成检索明细。")
        else:
            parts.append("渠道检索未形成有效结果。")
    elif mode == "search":
        name = subject.get("match_raw") or "目标渠道"
        parts = [f"本报告以“{name}”为检索范围，呈现渠道/供应商检索结果及其状态。"]
        if search_status == "error":
            parts.append("渠道检索调用受阻，未形成检索明细。")
        elif search_status == "empty":
            parts.append("渠道检索调用成功但结果为空。")
        else:
            parts.append(f"本次展示 {len(core.get('channel_search') or [])} 条；主营产品为上游标签摘要，命中不等于代理或授权关系。")
    else:
        name = subject.get("enterprise") or subject.get("match_raw") or "目标企业"
        if subject.get("requires_confirmation"):
            parts = [f"“{name}”的模糊查询存在多个企业候选；本报告已停止主体分析，需确认企业全称或 ID。"]
        else:
            parts = [f"本报告以“{name}”为分析对象，呈现注册资本与营收同行基准；该产品不提供企业渠道结构证据。"]
    if metrics:
        kv = "、".join(f"{m['label']} {m['value']}" for m in metrics[:5])
        parts.append(f"关键指标包括：{kv}。")
    if mode in ("search", "combined"):
        parts.append("检索结果仅为公开数据样本；错误、空结果或待确认主体不计入有效覆盖。")
    else:
        parts.append("同行排名与区间仅按上游口径展示；未说明排名方向时不做前/后百分比解读。")
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
    return apply_content_review(_assemble(subject, core, metrics, dry_run=True, search_mode=bool(subject.get("search_mode"))))


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #

def _quality_report(core: Mapping[str, Any]) -> Dict[str, Any]:
    """Section-fill rate from final declared sections and their actual bodies.

    ``0`` is a populated body; None/''/[]/{} is empty. Not an accuracy score.
    """
    ca = core if isinstance(core, dict) else {}
    sections = ca.get("sections")
    if isinstance(sections, list):
        total = len(sections)
        populated = sum(1 for s in sections if isinstance(s, dict) and ca.get(s.get("key")) not in (None, "", [], {}))
    else:
        keys = [k for k in ca if k not in ("sections", "source_status")]
        total = len(keys)
        populated = sum(1 for k in keys if ca.get(k) not in (None, "", [], {}))
    return {
        "total_sections": total,
        "populated_sections": populated,
        "empty_sections": total - populated,
        "coverage_pct": round(populated / max(1, total) * 100),
    }


def _assemble(subject: Mapping[str, Any], core: Mapping[str, Any], metrics: Sequence[Mapping[str, Any]], *, dry_run: bool, search_mode: bool = False) -> Dict[str, Any]:
    abstract = build_abstract(subject, core, metrics)
    records = build_records(core)
    insights = build_insights(subject, core, metrics)
    ca = core if isinstance(core, dict) else {}
    status_value = ca.get("source_status")
    statuses: Dict[str, Any] = status_value if isinstance(status_value, dict) else {}
    quality_report = _quality_report(core)
    populated = quality_report["populated_sections"]
    if populated == 0:
        import sys
        print("⚠️ 质量门禁警告: 所有核心分析维度均无数据", file=sys.stderr)
    mode = subject.get("mode") or ("search" if search_mode else "enterprise")
    status_values = [value for value in statuses.values() if value != "not_requested"]
    partial = "success" in status_values and any(value != "success" for value in status_values)
    if mode == "combined":
        report_label = "企业同行基准与渠道检索组合报告" + ("（部分成功）" if partial else "")
    elif mode == "search":
        report_label = "渠道检索报告"
    else:
        report_label = "企业规模同行基准报告"
    title = f"{subject.get('enterprise') or subject.get('match_raw') or '目标'} {report_label}"
    return {
        "report_type": REPORT_TYPE,
        "title": title,
        "banner": REPORT_BANNER,
        "subject": dict(subject),
        "abstract": abstract,
        "summary": abstract,
        "executive_summary": [item["interpretation"] for item in insights][:5] or [abstract[:120]],
        "metrics": list(metrics),
        "caliber": build_caliber(subject, search_mode, core),
        "core_analysis": dict(core),
        "representative_records": records,
        "insights": insights,
        "data_source": {
            "mcp_server": "factory-channel-mcp-server",
            "products": requested_products(subject, core),
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "dry_run": dry_run,
            "quality_report": quality_report,
            "source_status": core.get("source_status", {}),
            "mode": mode,
        },
    }


def _neutral_rank(value: Any) -> Optional[str]:
    """Convert an old '后 0.02%（排名 433897/433988）' string to a neutral rank."""
    text = _text(value)
    match = _re.search(r"(\d+)\s*/\s*(\d+)", text)
    if match:
        return f"{match.group(1)} / {match.group(2)}"
    if text and text != "-":
        return f"{text}（上游未说明方向）"
    return None


def _review_channel_analysis(kv: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(kv)
    for old_key, new_key in (("注册资本分位", "注册资本排名"), ("营收分位", "营收排名")):
        if old_key in out:
            neutral = _neutral_rank(out.pop(old_key))
            if neutral:
                out[new_key] = neutral
    return out


def _review_metrics(metrics: Sequence[Mapping[str, Any]], kv: Mapping[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for raw in metrics:
        if not isinstance(raw, dict):
            continue
        metric = dict(raw)
        label = str(metric.get("label") or "")
        if label in ("注册资本分位", "营收分位"):
            source = kv.get("注册资本排名" if label == "注册资本分位" else "营收排名")
            neutral = _neutral_rank(metric.get("delta")) or _neutral_rank(source) or _neutral_rank(metric.get("value"))
            label = "注册资本同行排名" if label == "注册资本分位" else "营收同行排名"
            metric["value"] = neutral or metric.get("value")
            metric["hint"] = "上游序位，未说明排名方向"
        metric["label"] = label
        if label in seen:
            continue
        seen.add(label)
        out.append(metric)
    return out


def _review_search_rows(rows: Sequence[Mapping[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    token = "".join(str(keyword or "").casefold().split())
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        raw_products = row.get("主营产品原文") or row.get("主营产品") or "-"
        if isinstance(raw_products, list):
            raw_products = _join_list(raw_products) or "-"
        row["主营产品原文"] = raw_products
        existing_summary = str(row.get("主营产品") or "")
        existing_meta = row.get("主营标签统计")
        if str(raw_products).strip() in ("", "-"):
            summary, meta = "", {"total": 0, "hits": 0, "others": 0}
        elif existing_summary.startswith("上游标签") and isinstance(existing_meta, dict):
            # Already organised by the current normal generator or a prior
            # review: keep its summary instead of re-tokenising it.
            summary, meta = existing_summary, existing_meta
        else:
            summary, meta = _product_tag_summary(raw_products, keyword)
        row["主营产品"] = summary or "-"
        row["主营标签统计"] = meta
        name = str(row.get("渠道/供应商名称") or "")
        row["名称含关键词"] = "是" if token and token in "".join(name.casefold().split()) else "否"
        old_cap = str(row.get("注册资本") or "")
        if old_cap and old_cap != "-" and "注册资本原文" not in row:
            row["注册资本原文"] = old_cap
            row["注册资本"] = _money_text(old_cap) or "-"
        out.append(row)
    return out


def apply_content_review(report: Mapping[str, Any], *, source_sha256: Optional[str] = None,
                         reviewed_at: Optional[str] = None) -> Dict[str, Any]:
    """Rebuild factory-channel narrative content offline from an existing payload.

    Uses only fields already present. No MCP call, no new facts. Fixes:
    * a rank converted to "前/后 X%" although the upstream never states the
      ranking direction (BYD's top-bucket capital was rendered as bottom 0.02%);
    * raw upstream tag dumps presented as product lists, with six-decimal
      capital strings;
    * keyword hits in names/tags left unmarked, making a supplier search look
      like a verified channel relationship.
    """
    out = copy.deepcopy(dict(report))
    subject = dict(out.get("subject") or {})
    ds = dict(out.get("data_source") or {})
    core = dict(out.get("core_analysis") or {})
    keys = [s.get("key") for s in core.get("sections", []) if isinstance(s, dict)]
    if not keys:
        keys = [key for key in core if key not in {"sections", "source_status"}]
    has_body = any(core.get(key) not in (None, "", [], {}) for key in keys)
    if subject.get("requires_confirmation") or not has_body:
        ds["quality_report"] = _quality_report(out.get("core_analysis") or {})
        ds["content_revision"] = {
            "mode": "offline_source_preserving",
            "source_sha256": source_sha256,
            "original_generated_at": ds.get("generated_at"),
            "reviewed_at": reviewed_at or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "scope": ("主体存在多候选：保留原停止说明，不重算业务结论"
                      if subject.get("requires_confirmation") else
                      "无有效业务章节：保留原始空结果或调用失败说明，不生成业务结论"),
        }
        out["data_source"] = ds
        return out
    keyword = str(subject.get("search_keyword") or subject.get("match_raw") or subject.get("matchKeyword") or "")
    kv = _review_channel_analysis(core.get("channel_analysis") or {})
    core["channel_analysis"] = kv
    core["channel_search"] = _review_search_rows(core.get("channel_search") or [], keyword)
    sections = []
    for spec in core.get("sections") or []:
        if isinstance(spec, dict):
            spec = dict(spec)
            if spec.get("key") == "channel_search":
                spec["columns"] = [("渠道/供应商名称", "渠道/供应商名称"), ("名称含关键词", "名称含关键词"),
                                   ("主营产品（标签摘要）", "主营产品"), ("成立时间", "成立时间"),
                                   ("注册资本", "注册资本")]
                note = str(spec.get("note") or "")
                if "主营产品为上游标签摘要" not in note:
                    spec["note"] = note + "；主营产品为上游标签摘要，原文保留在 JSON"
            elif spec.get("key") == "channel_analysis":
                note = str(spec.get("note") or "")
                if not note or "分位" in note:
                    spec["note"] = "注册资本 / 年营收在上游同行口径中的排名与区间；排名方向未说明，不代表渠道结构"
        sections.append(spec)
    core["sections"] = sections
    metrics = _review_metrics(out.get("metrics") or [], kv)
    insights = build_insights(subject, core, metrics)
    abstract = build_abstract(subject, core, metrics)
    old_abstract = str(out.get("abstract") or "")
    marker = "明细含未完整采集的来源"
    if marker in old_abstract:
        # attach_pagination() appends this disclosure after the review; keep it
        # when an already-attached report is reviewed again offline.
        abstract += old_abstract[old_abstract.index(marker):]
    out["core_analysis"] = core
    out["metrics"] = metrics
    out["insights"] = insights
    out["abstract"] = abstract
    out["summary"] = abstract
    out["executive_summary"] = [i.get("interpretation") for i in insights][:5] or [abstract[:120]]
    out["representative_records"] = build_records(core)
    ds["quality_report"] = _quality_report(core)
    ds["content_revision"] = {
        "mode": "offline_source_preserving",
        "source_sha256": source_sha256,
        "original_generated_at": ds.get("generated_at"),
        "reviewed_at": reviewed_at or dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope": "撤销无依据的前/后分位；标签摘要化并保留原文；规范注册资本；标注名称/标签命中；未新增查询",
    }
    out["data_source"] = ds
    return out


@paid_call_scope
def build_payload(raw: str, keyword_type: str, search_keyword: Optional[str], address: Optional[str], page_size: int, max_pages: int = 1) -> Dict[str, Any]:
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or max_pages < 1:
        raise ValueError("max_pages 必须为正整数")
    search_mode = bool(search_keyword)
    resolved = resolve_enterprise_name(raw) if raw else {"enterprise": "", "resolved": False, "reason": "未指定企业（渠道检索模式）"}
    enterprise = resolved.get("enterprise") or raw

    if not raw:
        analysis: Any = {"_error": "未指定企业，跳过渠道分析"}
    elif resolved.get("requires_confirmation"):
        analysis = {"_error": "requires_confirmation"}
    else:
        analysis = _safe_call(T_ANALYSIS, {"matchKeyword": enterprise, "keywordType": keyword_type})

    # 渠道搜索：keywordType 在该接口是"搜索类型"枚举（综合搜索/主营产品），与企业主体
    # keywordType 不同；搜索模式默认"综合搜索"，address 为空时不传（接口不允许 None）。
    # 分页按 total 驱动、在 max_pages 预算内翻页（pageIndex 由 collect_detail_pages 管理）。
    search: Any = {"_error": "未指定检索关键词，跳过渠道搜索"}
    if search_keyword:
        search_args = {k: v for k, v in {
            "matchKeyword": search_keyword,
            "address": address,
            "keywordType": "综合搜索",
            "pageSize": page_size,
        }.items() if v is not None}
        search = collect_detail_pages(_safe_call, T_SEARCH, search_args,
                                      get_rows=_first_list, get_total=_safe_total, is_error=_is_api_error,
                                      max_pages=max_pages)

    subject = build_subject(
        raw or (search_keyword or "渠道检索"),
        resolved,
        keyword_type,
        search_mode,
        enterprise_requested=bool(raw),
    )
    if search_keyword:
        # Keep the search keyword distinct from the enterprise name so offline
        # review can re-check name/tag hits in combined mode.
        subject["search_keyword"] = search_keyword
    core = build_core_analysis(analysis, search, search_keyword or "")
    core["source_status"] = {
        "channel_analysis": "requires_confirmation" if resolved.get("requires_confirmation") else _payload_status(analysis) if raw else "not_requested",
        "channel_search": _payload_status(search) if search_keyword else "not_requested",
    }
    metrics = build_metrics(analysis, search)
    _derive_core_metrics(metrics, core if isinstance(core, dict) else {})
    # --- Enterprise profile enrichment (from fuzzy_search) ---
    if not resolved.get("requires_confirmation"):
        _enrich_metrics_with_profile(metrics, resolved.get("record") if isinstance(resolved, dict) else None)
    report = apply_content_review(_assemble(subject, core, metrics, dry_run=False, search_mode=search_mode))
    return attach_pagination(report, {"渠道/供应商搜索": search})


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
    parser.add_argument("--max-pages", type=int, default=1, help="渠道搜索明细付费调用页数上限，默认1；先按 total 估算，只有必要且已授权时提高")
    parser.add_argument("--dry-run", action="store_true", help="不调用真实 MCP，使用样例数据组装报告骨架")
    parser.add_argument("--output", help="输出 JSON 路径；省略则打印到 stdout")
    parser.add_argument("--report-output", help="同时输出 HTML 报告（.html）与 Markdown 报告（.md）")
    parser.add_argument("--pdf-output", help="额外输出 PDF 报告（.pdf）；需要 Playwright + Chromium")
    args = parser.parse_args()

    if not args.enterprise and not args.dry_run and not args.search_keyword:
        parser.error("至少需要 --enterprise（企业渠道分析模式）或 --search（渠道检索模式）；或使用 --dry-run。")

    if args.max_pages is not None and args.max_pages < 1:
        parser.error("--max-pages 必须为正整数")

    if args.dry_run:
        payload = build_dry_run_payload(args.enterprise or "示例科技有限公司", args.keyword_type)
    else:
        payload = build_payload(args.enterprise or "", args.keyword_type, args.search_keyword, args.address, args.page_size, args.max_pages)

    payload = prepare_draft(payload)

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
