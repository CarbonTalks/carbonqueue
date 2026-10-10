"""Komut satiri.

  python -m cqsim simulate --year 2022 --policy carbonqueue   -> results/2022-carbonqueue.json
  python -m cqsim all                                         -> butun yillar x politikalar + results/summary.md
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from cqsim.metrics import summarize
from cqsim.prepare import DATA, ROOT, build_queue, lane_shares, load_config, weekly_capacity
from cqsim.simulator import POLICIES, simulate

YEARS = range(2019, 2024)


def run_year(year: int, policies, cfg: dict, data: Path, out: Path) -> dict:
    q = build_queue(year, cfg, data)
    start = pd.Timestamp(year, 1, 1)
    fifo = simulate(q, "fifo", cfg, start)
    unscored, small = lane_shares(q, cfg)
    results = {}
    for policy in policies:
        res = fifo if policy == "fifo" else simulate(q, policy, cfg, start)
        results[policy] = {
            "year": year, "policy": policy,
            "capacity_hours_per_week": round(weekly_capacity(q, cfg), 1),
            "lane_share": {"unscored": round(unscored, 3), "small_quota": round(small, 3)},
            "assumptions": cfg,
            **summarize(q, res, fifo, cfg),
        }
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{year}-{policy}.json").write_text(json.dumps(results[policy], ensure_ascii=False, indent=1), encoding="utf-8")
    return results


def summary_table(all_results: dict) -> str:
    rows = ["| Yıl | Politika | Kazanç tCO₂ (α=0,5; düşük–merkezi–yüksek) | Medyan bekleme | P90 | Küçük proje medyan | Küçük proje P90 "
            "| Azami beklemeyi aşan | Geri çekilene harcanan saat |", "|---|---|---|---|---|---|---|---|---|"]
    for year, by_policy in all_results.items():
        for policy, r in by_policy.items():
            g = r["carbon_gain_tco2_vs_fifo"].get("alpha_0.5", {})
            w, s = r["wait_days"]["all"], r["wait_days"]["small_scored"]
            rows.append(
                f"| {year} | {policy} | {g.get('low', 0):,.0f} – {g.get('central', 0):,.0f} – {g.get('high', 0):,.0f} "
                f"| {w['median']:.0f} | {w['p90']:.0f} | {s.get('median', float('nan')):.0f} | {s.get('p90', float('nan')):.0f} "
                f"| %{100 * r['over_max_wait_share']:.1f} | {r['wasted_hours_on_withdrawn']:.0f} |")
    return "\n".join(rows) + "\n"


if __name__ == "__main__":
    p = argparse.ArgumentParser(prog="cqsim")
    sub = p.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("simulate")
    one.add_argument("--year", type=int, required=True)
    one.add_argument("--policy", choices=list(POLICIES), required=True)
    sub.add_parser("all")
    for s in sub.choices.values():
        s.add_argument("--data", type=Path, default=DATA)
        s.add_argument("--out", type=Path, default=ROOT / "results")
        s.add_argument("--config", type=Path, default=None)
    args = p.parse_args()
    cfg = load_config(args.config)

    if args.cmd == "simulate":
        r = run_year(args.year, [args.policy], cfg, args.data, args.out)[args.policy]
        print(json.dumps({k: v for k, v in r.items() if k != "assumptions"}, ensure_ascii=False, indent=1))
    else:
        res = {y: run_year(y, list(POLICIES), cfg, args.data, args.out) for y in YEARS}
        table = summary_table(res)
        (args.out / "summary.md").write_text(table, encoding="utf-8")
        print(table)
