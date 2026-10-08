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
