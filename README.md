# china-lottery-caipiao-data

[![update-lottery-data](https://github.com/terry2010/china-lottery-caipiao-data/actions/workflows/update.yml/badge.svg)](https://github.com/terry2010/china-lottery-caipiao-data/actions/workflows/update.yml)
[![last commit](https://img.shields.io/github/last-commit/terry2010/china-lottery-caipiao-data)](https://github.com/terry2010/china-lottery-caipiao-data/commits)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

中国**全部 11 种彩票**的开奖历史数据集：开奖号码 + **各奖级中奖注数 + 单注奖金 + 销售额 + 奖池滚存**，JSON 格式，GitHub Actions 每日自动更新。

Daily-updated dataset of all 11 Chinese lottery games — draw numbers, **prize-tier winning counts, per-tier prize money, total sales and pool rollover** — as free JSON, updated daily by GitHub Actions. No API key, no auth.

## 数据面板 / Dashboard

👉 **[在线数据站](https://terry2010.github.io/china-lottery-caipiao-data/)** — 最新一期开奖速览，带分享功能（GitHub Pages，每日随数据更新）
👉 **[DASHBOARD.md](DASHBOARD.md)** — 仓库内的 Markdown 版速览

## 快速使用 / Quick start

```bash
# 所有彩种最新一期（一次请求）
curl https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main/latest.json

# 双色球完整历史
curl https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main/data/ssq.json

# 数据清单（机器可读索引，含每期数/最新期号/下载地址）
curl https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main/index.json
```

```python
import pandas as pd, requests
d = requests.get("https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main/data/ssq.json").json()
df = pd.DataFrame(d["data"])   # 3531 行：issue, date, front, back, prizes, sales, pool
```

## 覆盖彩种 / Coverage

| 代码 | 彩种 | Game | 起始 | 开奖日 | 文件 |
|---|---|---|---|---|---|
| `ssq` | 双色球 | Union Lotto | 2003 | 周二/四/日 | `data/ssq.json` |
| `dlt` | 超级大乐透 | Super Lotto | 2007 | 周一/三/六 | `data/dlt.json` |
| `sd` | 福彩3D | Welfare 3D | 2004 | 每日 | `data/sd.json` |
| `pls` | 排列3 | Arrangement 3 | 2004 | 每日 | `data/pls.json` |
| `plw` | 排列5 | Arrangement 5 | 2004 | 每日 | `data/plw.json` |
| `qlc` | 七乐彩 | Seven Lottery | 2007 | 周一/三/五 | `data/qlc.json` |
| `kl8` | 快乐8 | Happy 8 | 2021 | 每日 | `data/kl8.json` |
| `qxc` | 七星彩 | Seven Stars | 2004 | 周二/五/日 | `data/qxc.json` |
| `sfc` | 胜负彩14场 | Football 14 | 2004 | 赛期制 | `data/sfc.json` |
| `jq4` | 四场进球 | 4-Game Goals | 2006 | 赛期制 | `data/jq4.json` |
| `zc6` | 六场半全场 | 6-Game HT/FT | 2006 | 赛期制 | `data/zc6.json` |

## 数据格式 / Schema

```json
{
  "game": "双色球", "code": "ssq", "updated_at": "2026-11-22 23:00:00",
  "data": [{
    "issue": "2026134", "date": "2026-11-22",
    "front": ["04","05","10","17","21","32"], "back": ["08"],
    "sales": 435713586, "pool": 1154982023,
    "prizes": [{"level": 1, "money": 6115183, "count": 13}]
  }]
}
```

- `front`/`back`：前后区彩种；其他彩种为 `numbers` 数组
- `prizes[].level` 1=一等奖，`money` 单注奖金（元），`count` 中奖注数
- `sales` 本期销售额（元）；`pool` 奖池滚存（元）

## FAQ

**Q: 有中奖人数/购买人数数据吗？**
A: 中国彩票官方从不公布购买人数。最接近的指标是 `sales`（销售额）和 `prizes[].count`（各奖级中奖注数）。

**Q: 福彩3D 的中奖注数为什么是 0？**
A: 上游源约 2022 年起不再更新 3D 注数字段；之前年份正常。销售额全期可用。

**Q: 快乐8 没有分奖级数据？**
A: 上游仅提供快乐8 的销量与奖池，无分奖级注数。

**Q: 更新频率？**
A: 每日 22:40（北京时间）由 GitHub Actions 抓取，开奖日 21:15–21:30 开奖后更新。

**Q: 如何回补全量历史详情？**
A: Actions → `update-lottery-data` → Run workflow → 勾 `backfill`，可断点续跑。

## 数据来源与免责声明

- 源：[500彩票网](https://www.500.com) 公开开奖 XML（官方 `cwl.gov.cn` / `webapi.sporttery.cn` 对境外 IP 不可用）
- 仅聚合公开数据用于学习研究，不构成购彩建议；开奖结果随机，历史数据无法预测未来

## License

MIT
