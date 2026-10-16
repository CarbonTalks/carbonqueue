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

Her klasörün kendi README'si ayrıntılı kurulum ve sözleşmeleri anlatır.

## Uçtan uca çalıştırma

Gerekenler: Python 3.11+ (pandas, pyarrow, catboost, scikit-learn), [uv](https://docs.astral.sh/uv/) (backend Python 3.14 kullanır), Node.js.

Önce veri, model ve simülasyon sonuçları üretilir (bir kez):

```sh
cd cq-model
pip install pandas pyarrow catboost scikit-learn
python scripts/download_repd.py
PYTHONPATH=src python -m cq.dataset
PYTHONPATH=src python scripts/make_predictions.py        # ~5 dk, model_live.cbm dahil

cd ../cq-sim
PYTHONPATH=src python -m cqsim all                        # geçmiş simülasyon ve duyarlılık
PYTHONPATH=src python -m cqsim rank                       # canlı kuyruk (results/live-queue.json)
```

Sonra dört süreç, her biri ayrı terminalde ve `cq-backend` klasöründen başlatılarak:

```sh
# 1. Model köprüsü (port 9001, cq-model ortamı)
cd ../cq-model && PYTHONPATH=src python ../cq-backend/integration/ml_server.py --predictor cq.serve:predict --port 9001

# 2. Kuyruk motoru (port 9002)
cd ../cq-sim && PYTHONPATH=src python -m cqsim serve

# 3. Backend (port 8000); .env:
#    CQ_ML_URL=http://127.0.0.1:9001
#    CQ_QUEUE_ENGINE_URL=http://127.0.0.1:9002
#    CQ_CORS_ORIGINS=http://localhost:5173
#    CQ_SIMULATION_RESULTS_DIR=../cq-sim/results
uv sync --locked && uv run cq-backend

# 4. Dashboard (port 5173)
cd ../cq-website && npm install && npm run dev
```

Canlı kuyruğu bir kez backend'e yükleyin (`cq-backend` klasöründen):

```sh
curl --fail -H 'Content-Type: application/json'   --data-binary @../cq-sim/results/live-queue.json   http://127.0.0.1:8000/queue/live/import
```

Windows PowerShell'de `PYTHONPATH=src` yerine `$env:PYTHONPATH="src"` kullanın.

Belgeden alan çıkarma için `cq-backend/.env` dosyasına kendi `GOOGLE_API_KEY` değerinizi yazın (`cq-backend/.env.example`).

## Bağlantıların durumu (17 Ekim 2026)

| Bağlantı | Durum |
|---|---|
| cq-model → cq-sim (tahmin dosyaları) | Çalışıyor |
| cq-sim → cq-backend (canlı kuyruk içe aktarma) | Çalışıyor |
| cq-model → cq-backend (`cq.serve:predict`, model köprüsü üzerinden) | Çalışıyor |
| cq-backend → kuyruk motoru (`cqsim serve`: karbon bandı, efor, kademe, gerekçe, planlanan hafta) | Çalışıyor |
| cq-website → cq-backend (canlı kuyruk, proje, belge yükleme, geçmiş simülasyon) | Çalışıyor; arayüz Türkçe / İngilizce |
| cq-backend → belge çıkarma (Gemini) | API anahtarı gerektirir; gerçek PDF ile test bekliyor |

## Bilinen sınırlamalar

- Geri çekilme tahmini zayıf (ROC-AUC 0,54–0,64); sıralamaya etkisi %2'den az.
- Kapasite gözlenen medyan karar süresine kalibre edilir; en yavaş uç (P90) yeniden üretilemez.
- Uzman saati ve maliyet verisi kamuya açık değil; efor kural tabanlı.
- Projenin gerçekten işletmeye girme olasılığı (gerçekleşme modeli) denendi, mevcut veriyle güvenilir değil; kullanılmıyor.

## Alt repolarla senkron

Klasörler `git subtree` ile eklendi. Bir alt reponun son halini çekmek için:

```sh
git subtree pull --prefix=cq-sim https://github.com/CarbonTalks/cq-sim.git main
```
