#!/usr/bin/env python3
"""
生成项目衍生物：
  - DASHBOARD.md  各彩种最新一期开奖数据速览，方便排查数据问题
  - latest.json   各彩种最新一期记录汇总（LLM/调用方一次请求拿全）
  - index.json    数据清单：每彩种的文件、期数、最新期号、raw 下载地址

用法: python scripts/render_dashboard.py
"""

import json
import os
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
OUTPUT = os.path.join(REPO_ROOT, "DASHBOARD.md")
RAW_BASE = "https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main"

CST = timezone(timedelta(hours=8))

ORDER = ["ssq", "dlt", "sd", "pls", "plw", "qlc", "kl8", "qxc", "sfc", "jq4", "zc6"]

# 各彩种奖级名称（按 level 序号）
PRIZE_NAMES = {
    "ssq": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖"],
    "dlt": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖",
            "七等奖", "八等奖", "九等奖"],
    "sd":  ["直选", "组选三", "组选六"],
    "pls": ["直选", "组选三", "组选六"],
    "plw": ["一等奖"],
    "qlc": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖", "七等奖"],
    "qxc": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖"],
    "sfc": ["一等奖", "二等奖"],
    "jq4": ["一等奖"],
    "zc6": ["一等奖"],
    "kl8": [],
}

# 各彩种开奖日（用于判断数据是否过期）
DRAW_DAYS = {
    "ssq": "周二/四/日", "dlt": "周一/三/六", "sd": "每日", "pls": "每日",
    "plw": "每日", "qlc": "周一/三/五", "kl8": "每日", "qxc": "周二/五/日",
    "sfc": "赛期制", "jq4": "赛期制", "zc6": "赛期制",
}


def fmt_money(v) -> str:
    return f"{v:,}" if isinstance(v, (int, float)) else "-"


def fmt_nums(rec: dict) -> str:
    if "front" in rec:
        return " ".join(rec["front"]) + " | " + " ".join(rec["back"])
    return " ".join(rec.get("numbers", []))


def prize_name(code: str, level: int) -> str:
    names = PRIZE_NAMES.get(code, [])
    return names[level - 1] if level - 1 < len(names) else f"{level} 等奖"


def load(code: str) -> dict:
    p = os.path.join(DATA_DIR, f"{code}.json")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def render() -> str:
    now = datetime.now(CST)
    lines = [
        "# 开奖数据面板",
        "",
        f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}（北京时间） · ",
        "> 数据源：500彩票网 · 每日由 GitHub Actions 自动更新",
        "",
        "## 数据状态",
        "",
        "| 彩种 | 最新期号 | 开奖日期 | 开奖日 | 号码 | 总期数 | 详情覆盖 |",
        "|---|---|---|---|---|---|---|",
    ]

    sections = []
    for code in ORDER:
        payload = load(code)
        data = payload.get("data") or []
        if not data:
            lines.append(f"| {code} | - | - | - | **无数据** | 0 | - |")
            continue
        latest = data[-1]
        with_detail = sum(1 for r in data if r.get("prizes") or r.get("sales"))
        lines.append(
            f"| {payload.get('game', code)} | {latest['issue']} | {latest['date']} "
            f"| {DRAW_DAYS.get(code, '-')} | {fmt_nums(latest).replace(' | ', ' + ')} "
            f"| {len(data)} | {with_detail}/{len(data)} |"
        )

        sec = [f"### {payload.get('game', code)} · {latest['issue']} 期（{latest['date']}）",
               "", f"**号码：{fmt_nums(latest)}**", ""]
        if latest.get("zuxuan"):
            sec.append(f"- 组选形态：{latest['zuxuan']}")
        if latest.get("sales") is not None:
            sec.append(f"- 销售额：{fmt_money(latest['sales'])} 元")
        if latest.get("pool") is not None:
            sec.append(f"- 奖池滚存：{fmt_money(latest['pool'])} 元")
        if latest.get("prizes"):
            sec += ["", "| 奖级 | 单注奖金 | 中奖注数 |", "|---|---|---|"]
            for p in latest["prizes"]:
                sec.append(f"| {prize_name(code, p['level'])} "
                           f"| {fmt_money(p.get('money'))} | {fmt_money(p.get('count'))} |")
        sec += ["", f"上期：{data[-2]['issue']} {fmt_nums(data[-2])}（{data[-2]['date']}）"
                if len(data) > 1 else ""]
        sections.append("\n".join(sec).rstrip())

    lines += ["", "## 最新一期详情", ""]
    return "\n".join(lines) + "\n\n" + "\n\n".join(sections) + "\n"


def render_latest() -> dict:
    """各彩种最新一期记录汇总"""
    out = {"updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")}
    for code in ORDER:
        data = (load(code).get("data") or [])
        if data:
            out[code] = data[-1]
    return out


def render_index() -> dict:
    """数据清单：给搜索引擎 / LLM / 调用方的机器可读索引"""
    types = []
    for code in ORDER:
        payload = load(code)
        data = payload.get("data") or []
        if not data:
            continue
        types.append({
            "code": code,
            "name": payload.get("game"),
            "file": f"data/{code}.json",
            "url": f"{RAW_BASE}/data/{code}.json",
            "draws": len(data),
            "first_issue": data[0]["issue"],
            "first_date": data[0]["date"],
            "latest_issue": data[-1]["issue"],
            "latest_date": data[-1]["date"],
        })
    return {
        "name": "china-lottery-caipiao-data",
        "description": "Chinese lottery draw history: numbers, prize tiers, sales, pool. JSON, daily-updated.",
        "updated_at": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S"),
        "latest_url": f"{RAW_BASE}/latest.json",
        "types": types,
    }


def main():
    text = render()
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"written: {OUTPUT}")
    for name, payload in (("latest.json", render_latest()), ("index.json", render_index())):
        p = os.path.join(REPO_ROOT, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"written: {p}")


if __name__ == "__main__":
    main()
