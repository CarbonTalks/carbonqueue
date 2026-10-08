"""Ortak veri seti: REPD'den her basvuru icin tek satir (docs/applications_schema.md).

Calistirma: PYTHONPATH=src python -m cq.dataset
"""
import numpy as np
import pandas as pd

from cq.repd import ROOT, SNAPSHOT, load_raw

OUT = ROOT / "data" / "processed" / "applications.parquet"

CATEGORY = {
    "Solar Photovoltaics": "solar",
    "Wind Onshore": "onshore_wind",
    "Battery": "storage",
    "Pumped Storage Hydroelectricity": "storage",
    "Liquid Air Energy Storage": "storage",
    "Compressed Air Energy Storage": "storage",
    "Flywheels": "storage",
    "Anaerobic Digestion": "bioenergy_waste",
    "Landfill Gas": "bioenergy_waste",
    "Biomass (dedicated)": "bioenergy_waste",
    "Biomass (co-firing)": "bioenergy_waste",
    "EfW Incineration": "bioenergy_waste",
    "Advanced Conversion Technologies": "bioenergy_waste",
    "Sewage Sludge Digestion": "bioenergy_waste",
    "Small Hydro": "other_renewable",
    "Large Hydro": "other_renewable",
    "Tidal Stream": "other_renewable",
    "Tidal Lagoon": "other_renewable",
    "Shoreline Wave": "other_renewable",
    "Geothermal": "other_renewable",
    "Hot Dry Rocks (HDR)": "other_renewable",
    "Wind Offshore": "out_of_scope",  # ayri izin rejimi
    "Hydrogen": "out_of_scope",  # etkisi kullanima bagli
    "Fuel Cell (Hydrogen)": "out_of_scope",
    "Air Source Heat Pumps": "out_of_scope",
    "Unknown": "out_of_scope",
}
MISSING_OPERATORS = {"Private Developer", "Unknown", "Private Client"}
SPECIAL_ROUTE = r"S36|National Infrastructure|NSIP|Marine"
STALE_YEARS = 5
THRESHOLD_CHANGE = pd.Timestamp("2021-01-01")


def _chains(df: pd.DataFrame) -> pd.Series:
    """Yeniden basvuru baglantilariyla birbirine bagli basvurulara ortak chain_id verir."""
    parent = {i: i for i in df.ref_id}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for col in ["reapply_new_ref", "reapply_old_ref"]:
        links = df[["ref_id", col]].dropna()
        for ref, cell in zip(links.ref_id, links[col]):
            for other in map(int, pd.Series(cell).str.findall(r"\d+").iloc[0]):
                if other in parent:
                    parent[find(ref)] = find(other)
    return df.ref_id.map(find)


def build() -> pd.DataFrame:
    df = load_raw()
    out = pd.DataFrame({"app_id": df.ref_id})
    for c in ["site_name", "technology", "authority", "county", "region", "country",
              "status", "capacity_mw", "solar_mounting", "storage_type", "solar_area_sqm"]:
        out[c] = df[c]
    out["category"] = df.technology.map(CATEGORY).fillna("out_of_scope")
    out["operator"] = df.operator.mask(df.operator.isin(MISSING_OPERATORS))
    out["chain_id"] = _chains(df)
    out["in_chain"] = out.chain_id.duplicated(keep=False)

    # --- Olay: ilk karar ya da geri cekilme ---
    # Temyizle verilen izin d_granted'in uzerine yazildigi icin min(izin, red) kurumun ilk kararidir.
    # Redsiz acilan temyizde (karar verilmeme) dosya temyiz tarihinde kurumun kuyrugundan cikar.
    nondet = df.d_appeal_lodged.where(df.d_refused.isna())
    decision = pd.concat([df.d_granted, df.d_refused, df.d_sos_granted, df.d_sos_refused, nondet], axis=1).min(axis=1)
    withdrawal_first = df.d_withdrawn.notna() & (df.d_withdrawn < decision.fillna(pd.Timestamp.max))
    out["d_submitted"] = df.d_submitted
    out["d_first_decision"] = decision
    out["d_withdrawn"] = df.d_withdrawn
    out["decision_via_nondetermination_appeal"] = nondet.notna() & (decision == nondet)
    out["event"] = np.select([withdrawal_first, decision.notna()], ["withdrawal", "decision"], "open")
    out["d_event"] = np.where(withdrawal_first, df.d_withdrawn, decision)
    out["d_event"] = pd.to_datetime(out.d_event)
    out["duration_days"] = (out.d_event.fillna(SNAPSHOT) - out.d_submitted).dt.days

    # --- Nihai sonuc (simulasyonda karbonun gercekleseni icin) ---
    out["d_permitted"] = df[["d_granted", "d_sos_granted"]].min(axis=1)  # temyizle verilen izin dahil
    out["d_construction"] = df.d_construction
    out["d_operational"] = df.d_operational
    out["abandoned_or_expired"] = df.status.isin(["Abandoned", "Planning Permission Expired"])

    # --- Disarida birakma nedenleri (model egitimi) ---
    reason = pd.Series(pd.NA, index=df.index, dtype="string")
    ended_no_date = (out.event == "open") & (df.status != "Planning Application Submitted")
    bad_order = out.d_event < out.d_submitted
    future = (out.d_event > SNAPSHOT) | (out.d_submitted > SNAPSHOT)
    pre_small = (out.d_submitted < THRESHOLD_CHANGE) & (out.capacity_mw < 1)
    for mask, why in [
        (out.category == "out_of_scope", "out_of_scope_technology"),
        (pre_small, "pre2021_below_1mw"),
        (future, "date_after_snapshot"),
        (bad_order, "event_before_submission"),
        (ended_no_date, "outcome_without_date"),
        (out.d_submitted.isna(), "no_submission_date"),
    ]:
        reason = reason.mask(mask, why)  # sonraki satir onceliklidir
    out["exclude_reason"] = reason
    out["model_eligible"] = reason.isna()

    # --- Bayraklar ---
    out["post_2021"] = out.d_submitted >= THRESHOLD_CHANGE
    out["small_project"] = out.capacity_mw < 1
    out["special_route"] = df.authority.fillna("").str.contains(SPECIAL_ROUTE)
    out["in_england"] = df.country.eq("England")
    out["sim_eligible"] = out.model_eligible & out.in_england & ~out.special_route
    age_years = (SNAPSHOT - out.d_submitted).dt.days / 365.25
    out["live_queue"] = out.sim_eligible & (out.event == "open")
    out["stale_or_uncertain"] = out.live_queue & (age_years > STALE_YEARS)
    return out


if __name__ == "__main__":
    data = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data.to_parquet(OUT, index=False)
    print(f"{OUT}  satir={len(data)}")
    print("model_eligible:", data.model_eligible.sum(), "| sim_eligible:", data.sim_eligible.sum(),
          "| live_queue:", data.live_queue.sum(), "| stale:", data.stale_or_uncertain.sum())
    print(data.exclude_reason.value_counts().to_string())
    print(pd.crosstab(data[data.model_eligible].category, data[data.model_eligible].event).to_string())
