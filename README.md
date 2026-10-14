# CarbonQueue

Düşük karbonlu enerji projelerinin planlama başvurularını, sınırlı uzman kapasitesini dikkate alarak karbon etkisine göre
sıralayan karar destek sistemi. Sistem onay ya da red vermez; yalnızca inceleme sırasını önerir.

Bu repo ekibin dört reposunu, geçmişleriyle birlikte tek yerde toplar:

| Klasör | Sahibi | İçerik |
|---|---|---|
| [cq-model](cq-model) | K1 | REPD temizliği, ortak veri seti, geri çekilme ve karar süresi modeli, tahmin dosyaları |
| [cq-sim](cq-sim) | K2 | Karbon motoru, efor kuralları, kuyruk politikaları, simülatör, canlı kuyruk sıralaması |
| [cq-backend](cq-backend) | K3 | Belge okuma ve kanıtlı alan çıkarma (agent), API, kayıt |
| [cq-website](cq-website) | K4 | Dashboard |
| [integration](integration) | — | Parçaları birbirine bağlayan yardımcılar |

Her klasörün kendi README'si ayrıntılı kurulum ve sözleşmeleri anlatır.

## Uçtan uca çalıştırma

Gerekenler: Python 3.11+ (pandas, pyarrow, catboost, scikit-learn), [uv](https://docs.astral.sh/uv/) (backend Python 3.14 kullanır), Node.js.

```sh
# 1. Veri ve modeller (cq-model)
cd cq-model
pip install pandas pyarrow catboost scikit-learn
python scripts/download_repd.py
PYTHONPATH=src python -m cq.dataset
PYTHONPATH=src python scripts/make_predictions.py        # ~5 dk

# 2. Simülasyon ve canlı kuyruk (cq-sim, ../cq-model çıktılarını okur)
cd ../cq-sim
PYTHONPATH=src python -m cqsim all
PYTHONPATH=src python -m cqsim rank

# 3. Model sunucusu (ayrı terminal, port 9001)
cd ..
python integration/ml_server.py

# 4. Backend (ayrı terminal, port 8000)
cd cq-backend
uv sync --locked
CQ_ML_URL=http://127.0.0.1:9001 uv run cq-backend

# 5. Canlı kuyruğu backend'e yükle
curl --fail -H 'Content-Type: application/json' \
  --data-binary @../cq-sim/results/live-queue.json \
  http://127.0.0.1:8000/queue/live/import

# 6. Web sitesi (ayrı terminal, port 5173)
cd ../cq-website
npm install
npm run dev
```

Windows PowerShell'de `PYTHONPATH=src` yerine `$env:PYTHONPATH="src"`, `CQ_ML_URL=...` yerine `$env:CQ_ML_URL="..."` kullanın.

Belgeden alan çıkarma için `cq-backend/.env` dosyasına kendi `GOOGLE_API_KEY` değerinizi yazın (`cq-backend/.env.example`).

## Bağlantıların durumu (14 Ekim 2026)

| Bağlantı | Durum |
|---|---|
| cq-model → cq-sim (tahmin dosyaları) | Çalışıyor |
| cq-sim → cq-backend (canlı kuyruk içe aktarma) | Çalışıyor: 765 sıralı, 35 teyit bekleyen dosya |
| cq-model → cq-backend (tahmin, `integration/ml_server.py` üzerinden) | Çalışıyor |
| cq-backend → belge çıkarma (Gemini) | API anahtarı gerektirir |
| cq-backend → kuyruk motoru (`/queue/run`, `/simulation/run`) | Henüz yok: cq-sim için motor adaptörü yazılacak |
| cq-website → cq-backend / cq-sim sonuçları | Henüz yok: dashboard örnek verilerle çalışıyor |

## Bilinen sorunlar

- Canlı model, yeni bir başvuru için "12 ay içinde karar yok" olasılığını yüksek veriyor (40 MW güneşte %55–78; gerçekte
  2024 güneş başvurularında %17). cq-sim sonuçlarını etkilemez, çünkü motor bu dağılımı kullanmıyor.
- Geri çekilme tahmini zayıf (ROC-AUC 0,57–0,66); sıralamaya etkisi %2'den az.
- Uzman saati ve maliyet verisi kamuya açık değil; efor kural tabanlı.

## Alt repolarla senkron

Klasörler `git subtree` ile eklendi. Bir alt reponun son halini çekmek için:

```sh
git subtree pull --prefix=cq-sim https://github.com/CarbonTalks/cq-sim.git main
```
