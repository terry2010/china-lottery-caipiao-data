#!/usr/bin/env python3
"""
生成 GitHub Pages 站点 docs/index.html（自包含单页，无外部依赖）。
数据在构建期内嵌进 HTML，打开即用；每彩种带分享按钮（复制开奖文本/链接、
微博、X、系统分享）。

用法: python scripts/render_site.py
"""

import json
import os
import shutil
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
OUT_DIR = os.path.join(REPO_ROOT, "docs")
OUT = os.path.join(OUT_DIR, "index.html")

CST = timezone(timedelta(hours=8))
SITE_URL = "https://terry2010.github.io/china-lottery-caipiao-data/"
RAW_BASE = "https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main"

ORDER = ["ssq", "dlt", "sd", "pls", "plw", "qlc", "kl8", "qxc", "sfc", "jq4", "zc6"]

DRAW_DAYS = {
    "ssq": "周二/四/日", "dlt": "周一/三/六", "sd": "每日", "pls": "每日",
    "plw": "每日", "qlc": "周一/三/五", "kl8": "每日", "qxc": "周二/五/日",
    "sfc": "赛期制", "jq4": "赛期制", "zc6": "赛期制",
}

# 号码球配色：ball=红球蓝球样式，digit=数字方块样式
DISPLAY = {
    "ssq": "balls", "dlt": "balls", "qlc": "balls", "kl8": "balls",
    "sd": "digits", "pls": "digits", "plw": "digits", "qxc": "digits",
    "sfc": "chips", "jq4": "chips", "zc6": "chips",
}

PRIZE_NAMES = {
    "ssq": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖"],
    "dlt": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖",
            "七等奖", "八等奖", "九等奖"],
    "sd": ["直选", "组选三", "组选六"],
    "pls": ["直选", "组选三", "组选六"],
    "plw": ["一等奖"],
    "qlc": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖", "七等奖"],
    "qxc": ["一等奖", "二等奖", "三等奖", "四等奖", "五等奖", "六等奖"],
    "sfc": ["一等奖", "二等奖"],
    "jq4": ["一等奖"], "zc6": ["一等奖"], "kl8": [],
}


def fmt(v):
    return f"{v:,}" if isinstance(v, (int, float)) else "-"


def load(code):
    p = os.path.join(DATA_DIR, f"{code}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def nums_html(code, rec):
    kind = DISPLAY[code]
    if "front" in rec:
        front = "".join(f'<span class="ball red">{n}</span>' for n in rec["front"])
        back = "".join(f'<span class="ball blue">{n}</span>' for n in rec["back"])
        return f'<div class="nums">{front}<span class="sep"></span>{back}</div>'
    nums = rec.get("numbers", [])
    if kind == "balls":
        return '<div class="nums">' + "".join(
            f'<span class="ball red">{n}</span>' for n in nums) + "</div>"
    if kind == "digits":
        return '<div class="nums">' + "".join(
            f'<span class="digit">{n}</span>' for n in nums) + "</div>"
    return '<div class="nums chips">' + "".join(
        f'<span class="chip">{n}</span>' for n in nums) + "</div>"


def nums_text(rec):
    if "front" in rec:
        return " ".join(rec["front"]) + " + " + " ".join(rec["back"])
    return " ".join(rec.get("numbers", []))


def prize_table(code, rec):
    names = PRIZE_NAMES.get(code, [])
    rows = "".join(
        f"<tr><td>{names[p['level']-1] if p['level']-1 < len(names) else str(p['level'])+'等奖'}</td>"
        f"<td class='r'>{fmt(p.get('money'))}</td><td class='r'>{fmt(p.get('count'))}</td></tr>"
        for p in rec.get("prizes", []))
    if not rows:
        return ""
    return ("<table class='prize'><thead><tr><th>奖级</th>"
            "<th class='r'>单注奖金(元)</th><th class='r'>中奖注数</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>")


def card(code, payload, latest_for_js):
    data = payload.get("data") or []
    if not data:
        return ""
    r = data[-1]
    total, covered = len(data), sum(1 for x in data if x.get("prizes") or x.get("sales"))
    meta = []
    if r.get("sales") is not None:
        meta.append(f"销售额 <b>{fmt(r['sales'])}</b> 元")
    if r.get("pool") is not None:
        meta.append(f"奖池 <b>{fmt(r['pool'])}</b> 元")
    if r.get("zuxuan"):
        meta.append(f"组选形态 <b>{r['zuxuan']}</b>")
    meta_s = " · ".join(meta)
    return f"""
<section class="card" id="{code}">
  <header>
    <h2>{payload.get('game', code)}<span class="code">{code}</span></h2>
    <span class="acts"><button class="share" data-img="{code}" title="生成分享图片">🖼</button>
    <button class="share" data-game="{code}" title="分享本彩种">↗ 分享</button></span>
  </header>
  <div class="issue">第 <b>{r['issue']}</b> 期 · {r['date']} · {DRAW_DAYS.get(code,'')}</div>
  {nums_html(code, r)}
  <div class="meta">{meta_s}</div>
  {prize_table(code, r)}
  <div class="foot">共 {total} 期 · 详情覆盖 {covered}/{total} ·
    <a href="{RAW_BASE}/data/{code}.json">JSON ↗</a></div>
</section>"""


HTML = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中国彩票开奖数据 · 每日自动更新 | china-lottery-caipiao-data</title>
<meta name="description" content="中国全部11种彩票开奖历史数据：双色球、大乐透、福彩3D、排列3/5、七乐彩、快乐8、七星彩、胜负彩、四场进球、六场半全场。含中奖注数、单注奖金、销售额、奖池。JSON免费下载，每日自动更新。">
<meta property="og:type" content="website">
<meta property="og:title" content="中国彩票开奖数据 · 最新一期速览">
<meta property="og:description" content="11种彩票开奖号码+中奖注数+奖金+销量+奖池，JSON数据集每日自动更新">
<meta property="og:url" content="__SITE_URL__">
<meta property="og:image" content="https://opengraph.githubassets.com/1/terry2010/china-lottery-caipiao-data">
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1f2329;--sub:#6b7280;--red:#d92b2b;--blue:#1f6feb;--line:#e5e7eb}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:16px}
header.top{position:sticky;top:0;background:#fffffff2;backdrop-filter:blur(8px);border-bottom:1px solid var(--line);z-index:9}
header.top .wrap{display:flex;align-items:center;gap:10px;padding-top:10px;padding-bottom:10px}
h1{font-size:19px;flex:1}
h1 small{color:var(--sub);font-weight:400;font-size:13px}
.btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer;color:var(--ink)}
.btn:hover{background:#f0f2f5}
.updated{color:var(--sub);font-size:12.5px;margin:10px 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:14px}
@media(max-width:420px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card:target{border-color:var(--blue);box-shadow:0 0 0 2px #1f6feb22}
.card header{display:flex;align-items:center;justify-content:space-between}
.card h2{font-size:17px}
.card h2 .code{color:var(--sub);font-size:11px;font-weight:400;margin-left:6px;background:#f0f2f5;padding:1px 6px;border-radius:6px}
.share{border:1px solid var(--blue);color:var(--blue);background:#fff;border-radius:8px;padding:4px 10px;font-size:12.5px;cursor:pointer}
.share:hover{background:#1f6feb;color:#fff}
.acts{display:flex;gap:6px}
.issue{color:var(--sub);font-size:13px;margin:6px 0 8px}
.nums{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0 8px}
.ball{width:30px;height:30px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;color:#fff}
.ball.red{background:radial-gradient(circle at 30% 30%,#f66,var(--red))}
.ball.blue{background:radial-gradient(circle at 30% 30%,#6ea8ff,var(--blue))}
.sep{width:8px}
.digit{width:26px;height:32px;border:1px solid var(--line);border-bottom:3px solid var(--red);border-radius:5px;display:inline-flex;align-items:center;justify-content:center;font-weight:700;background:#fff}
.chips .chip{border:1px solid var(--line);border-radius:6px;padding:2px 7px;font-weight:700;background:#fff}
.meta{font-size:13px;color:var(--sub);margin:6px 0}
.prize{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
.prize th{text-align:left;color:var(--sub);font-weight:400;border-bottom:1px solid var(--line);padding:4px 2px}
.prize td{border-bottom:1px solid #f2f3f5;padding:4px 2px}
.prize .r{text-align:right}
.card .foot{margin-top:10px;font-size:12px;color:var(--sub)}
.card .foot a{color:var(--blue);text-decoration:none}
.notice{background:#fffbe8;border:1px solid #f0e0a8;border-radius:10px;padding:10px 14px;font-size:13px;color:#7a6514;margin-bottom:14px}
footer{color:var(--sub);font-size:12.5px;margin:22px 0 30px;line-height:1.9}
footer a{color:var(--blue);text-decoration:none}
#toast{position:fixed;left:50%;bottom:40px;transform:translateX(-50%);background:#111827;color:#fff;padding:8px 16px;border-radius:8px;font-size:13px;opacity:0;transition:opacity .25s;pointer-events:none;z-index:99}
#toast.show{opacity:.95}
#imgModal{position:fixed;inset:0;background:#000a;display:none;align-items:center;justify-content:center;z-index:100;padding:18px}
#imgModal.open{display:flex}
#imgModal .box{background:#fff;border-radius:16px;padding:16px;max-width:400px;width:100%;max-height:92vh;overflow-y:auto;text-align:center;position:relative}
#imgModal .x{position:absolute;top:10px;right:12px;border:0;background:none;font-size:18px;color:#9ca3af;cursor:pointer}
#imgModal .x:hover{color:#1f2329}
#imgPreview{width:100%;border-radius:10px;border:1px solid var(--line);display:block}
#imgModal .siteinfo{margin:12px 0 4px;font-size:13px;color:var(--sub);line-height:1.5}
#imgModal .siteinfo b{color:var(--ink);font-size:14px}
#imgModal .siteinfo .url{color:var(--blue);font-size:12px;word-break:break-all}
#qr{width:130px;height:130px;margin:8px auto 2px;display:block;border-radius:8px}
#imgModal .qrtext{font-size:11.5px;color:var(--sub);margin-bottom:12px}
#imgModal .row{display:flex;gap:8px;margin-top:8px}
#imgModal .row .share{flex:1;padding:9px 0;font-size:13.5px}
#menu{position:fixed;inset:0;background:#0008;display:none;align-items:flex-end;justify-content:center;z-index:98}
#menu.open{display:flex}
#menu .sheet{background:#fff;width:100%;max-width:480px;border-radius:14px 14px 0 0;padding:14px 16px 26px}
#menu .sheet button{display:block;width:100%;text-align:left;background:none;border:0;border-bottom:1px solid #f2f3f5;padding:13px 4px;font-size:15px;cursor:pointer}
#menu .sheet button:last-child{border-bottom:0}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>中国彩票开奖数据 <small>每日自动更新</small></h1>
  <a class="btn" href="https://github.com/terry2010/china-lottery-caipiao-data" target="_blank" rel="noopener">GitHub ↗</a>
  <button class="btn" id="shareTop">↗ 分享</button>
</div></header>
<div class="wrap">
  <p class="updated">更新于 <b id="updated">__UPDATED__</b>（北京时间） · 数据源 500.com ·
    <a href="https://github.com/terry2010/china-lottery-caipiao-data" style="color:var(--blue)" target="_blank" rel="noopener">GitHub 项目 ↗</a></p>
  <div class="notice">数据仅供研究学习，不构成购彩建议。开奖结果随机，历史数据无法预测未来。</div>
  <div class="grid">__CARDS__</div>
  <footer>
    开源数据集（JSON 每日更新）：<a href="https://github.com/terry2010/china-lottery-caipiao-data">terry2010/china-lottery-caipiao-data</a> · MIT License<br>
    已知限制：快乐8 无分奖级数据；福彩3D 约 2022 年起中奖注数缺失；官方不公布购买人数。
  </footer>
</div>
<div id="toast"></div>
<div id="imgModal"><div class="box">
  <button class="x" id="imgClose" title="关闭">✕</button>
  <img id="imgPreview" alt="开奖分享图">
  <div class="siteinfo"><b>中国彩票开奖数据</b><br>
    <span class="url" id="siteUrl"></span><br>扫码查看全部彩种</div>
  <img id="qr" alt="站点二维码" onerror="this.style.display='none'">
  <div class="qrtext">微信/相机扫码访问</div>
  <div class="row">
    <button class="share" id="imgDl">⬇ 下载图片</button>
    <button class="share" id="imgShare">↗ 分享图片</button>
  </div>
</div></div>
<div id="menu"><div class="sheet">
  <button data-act="image">🖼 生成分享图片</button>
  <button data-act="copyText">📋 复制开奖结果文本</button>
  <button data-act="copyLink">🔗 复制本页链接</button>
  <button data-act="weibo">微博分享</button>
  <button data-act="x">分享到 X</button>
  <button data-act="native">系统分享…</button>
  <button data-act="close" style="color:#999">取消</button>
</div></div>
<script>
const SITE = "__SITE_URL__";
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const toast = m => { const t = $("#toast"); t.textContent = m; t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 1800); };
const copy = async t => { try { await navigator.clipboard.writeText(t); toast("已复制"); }
  catch { const ta = document.createElement("textarea"); ta.value = t;
    document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove(); toast("已复制"); } };
const fmt = v => (typeof v === "number") ? v.toLocaleString() : "-";
const nums = r => r.front ? r.front.join(" ") + " + " + r.back.join(" ") : (r.numbers || []).join(" ");
function shareText(code) {
  const g = DATA.games[code]; if (!g) return SITE;
  const r = g.latest; let s = `【${g.name}】第${r.issue}期 ${r.date} 开奖：${nums(r)}`;
  const p1 = (r.prizes || [])[0];
  if (p1) s += `｜一等奖 ${p1.count} 注，单注 ${fmt(p1.money)} 元`;
  if (r.sales) s += `｜销量 ${fmt(r.sales)} 元`;
  return s + `｜${SITE}#${code}`;
}
/* ---------- 分享图片生成 ---------- */
function rr(x, a, b, w, h, r){ x.beginPath(); x.moveTo(a+r,b); x.arcTo(a+w,b,a+w,b+h,r);
  x.arcTo(a+w,b+h,a,b+h,r); x.arcTo(a,b+h,a,b,r); x.arcTo(a,b,a+w,b,r); x.closePath(); }
function ball(x, cx, cy, n, color){ const g = x.createRadialGradient(cx-6,cy-7,2,cx,cy,19);
  g.addColorStop(0, color === "#d92b2b" ? "#ff7b7b" : "#7eb0ff"); g.addColorStop(1, color);
  x.fillStyle = g; x.beginPath(); x.arc(cx,cy,19,0,7); x.fill();
  x.fillStyle = "#fff"; x.font = "bold 15px sans-serif"; x.textAlign = "center";
  x.textBaseline = "middle"; x.fillText(n, cx, cy+1); x.textAlign = "left"; x.textBaseline = "alphabetic"; }
function digitBox(x, a, y, n){ rr(x, a, y-26, 34, 40, 6); x.fillStyle = "#fff"; x.fill();
  x.strokeStyle = "#e5e7eb"; x.lineWidth = 1.5; x.stroke();
  x.fillStyle = "#d92b2b"; x.fillRect(a, y+8, 34, 3);
  x.fillStyle = "#1f2329"; x.font = "bold 20px sans-serif"; x.textAlign = "center";
  x.textBaseline = "middle"; x.fillText(n, a+17, y-6); x.textAlign = "left"; x.textBaseline = "alphabetic"; }
async function shareImage(code){
  const g = DATA.games[code] || DATA.games.ssq, r = g.latest;
  const W = 880, P = 40;
  const allNums = r.front ? r.front.concat(r.back) : (r.numbers || []);
  const useBalls = !!r.front || allNums.some(n => String(n).length > 1);
  const rows = Math.ceil(allNums.length / (useBalls ? 11 : 16));
  const prizes = r.prizes || [];
  const metaH = (r.sales || r.pool) ? 40 : 0;
  const H = P*2 + 96 + rows*60 + metaH + (prizes.length ? 52 + prizes.length*38 : 0) + 64;
  const c = document.createElement("canvas"); c.width = W*2; c.height = H*2;
  const x = c.getContext("2d"); x.scale(2, 2);
  x.fillStyle = "#eef1f6"; x.fillRect(0, 0, W, H);
  rr(x, P, P, W-2*P, H-2*P, 16); x.fillStyle = "#fff"; x.fill();
  x.strokeStyle = "#e5e7eb"; x.lineWidth = 1; x.stroke();
  let y = P + 44;
  x.fillStyle = "#1f2329"; x.font = "bold 30px 'PingFang SC','Microsoft YaHei',sans-serif";
  x.fillText(g.name, P+26, y);
  x.fillStyle = "#6b7280"; x.font = "15px sans-serif"; x.textAlign = "right";
  x.fillText("第 " + r.issue + " 期", W-P-26, y); x.textAlign = "left";
  y += 32; x.fillText("开奖日期 " + r.date, P+26, y); y += 44;
  if (r.front) {
    let cx = P+26+19;
    r.front.forEach(n => { ball(x, cx, y-8, n, "#d92b2b"); cx += 46; });
    cx += 20;
    r.back.forEach(n => { ball(x, cx, y-8, n, "#1f6feb"); cx += 46; });
  } else if (useBalls) {
    let cx = P+26+19, col = 0;
    allNums.forEach(n => { ball(x, cx, y-8, n, "#d92b2b"); cx += 46;
      if (++col === 11) { col = 0; cx = P+26+19; y += 60; } });
  } else {
    let dx = P+26, col = 0;
    allNums.forEach(n => { digitBox(x, dx, y, n); dx += 42;
      if (++col === 16) { col = 0; dx = P+26; y += 52; } });
  }
  y += 34;
  if (r.sales || r.pool) {
    x.fillStyle = "#6b7280"; x.font = "14px sans-serif";
    let s = "";
    if (r.sales) s += "销售额 " + fmt(r.sales) + " 元";
    if (r.pool) s += (s ? "　·　" : "") + "奖池 " + fmt(r.pool) + " 元";
    x.fillText(s, P+26, y); y += 40;
  }
  if (prizes.length) {
    const names = {1:"一等奖",2:"二等奖",3:"三等奖",4:"四等奖",5:"五等奖",6:"六等奖",7:"七等奖",8:"八等奖",9:"九等奖"};
    const zh = {sd:["直选","组选三","组选六"], pls:["直选","组选三","组选六"]}[code];
    x.font = "14px sans-serif"; x.fillStyle = "#9ca3af";
    x.fillText("奖级", P+26, y); x.textAlign = "right";
    x.fillText("单注奖金(元)", W/2+120, y); x.fillText("中奖注数", W-P-26, y); x.textAlign = "left";
    y += 8; x.strokeStyle = "#e5e7eb"; x.beginPath(); x.moveTo(P+26,y); x.lineTo(W-P-26,y); x.stroke(); y += 30;
    prizes.forEach(p => { x.fillStyle = "#1f2329"; x.font = "14px sans-serif";
      x.fillText((zh && zh[p.level-1]) || names[p.level] || (p.level + "等奖"), P+26, y);
      x.textAlign = "right"; x.fillText(fmt(p.money), W/2+120, y); x.fillText(fmt(p.count), W-P-26, y);
      x.textAlign = "left"; y += 38; });
  }
  x.fillStyle = "#9ca3af"; x.font = "13px sans-serif"; y = H - P + 8;
  x.fillText(SITE.replace("https://","") + " · 每日自动更新 · 仅供研究", P+26, y);
  // 填充弹层：预览图 + 站点信息 + 二维码
  $("#imgPreview").src = c.toDataURL("image/png");
  $("#siteUrl").textContent = SITE.replace("https://","");
  $("#qr").style.display = "";
  $("#qr").src = "https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=4&data="
    + encodeURIComponent(SITE + "#" + code);
  $("#imgModal").classList.add("open");
  c.toBlob(b => { imgFile = new File([b], `${code}-${r.issue}.png`, {type: "image/png"}); }, "image/png");
}
let imgFile = null;
$("#imgClose").onclick = () => $("#imgModal").classList.remove("open");
$("#imgModal").addEventListener("click", e => { if (e.target.id === "imgModal") e.target.classList.remove("open"); });
$("#imgDl").onclick = () => { if (!imgFile) return;
  const a = document.createElement("a"); a.href = URL.createObjectURL(imgFile); a.download = imgFile.name;
  a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 3000); toast("图片已下载"); };
$("#imgShare").onclick = async () => { if (!imgFile) return;
  if (navigator.canShare && navigator.canShare({files: [imgFile]})) {
    try { await navigator.share({files: [imgFile]}); return; } catch(e) { if (e.name === "AbortError") return; }
  }
  const a = document.createElement("a"); a.href = URL.createObjectURL(imgFile); a.download = imgFile.name;
  a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 3000); toast("已下载，可粘贴分享"); };
let current = "";
function openMenu(code){ current = code || ""; $("#menu").classList.add("open"); }
$("#menu").addEventListener("click", e => { if (e.target.id === "menu" || e.target.dataset.act === "close")
  $("#menu").classList.remove("open"); });
document.querySelectorAll("[data-game]").forEach(b => b.onclick = () => openMenu(b.dataset.game));
document.querySelectorAll("[data-img]").forEach(b => b.onclick = () => shareImage(b.dataset.img));
$("#shareTop").onclick = () => openMenu("");
document.querySelectorAll("#menu button").forEach(b => b.onclick = async () => {
  const act = b.dataset.act, url = SITE + (current ? "#" + current : ""), text = shareText(current || "ssq");
  if (act === "image") shareImage(current || "ssq");
  else if (act === "copyText") copy(text);
  else if (act === "copyLink") copy(url);
  else if (act === "weibo") open("https://service.weibo.com/share/share.php?title=" + encodeURIComponent(text), "_blank");
  else if (act === "x") open("https://twitter.com/intent/tweet?text=" + encodeURIComponent(text), "_blank");
  else if (act === "native") { if (navigator.share) { try { await navigator.share({text, url}); } catch {} } else copy(text); }
  $("#menu").classList.remove("open");
});
</script>
</body>
</html>"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cards, latest_js = [], {}
    for code in ORDER:
        payload = load(code)
        data = payload.get("data") or []
        if not data:
            continue
        cards.append(card(code, payload, None))
        latest_js[code] = {"name": payload.get("game", code), "latest": data[-1]}

    html = (HTML
            .replace("__SITE_URL__", SITE_URL)
            .replace("__RAW_BASE__", RAW_BASE)
            .replace("__UPDATED__", datetime.now(CST).strftime("%Y-%m-%d %H:%M"))
            .replace("__CARDS__", "\n".join(cards))
            .replace("__DATA__", json.dumps({"games": latest_js}, ensure_ascii=False)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"written: {OUT} ({len(html)//1024}KB)")

    # 站点的 mini-API：复制轻量索引文件进 docs/（大文件 data/*.json 用 raw URL）
    for name in ("latest.json", "index.json"):
        src = os.path.join(REPO_ROOT, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT_DIR, name))
            print(f"copied: docs/{name}")


if __name__ == "__main__":
    main()
