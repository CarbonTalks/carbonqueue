"""Backend icin tahmin fonksiyonu (cq-backend: create_app(ml=...)).

    from cq.serve import load_predictor
    app = create_app(ml=load_predictor())

Girdi: backend'in ProjectFeatures nesnesi (ya da ayni alanlari tasiyan dict).
Cikti: {"withdrawal_probability_12m": float, "decision_distribution": 13 olasilik}
Tahmin, basvuru anindaki duruma gore yapilir; gecmis ozellikler (kurum yuku, basvuru sahibi gecmisi)
REPD verisinden basvuru tarihi itibariyla hesaplanir. Red olasiligi uretilmez.
"""
import re
import threading
from datetime import date

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from cq.dataset import OUT as APPLICATIONS
from cq.dataset import SPECIAL_ROUTE, THRESHOLD_CHANGE
from cq.features import build_features
from cq.model import predict as model_predict
from cq.repd import ROOT

MODEL = ROOT / "data" / "models" / "model_live.cbm"

# backend teknolojisi -> (kategori, REPD teknolojisi)
TECH = {
    "solar": ("solar", "Solar Photovoltaics"),
    "onshore_wind": ("onshore_wind", "Wind Onshore"),
    "battery": ("storage", "Battery"),
    "hydro": ("other_renewable", "Small Hydro"),
    "biomass": ("bioenergy_waste", "Biomass (dedicated)"),
    "tidal": ("other_renewable", "Tidal Stream"),
    "wave": ("other_renewable", "Shoreline Wave"),
}
GENERATION = {"solar", "onshore_wind", "bioenergy_waste", "other_renewable"}
_AUTH_NOISE = r"\b(the|of|and|district|borough|city|county|metropolitan|royal|council|unitary|authority)\b"


def _auth_key(name: str) -> str:
    """"Cherwell District Council" ve "Cherwell" ayni kurum."""
    s = re.sub(r"[^a-z ]", " ", name.lower().replace("&", " and "))
    return re.sub(r"\s+", " ", re.sub(_AUTH_NOISE, " ", s)).strip()


def _field(project, name):
    return project.get(name) if isinstance(project, dict) else getattr(project, name, None)


class Predictor:
    def __init__(self, apps: pd.DataFrame | None = None, model: CatBoostClassifier | None = None):
        self.apps = pd.read_parquet(APPLICATIONS) if apps is None else apps
        if model is None:
            if not MODEL.exists():
                raise FileNotFoundError(f"{MODEL} yok: once scripts/make_predictions.py calistirin")
            model = CatBoostClassifier()
            model.load_model(MODEL)
        self.model = model
        a = self.apps[self.apps.authority.notna()]
        place = a.groupby("authority")[["country", "region"]].agg(lambda s: s.mode().iat[0] if s.notna().any() else pd.NA)
        self.place = place
        self.authorities = {_auth_key(n): n for n in place.index}

    def authority(self, name: str | None) -> str | None:
        """Agent'in cikardigi kurum adini REPD'deki ada esler; bulunamazsa None."""
        if not name:
            return None
        return self.authorities.get(_auth_key(name))

    def row(self, project) -> pd.DataFrame:
        tech = _field(project, "technology")
        if tech not in TECH:
            raise ValueError(f"bu teknoloji icin model yok: {tech}")
        category, technology = TECH[tech]
        mw = float(_field(project, "capacity_mw"))
        submitted = pd.Timestamp(_field(project, "submission_date") or date.today())
        auth = self.authority(_field(project, "planning_authority"))
        country, region = self.place.loc[auth].tolist() if auth else (pd.NA, pd.NA)
        return pd.DataFrame([{
            "app_id": -1, "category": category, "technology": technology,
            "solar_mounting": pd.NA, "storage_type": "Stand-alone Storage" if category == "storage" else pd.NA,
            "country": country, "region": region, "authority": auth, "operator": _field(project, "applicant"),
            "capacity_mw": mw, "app_generation_mw": mw if category in GENERATION else np.nan, "n_components": 1,
            "d_submitted": submitted, "post_2021": submitted >= THRESHOLD_CHANGE, "small_project": mw < 1,
            "special_route": bool(auth and re.search(SPECIAL_ROUTE, auth)),
        }])

    def __call__(self, project) -> dict:
        feats = build_features(self.apps, query=self.row(project))
        pred = model_predict(self.model, feats, feats.index.values).iloc[0]
        return {"withdrawal_probability_12m": float(pred.p_withdraw_12m),
                "decision_distribution": [float(x) for x in pred.decision_dist]}


def load_predictor() -> Predictor:
    """Veri ve model bir kez yuklenir; donen nesne fonksiyon gibi cagrilir (senkron)."""
    return Predictor()


_PREDICTOR: Predictor | None = None
_LOCK = threading.Lock()


def predict(project) -> dict:
    """Modul duzeyinde tahmin fonksiyonu; veri ve model ilk cagrida bir kez yuklenir.

    cq-backend'in model koprusu icin: python integration/ml_server.py --predictor cq.serve:predict
    """
    global _PREDICTOR
    with _LOCK:
        if _PREDICTOR is None:
            _PREDICTOR = Predictor()
    return _PREDICTOR(project)
