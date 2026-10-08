"""REPD (Temmuz 2026) CSV'sini GOV.UK'den data/raw/ altina indirir."""
from pathlib import Path
from urllib.request import urlretrieve

URL = "https://assets.publishing.service.gov.uk/media/6a6cbdc00c36759b5ccaa305/REPD_Publication_Q2_2026.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "REPD_Publication_Q2_2026.csv"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        print(f"zaten var: {OUT}")
    else:
        urlretrieve(URL, OUT)
        print(f"indirildi: {OUT} ({OUT.stat().st_size:,} bayt)")
