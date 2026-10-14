"""REPD ham CSV'sini okur: kodlama, kolon adlari, tarih ve sayi tipleri."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "REPD_Publication_Q2_2026.csv"
SNAPSHOT = pd.Timestamp("2026-07-24")  # Temmuz 2026 surumundeki en son kayit guncellemesi

# Ham kolon adi -> kodda kullanilan kisa ad
COLS = {
    "Ref ID": "ref_id",
    "Old Ref ID": "old_ref_id",
    "Record Last Updated (dd/mm/yyyy)": "last_updated",
    "Operator (or Applicant)": "operator",
    "Site Name": "site_name",
    "Technology Type": "technology",
    "Storage Type": "storage_type",
    "Storage Co-location REPD Ref ID": "storage_coloc_ref",
    "Installed Capacity (MWelec)": "capacity_mw",
    "Mounting Type for Solar": "solar_mounting",
    "Solar Site Area (sqm)": "solar_area_sqm",
    "No. of Turbines": "n_turbines",
    "Turbine Capacity (MW)": "turbine_mw",
    "Development Status": "status",
    "Development Status (short)": "status_short",
    "Are they re-applying (New REPD Ref)": "reapply_new_ref",
    "Are they re-applying (Old REPD Ref) ": "reapply_old_ref",
    "County": "county",
    "Region": "region",
    "Country": "country",
    "Planning Authority": "authority",
    "Planning Application Reference": "app_ref",
    "Type of Secretary of State Intervention": "sos_type",
    "Offshore Wind Round": "offshore_round",
    "Planning Application Submitted": "d_submitted",
    "Planning Application Withdrawn": "d_withdrawn",
    "Planning Permission Refused": "d_refused",
    "Appeal Lodged": "d_appeal_lodged",
    "Appeal Withdrawn": "d_appeal_withdrawn",
    "Appeal Refused": "d_appeal_refused",
    "Appeal Granted": "d_appeal_granted",
    "Planning Permission  Granted": "d_granted",
    "Secretary of State - Intervened": "d_sos_intervened",
    "Secretary of State - Refusal": "d_sos_refused",
    "Secretary of State - Granted": "d_sos_granted",
    "Planning Permission Expired": "d_expired",
    "Under Construction": "d_construction",
    "Operational": "d_operational",
}
NUMERIC = ["capacity_mw", "solar_area_sqm", "n_turbines", "turbine_mw"]


def load_raw(path: Path = RAW) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="cp1252", low_memory=False, dtype=str)
    df = df.rename(columns=COLS)[list(COLS.values())]
    for c in df.columns:
        df[c] = df[c].str.strip().replace("", pd.NA)
    for c in [c for c in df.columns if c.startswith("d_")] + ["last_updated"]:
        parsed = pd.to_datetime(df[c], format="%d/%m/%Y", errors="coerce")
        # Tek tuk ABD bicimli kayit var (ör. 4/17/2026)
        df[c] = parsed.fillna(pd.to_datetime(df[c], format="%m/%d/%Y", errors="coerce"))
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")
    df["ref_id"] = df["ref_id"].astype(int)
    return df
