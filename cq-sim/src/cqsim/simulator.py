"""Haftalik adimli kuyruk simulatoru. Butun politikalar ayni kapasite ve ayni efor kuraliyla kosar.

Gercek tarihler yalnizca iki seyi belirler: dosyanin kuyruga ne zaman girdigi ve sonucunun ne oldugu.
Karar tarihleri simulasyondan cikar; politikalar birbiriyle karsilastirilir, gercek tarihlerle degil.

Kurallar:
- Tek Ingiltere havuzu: kurum basina dosya sayisi cok dusuk oldugu icin ortak bir uzman havuzu varsayilir.
- Geri cekilen (ve redsiz temyize giden) dosya, gercek cikis tarihine kadar incelenmediyse o tarihte kuyruktan
  cikar. Daha once sirasi gelirse eforu harcar; karbon katkisi her durumda sifirdir.
- Skorsuz dosyalar (depolama, biyoenerji, kapasitesi eksik) kapasitenin efor paylari kadarini alir ve
  kendi icinde basvuru tarihine gore ilerler: ne one alinir ne geriye itilir.
"""
import numpy as np
import pandas as pd

from cqsim.prepare import lane_shares, naive_capacity, score

WEEK = np.timedelta64(7, "D")
# politika -> (geri cekilme carpani, efora bolme, adalet kademeleri); fifo ayri ele alinir
POLICIES = {
    "fifo": None,
    "carbon": (False, False, False),
    "carbon_withdrawal": (True, False, False),
    "carbon_withdrawal_effort": (True, True, False),
    "carbonqueue": (True, True, True),
}


def calibrate(q: pd.DataFrame, cfg: dict, start: pd.Timestamp) -> dict:
    """Haftalik kapasiteyi, FIFO simulasyonundaki medyan bekleme gercek medyan karar suresine esit olacak sekilde bulur.

    Karsilastirma ayni dosyalar uzerinde yapilir: kurumun gercekte karar verdigi dosyalar. Yalnizca medyan
    eslestirilir; P90 kalibrasyona girmez ve simulasyonun gercegi ne kadar tuttugunu gosteren kontrol olarak raporlanir.
    """
    decided = q.real_days.notna().to_numpy()
    real = q.real_days[decided]
    base = naive_capacity(q)

    def fifo_wait(factor):
        res = simulate(q, "fifo", cfg, start, base * factor)
        return (res.done - q.arrival).dt.days[decided]

    lo, hi = 0.25, 16.0  # bekleme kapasiteyle azalir: ikiye bolerek ara
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fifo_wait(mid).median() > real.median() else (lo, mid)
    wait = fifo_wait(hi)
    return {
        "capacity_hours_per_week": round(base * hi * cfg["simulation"]["capacity_factor"], 1),
        "naive_capacity_hours_per_week": round(base, 1),
        "calibration_factor": round(hi, 3),
        "real_wait_median": float(real.median()), "fifo_wait_median": float(wait.median()),
        "real_wait_p90": round(float(real.quantile(0.9)), 1), "fifo_wait_p90": round(float(wait.quantile(0.9)), 1),
    }


def simulate(q: pd.DataFrame, policy: str, cfg: dict, start: pd.Timestamp, capacity: float) -> pd.DataFrame:
    """Kuyrugu bosalana kadar kosturur. q, build_queue ciktisidir (basvuru tarihine gore sirali).

    Donus: app_id, done (incelemenin bittigi tarih; incelenmeden ciktiysa bos), spent (harcanan saat),
    order (bitis sirasi, 1'den baslar), lane (dosyanin hangi kademeden bittigi).
    """
    if capacity <= 0:
        raise ValueError("kapasite sifir")
    n = len(q)
    arrival = q.arrival.to_numpy("datetime64[D]")
    exit_ = q.exit.to_numpy("datetime64[D]")
    effort = q.effort.to_numpy(float)
    scored = q.scored.to_numpy(bool)
    small = q.small.to_numpy(bool)
    remaining, spent = effort.copy(), np.zeros(n)
    done = np.full(n, np.datetime64("NaT"), "datetime64[D]")
    gone = np.zeros(n, bool)  # incelendi ya da kendiliginden cikti
    order, lane = np.zeros(n, int), np.full(n, None, object)
    finished = 0

    fair = False
    if policy != "fifo":
        use_wd, use_effort, fair = POLICIES[policy]
        s = np.nan_to_num(score(q, use_wd, use_effort), nan=-1.0)
        share_unscored, share_small = lane_shares(q, cfg)
        if not fair:
            share_small = 0.0
    max_wait = np.timedelta64(cfg["queue"]["max_wait_days"], "D")
    now = np.datetime64(start, "D")

    def work(idx, budget, name):
        """Verilen siradaki dosyalara butceyi harcar; artan butceyi dondurur. Yarim kalan dosya ilerlemesini korur."""
        nonlocal finished
        for i in idx:
            if budget <= 1e-9:
                break
            if gone[i]:
                continue
            step = min(remaining[i], budget)
            remaining[i] -= step
            spent[i] += step
            budget -= step
            if remaining[i] <= 1e-9:
                finished += 1
                gone[i], done[i], order[i], lane[i] = True, now + WEEK, finished, name
        return budget

    def by_score(idx):
        # skor (yuksekten dusuge), esitlikte basvuru tarihi (FIFO)
        return idx[np.lexsort((idx, -s[idx]))]

    for _ in range(cfg["simulation"]["max_weeks"]):
        gone |= ~gone & (exit_ <= now)  # NaT karsilastirmasi False doner
        waiting = np.flatnonzero((arrival <= now) & ~gone)
        if len(waiting) == 0:
            if not (~gone).any():
                break
        elif policy == "fifo":
            work(waiting, capacity, "fifo")
        else:
            budget = capacity
            if fair:  # 1. zorunlu kademe: azami beklemeyi asanlar, basvuru tarihine gore
                cap = capacity * cfg["queue"]["max_wait_capacity_share"]
                budget = capacity - cap + work(waiting[now - arrival[waiting] > max_wait], cap, "max_wait")
            w_scored, w_unscored = waiting[scored[waiting]], waiting[~scored[waiting]]
            left = work(w_unscored, budget * share_unscored, "unscored")  # skorsuz yol
            left += work(w_scored[small[w_scored]], budget * share_small, "small_quota")  # 2. adalet: kucuk proje kotasi
            left += work(by_score(w_scored), budget * (1 - share_unscored - share_small), "carbon")  # 3. karbon skoru
            left = work(by_score(w_scored), left, "carbon")  # bos kalan kapasite diger yola gecer
            work(w_unscored, left, "unscored")
        now = now + WEEK
    else:
        raise RuntimeError("kuyruk max_weeks icinde bosalmadi")

    return pd.DataFrame({"app_id": q.app_id.values, "done": pd.to_datetime(done), "spent": spent,
                         "order": order, "lane": lane})
