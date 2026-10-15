# cq-model

CarbonQueue K1: REPD temizliği, ayrık zamanlı geri çekilme modeli ve yıllık tahmin dosyaları.

## Kurulum ve çalıştırma

```sh
pip install pandas pyarrow catboost scikit-learn
python scripts/download_repd.py                                   # data/raw/ altına REPD (Temmuz 2026)
PYTHONPATH=src python -m cq.dataset                               # data/processed/applications.parquet
PYTHONPATH=src python scripts/make_predictions.py                 # yıl yıl modeller + data/processed/predictions/ (~5 dk)
PYTHONPATH=src python scripts/evaluate.py                         # 2023 doğrulama / 2024 test metrikleri
PYTHONPATH=src python scripts/profile_repd.py                     # reports/repd_profile.md sayıları
```

Windows PowerShell'de `PYTHONPATH=src` yerine önce `$env:PYTHONPATH="src"` çalıştırın.

- Veri sözleşmesi: [docs/data_contract.md](docs/data_contract.md)
- Veri profili: [reports/repd_profile.md](reports/repd_profile.md)

## Backend entegrasyonu (cq-backend)

```python
from cq.serve import load_predictor   # cq-model/src PYTHONPATH'te olmalı
app = create_app(ml=load_predictor())
```

- Gerekenler: `data/processed/applications.parquet` ve `data/models/model_live.cbm`, `pandas`, `pyarrow`, `catboost`. Yalnızca canlı modeli üretmek için: `PYTHONPATH=src python scripts/make_predictions.py --live-model-only` (tahmin dosyalarına dokunmaz). Model sunucusu modeli başlangıçta bir kez yükler; yeni dosyadan sonra yeniden başlatın.
- Girdi: `ProjectFeatures` (`technology`, `capacity_mw`, opsiyonel `planning_authority`, `applicant`, `submission_date`). Kurum adı REPD'deki ada eşlenir ("Cherwell District Council" → "Cherwell"); bulunamazsa kurum özellikleri boş kalır, tahmin yine üretilir.
- Çıktı: `withdrawal_probability_12m` ve 13 elemanlı `decision_distribution` (12 aylık dilim + "12 ay içinde karar yok").
- Desteklenmeyen teknolojide `ValueError` verir. Bir çağrı yaklaşık 0,3 saniye; veri ve model başlangıçta bir kez yüklenir.
- Backend'in model köprüsüyle (cq-backend/integration/ml_server.py) ayrı süreçte: `PYTHONPATH=src python ../cq-backend/integration/ml_server.py --predictor cq.serve:predict --port 9001`. `predict` modeli ilk çağrıda bir kez yükler.
- Test: `PYTHONPATH=src python tests/test_serve.py`
