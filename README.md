# china-lottery-caipiao-data

中国彩票开奖数据自动采集仓库 · Daily-updated draw history for all Chinese lotteries — draw numbers, prize tiers (中奖注数/单注奖金), sales (销售额) and pool (奖池滚存), stored as JSON and updated daily by GitHub Actions.

## 数据面板

👉 **[DASHBOARD.md](DASHBOARD.md)** — 各彩种最新一期开奖数据速览

## 覆盖彩种

| 代码 | 彩种 | 开奖日 | 数据文件 |
|---|---|---|---|
| `ssq` | 双色球 | 周二/四/日 | `data/ssq.json` |
| `dlt` | 超级大乐透 | 周一/三/六 | `data/dlt.json` |
| `sd` | 福彩3D | 每日 | `data/sd.json` |
| `pls` | 排列3 | 每日 | `data/pls.json` |
| `plw` | 排列5 | 每日 | `data/plw.json` |
| `qlc` | 七乐彩 | 周一/三/五 | `data/qlc.json` |
| `kl8` | 快乐8 | 每日 | `data/kl8.json` |
| `qxc` | 七星彩 | 周二/五/日 | `data/qxc.json` |
| `sfc` | 胜负彩14场 | 赛期制 | `data/sfc.json` |
| `jq4` | 四场进球 | 赛期制 | `data/jq4.json` |
| `zc6` | 六场半全场 | 赛期制 | `data/zc6.json` |

## 数据格式

```json
{
  "game": "双色球",
  "code": "ssq",
  "updated_at": "2026-11-22 23:00:00",
  "data": [
    {
      "issue": "2026134",
      "date": "2026-11-22",
      "front": ["04", "05", "10", "17", "21", "32"],
      "back": ["08"],
      "sales": 435713586,
      "pool": 1154982023,
      "prizes": [
        {"level": 1, "money": 6115183, "count": 13},
        {"level": 2, "money": 102382, "count": 177}
      ]
    }
  ]
}
```

- `front`/`back`：前后区彩种（双色球、大乐透、七乐彩）；其他彩种用 `numbers`
- `prizes[].level`：奖级序号（1=一等奖），`money` 单注奖金（元），`count` 中奖注数
- `sales` 本期销售额（元），`pool` 奖池滚存（元）
- 已知限制：快乐8 无分奖级注数；福彩3D/排列3 的注数字段源站常为空；排列5 奖池在 `pool`（取自源 AddCCMoney 字段）

## 直接使用

```
https://raw.githubusercontent.com/terry2010/china-lottery-caipiao-data/main/data/ssq.json
```

## 本地运行

```bash
pip install -r requirements.txt
python scripts/fetch_lottery.py            # 增量更新
python scripts/fetch_lottery.py --full     # 回补全部历史详情（慢）
python scripts/render_dashboard.py         # 生成 DASHBOARD.md
```

## 数据来源与免责声明

- 数据源：[500彩票网](https://www.500.com) 公开开奖接口（官方接口 `cwl.gov.cn` / `webapi.sporttery.cn` 对境外 IP 均有限制，GitHub Actions 不可用）
- 本项目仅聚合公开数据用于学习研究，不构成任何购彩建议；彩票开奖结果随机，历史数据无法预测未来

## License

MIT
