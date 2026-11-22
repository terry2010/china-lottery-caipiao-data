#!/usr/bin/env python3
"""
中国彩票开奖数据抓取脚本
数据源：500彩票网 XML 接口
  - 列表: https://www.500.com/static/info/kaijiang/xml/{code}/list.xml
  - 详情: https://www.500.com/static/info/kaijiang/xml/{code}/{issue}.xml

输出 data/{code}.json，格式:
  {"game": "...", "code": "ssq", "updated_at": "...",
   "data": [{"issue": "...", "date": "...", "numbers"/"front"/"back": [...],
             "sales": int, "pool": int, "prizes": [{"level":1,"money":0,"count":0}]}]}

用法:
  python scripts/fetch_lottery.py                 # 增量更新（最近 --details 期补详情）
  python scripts/fetch_lottery.py --type ssq dlt  # 只更新指定彩种
  python scripts/fetch_lottery.py --details 200   # 补齐最近 200 期的详情
  python scripts/fetch_lottery.py --full          # 全量回补所有期的详情
"""

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")

BASE = "https://www.500.com/static/info/kaijiang/xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://www.500.com/",
}

# split="|" 表示 opencode 用 | 分隔前后区；n 为号码个数（校验用，0 表示不校验）
LOTTERIES = {
    "ssq": {"name": "双色球", "split": "|", "pad": True, "full_issue": True},
    "dlt": {"name": "超级大乐透", "split": "|", "pad": True},
    "sd":  {"name": "福彩3D", "pad": False},
    "pls": {"name": "排列3", "pad": False},
    "plw": {"name": "排列5", "pad": False},
    "qlc": {"name": "七乐彩", "split": "|", "pad": True, "full_issue": True},
    "kl8": {"name": "快乐8", "pad": True, "n": 20},
    "qxc": {"name": "七星彩", "pad": False},
    "sfc": {"name": "胜负彩14场", "pad": False, "n": 14},
    "jq4": {"name": "四场进球", "pad": False, "n": 8},
    "zc6": {"name": "六场半全场", "pad": False, "n": 12},
}

CST = timezone(timedelta(hours=8))


def now_cst() -> str:
    return datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")


def get(url: str, retries: int = 3) -> str:
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and r.text.strip():
                r.encoding = "utf-8"
                return r.text
            print(f"    HTTP {r.status_code} {url}，重试 {i + 1}/{retries}")
        except Exception as e:
            print(f"    {e}，重试 {i + 1}/{retries}")
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"fetch failed: {url}")


def norm_issue(code: str, expect: str) -> str:
    """福彩官方期号为 7 位 YYYYNNN，5 位时补 20 前缀；体彩保持原样"""
    if LOTTERIES[code].get("full_issue") and len(expect) == 5:
        return "20" + expect
    return expect


def parse_opencode(code: str, opencode: str) -> dict:
    cfg = LOTTERIES[code]
    pad = (lambda s: s.strip().zfill(2)) if cfg.get("pad") else (lambda s: s.strip())
    if cfg.get("split") == "|" and "|" in opencode:
        a, b = opencode.split("|", 1)
        return {"front": [pad(x) for x in a.split(",")], "back": [pad(x) for x in b.split(",")]}
    nums = [pad(x) for x in opencode.replace("|", ",").split(",") if x.strip()]
    if cfg.get("n") and len(nums) != cfg["n"]:
        return {}
    return {"numbers": nums}


def fetch_list(code: str) -> list:
    """返回 [{issue, expect, date, numbers/front/back}]，最新在前"""
    text = get(f"{BASE}/{code}/list.xml")
    rows = re.findall(
        r'<row\s+expect="(\d+)"\s+opencode="([^"]*)"\s+opentime="([^"]*)"', text)
    out = []
    for expect, opencode, opentime in rows:
        rec = parse_opencode(code, opencode)
        if not rec:
            continue
        rec["issue"] = norm_issue(code, expect)
        rec["expect"] = expect  # 详情页 URL 用原始期号
        rec["date"] = opentime.split(" ")[0]
        out.append(rec)
    return out


def to_int(s: str):
    s = (s or "").replace(",", "").strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def fetch_detail(code: str, expect: str) -> dict:
    """抓详情页，返回 {prizes, sales, pool, extra}；无数据返回 {}"""
    text = get(f"{BASE}/{code}/{expect}.xml")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {}
    fields = {e.tag: (e.text or "").strip() for e in root}

    prizes = []
    for i in range(1, 20):
        money, count = to_int(fields.get(f"Money{i}")), to_int(fields.get(f"Num{i}"))
        if money is None and count is None:
            break
        prizes.append({"level": i, "money": money, "count": count})

    detail = {}
    if prizes:
        detail["prizes"] = prizes
    for key in ("TotalMoney", "CCMoney", "PoolMoney", "AddCCMoney"):
        v = to_int(fields.get(key))
        if v:
            detail.setdefault("sales" if key == "TotalMoney" else "pool", v)
    if fields.get("ZuxuanType"):
        detail["zuxuan"] = fields["ZuxuanType"]
    return detail


def data_path(code: str) -> str:
    return os.path.join(DATA_DIR, f"{code}.json")


def load_data(code: str) -> dict:
    p = data_path(code)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"game": LOTTERIES[code]["name"], "code": code, "data": []}


def save_data(code: str, payload: dict):
    payload["updated_at"] = now_cst()
    with open(data_path(code), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


def update_one(code: str, details: int, full: bool):
    cfg = LOTTERIES[code]
    print(f"\n=== {cfg['name']} ({code}) ===")
    rows = fetch_list(code)
    print(f"  列表 {len(rows)} 期，最新 {rows[0]['issue']} {rows[0]['date']}")

    payload = load_data(code)
    by_issue = {r["issue"]: r for r in payload["data"]}

    new_count = 0
    for row in rows:  # 列表全量合并（号码维度）
        issue = row["issue"]
        merged = dict(row)
        merged.pop("expect")
        if issue in by_issue:  # 保留已抓到的详情字段
            old = by_issue[issue]
            for k in ("prizes", "sales", "pool", "zuxuan"):
                if k in old:
                    merged[k] = old[k]
        else:
            new_count += 1
        by_issue[issue] = merged

    ordered = sorted(by_issue.values(), key=lambda r: int(r["issue"]))
    payload["data"] = ordered

    # 详情回补：最近 details 期 + 所有缺详情的期(full)
    need = [r for r in ordered if "prizes" not in r and "sales" not in r]
    if not full:
        need = [r for r in need if int(r["issue"]) >= int(ordered[-min(details, len(ordered))]["issue"])]
    print(f"  新增 {new_count} 期；需补详情 {len(need)} 期")

    ok, fail = 0, 0
    for r in need:
        expect = (r["issue"][-5:]
                  if cfg.get("full_issue") and len(r["issue"]) == 7 else r["issue"])
        try:
            d = fetch_detail(code, expect)
        except Exception as e:
            print(f"    详情失败 {r['issue']}: {e}")
            fail += 1
            continue
        r.update(d)
        ok += 1
        if ok % 50 == 0:
            print(f"    详情进度 {ok}/{len(need)}")
        time.sleep(0.15)

    if fail and ok == 0:
        print("  详情全部失败，跳过写盘")
        return
    save_data(code, payload)
    print(f"  已写入 {len(ordered)} 期（详情 {ok} 成功 / {fail} 失败）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", nargs="+", choices=LOTTERIES.keys())
    ap.add_argument("--details", type=int, default=90, help="补齐最近 N 期详情，默认 90")
    ap.add_argument("--full", action="store_true", help="回补所有缺失详情")
    args = ap.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    codes = args.type or list(LOTTERIES)
    for code in codes:
        try:
            update_one(code, args.details, args.full)
        except Exception as e:
            print(f"!! {code} 更新失败: {e}")
    print("\nDone.")


if __name__ == "__main__":
    main()
