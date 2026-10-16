"""Komut satiri.

  python -m cqsim simulate --year 2022 --policy carbonqueue   -> results/2022-carbonqueue.json
  python -m cqsim all                                         -> butun yillar x politikalar + results/summary.md
  python -m cqsim rank                                        -> results/live-queue.json (canli kuyruk)
  python -m cqsim sensitivity                                 -> results/sensitivity.json + sensitivity.md
  python -m cqsim serve                                       -> backend icin kuyruk motoru, http://127.0.0.1:9002
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from cqsim import live, sensitivity
from cqsim.metrics import summarize
from cqsim.prepare import DATA, ROOT, build_queue, lane_shares, load_config
from cqsim.simulator import POLICIES, calibrate, simulate

YEARS = range(2019, 2024)


def run_year(year: int, policies, cfg: dict, data: Path, out: Path) -> dict:
    q = build_queue(year, cfg, data)
    start = pd.Timestamp(year, 1, 1)
    cal = calibrate(q, cfg, start)
    capacity = cal["capacity_hours_per_week"]
    fifo = simulate(q, "fifo", cfg, start, capacity)
    unscored, small = lane_shares(q, cfg)
    results = {}
    for policy in policies:
        res = fifo if policy == "fifo" else simulate(q, policy, cfg, start, capacity)
        results[policy] = {
            "year": year, "policy": policy,
            "calibration": cal,
            "lane_share": {"unscored": round(unscored, 3), "small_quota": round(small, 3)},
            "assumptions": cfg,
            **summarize(q, res, fifo, cfg, year),
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
    sub.add_parser("sensitivity")
    sub.add_parser("serve").add_argument("--port", type=int, default=9002)
    sub.add_parser("rank").add_argument("--include-stale", action="store_true",
                                        help="stale_or_uncertain dosyalari da siraya koy (varsayilan: ayri listede)")
    for s in sub.choices.values():
        s.add_argument("--data", type=Path, default=DATA)
        s.add_argument("--out", type=Path, default=ROOT / "results")
        s.add_argument("--config", type=Path, default=None)
    args = p.parse_args()
    cfg = load_config(args.config)

    if args.cmd == "simulate":
        r = run_year(args.year, [args.policy], cfg, args.data, args.out)[args.policy]
        print(json.dumps({k: v for k, v in r.items() if k != "assumptions"}, ensure_ascii=False, indent=1))
    elif args.cmd == "rank":
        r = live.rank(cfg, args.data, args.include_stale)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "live-queue.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"as_of={r['as_of']}  kapasite={r['calibration']['capacity_hours_per_week']} saat/hafta  dosya={len(r['files'])}"
              f"  teyit bekleyen={len(r['needs_confirmation'])}  kademeler={r['lane_counts']}")
        for f in r["files"][:15]:
            print(f"{f['position']['carbonqueue']:>4}  {f['site_name'][:34]:<34}  {f['reason']}")
    elif args.cmd == "serve":
        from cqsim.server import serve
        serve(args.port, cfg)
    elif args.cmd == "sensitivity":
        rows = sensitivity.run(cfg, args.data)
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "sensitivity.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        (args.out / "sensitivity.md").write_text(sensitivity.table(rows), encoding="utf-8")
        print(sensitivity.table(rows))
    else:
        res = {y: run_year(y, list(POLICIES), cfg, args.data, args.out) for y in YEARS}
        table = summary_table(res)
        (args.out / "summary.md").write_text(table, encoding="utf-8")
        print(table)
