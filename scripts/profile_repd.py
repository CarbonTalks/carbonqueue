"""REPD veri profili: reports/repd_profile.md'deki sayilari yeniden uretir.

Calistirma: PYTHONPATH=src python scripts/profile_repd.py
"""
import numpy as np
import pandas as pd

from cq.repd import SNAPSHOT, load_raw

df = load_raw()
print(f"satir={len(df)}  kurum={df.authority.nunique()}  basvuru sahibi={df.operator.nunique()}")

print("\n## Tarih dolulugu")
print(df.filter(regex="^d_").notna().mean().round(3).to_string())

print("\n## Snapshot sonrasi tarihler (> %s)" % SNAPSHOT.date())
for c in df.filter(regex="^d_").columns:
    n = (df[c] > SNAPSHOT).sum()
    if n:
        print(c, n)

print("\n## Teknoloji"); print(df.technology.value_counts().to_string())
print("\n## Durum"); print(df.status.value_counts().to_string())
print("\n## Ulke"); print(df.country.value_counts(dropna=False).to_string())

special = df.authority.fillna("").str.contains(r"S36|National Infrastructure|NSIP|Marine")
print("\n## Ozel izin yollari"); print(df.loc[special, "authority"].value_counts().to_string())

# Ilk karar = yerel kurumun ilk izin/red tarihi. Temyizle verilen izin d_granted'in uzerine
# yazildigi icin min(granted, refused) reddi yakalar.
df["d_first_decision"] = df[["d_granted", "d_refused", "d_sos_granted", "d_sos_refused"]].min(axis=1)
both = df.d_granted.notna() & df.d_refused.notna()
print("\n## Tutarlilik")
print("izin ve red birlikte:", both.sum(), "| d_granted == temyiz izni:", (df.d_granted == df.d_appeal_granted).sum())
print("redsiz temyiz (karar verilmeme temyizi?):", (df.d_appeal_lodged.notna() & df.d_refused.isna()).sum())
print("karar < basvuru:", (df.d_first_decision < df.d_submitted).sum(),
      "| geri cekilme < basvuru:", (df.d_withdrawn < df.d_submitted).sum(),
      "| geri cekilme ve karar birlikte:", (df.d_withdrawn.notna() & df.d_first_decision.notna()).sum())
print("basvuru tarihi yok:", df.d_submitted.isna().sum())

wd_first = df.d_withdrawn.notna() & (df.d_withdrawn < df.d_first_decision.fillna(pd.Timestamp.max))
df["event"] = np.select([wd_first, df.d_first_decision.notna()], ["geri_cekilme", "karar"], "acik")
nodate = (df.event == "acik") & ~df.status.isin(["Planning Application Submitted", "Revised"])
df.loc[nodate, "event"] = "sonuc_var_tarih_yok"
print("\n## Kohortlar (basvuru yili x olay)")
t = pd.crosstab(df.d_submitted.dt.year, df.event)
t["n"] = t.sum(axis=1)
t["acik_%"] = (100 * t["acik"] / t.n).round(1)
print(t.loc[2010:].to_string())

print("\n## <1 MW payi (basvuru yilina gore)")
print(df.groupby(df.d_submitted.dt.year).capacity_mw.apply(lambda s: (s < 1).mean()).loc[2014:].round(3).to_string())
print("kapasite bos:", df.capacity_mw.isna().sum())

days = (df.d_first_decision - df.d_submitted).dt.days
days = days[days >= 0]
print("\n## Ilk karara gun: medyan", days.median(), "| 8/13/16 hafta icinde:",
      [round((days <= d).mean(), 3) for d in (56, 91, 112)])

pend = df.status.eq("Planning Application Submitted")
eng = pend & df.country.eq("England") & ~special & df.technology.ne("Wind Offshore")
age = (SNAPSHOT - df.d_submitted).dt.days / 365.25
print("\n## Bekleyen kuyruk")
for name, m in [("tum UK", pend), ("England, ozel yol/offshore haric", eng)]:
    print(f"{name}: n={m.sum()} medyan yas={age[m].median():.2f} yil  >2y={(age[m] > 2).sum()}  >5y={(age[m] > 5).sum()}")
print(df.loc[eng, "technology"].value_counts().to_string())
