# CarbonQueue

Dört referans tasarımın React JavaScript uygulaması. React 18, Vite ve Tailwind CSS kullanır.

## Çalıştırma

```sh
npm install
npm run dev
```

Tarayıcı: http://localhost:5173

```sh
npm run build
npm run preview
```

## Backend bağlantısı

Dashboard verilerini cq-backend'den okur; örnek veri içermez.

- Adres: varsayılan `http://localhost:8000`. Değiştirmek için proje kökünde `.env.local` dosyasına `VITE_API_URL=http://...` yazın.
- Backend'de `.env`: `CQ_CORS_ORIGINS=http://localhost:5173`, `CQ_SIMULATION_RESULTS_DIR=../cq-sim/results`, `CQ_ML_URL`, `CQ_QUEUE_ENGINE_URL` ve belge çıkarma için `GOOGLE_API_KEY` (ayrıntılar cq-backend README).
- Canlı kuyruk bir kez backend'e yüklenmelidir: `curl -H 'Content-Type: application/json' --data-binary @../cq-sim/results/live-queue.json http://localhost:8000/queue/live/import`

## Sayfalar

| Sayfa | Veri kaynağı |
|---|---|
| `#/queue` | `GET /queue/live` (cq-sim canlı kuyruğu, 765 sıralı başvuru). Politika seçici: FIFO / Carbon only / CarbonQueue; oklar FIFO'ya göre sıra değişimi. Üstteki KPI'lar 2023 geçmiş simülasyonundan. CSV dışa aktarma filtrelenmiş kuyruğu verir |
| `#/project` | Seçilen kuyruk kaydı + `GET /applications/{id}` (eksik alanlar, çakışmalar, model kapsamı) |
| `#/upload` | `POST /applications/extract` (agent: belge, sayfa, alıntı), eksik alan için `PATCH /applications/{id}/observations`, skorlama için `POST /queue/run` |
| `#/results` | Planlanan iş yükü: canlı kuyruğun haftalara dağılımı. Geçmiş analiz: `GET /simulation/historical/{yıl}/{politika}`, 2019–2023, beş politika |
| `#/methodology`, `#/settings` | Yöntem, kaynaklar, sınırlamalar; bağlantı durumu |

Uzman ekranlarında gerçekleşme olasılığı gibi alanlar gösterilmez; backend bunları zaten sunmuyor.

## Dil

Arayüz Türkçe ve İngilizcedir; sağ üstteki TR / EN seçiciyle (ya da Ayarlar → Dil) değiştirilir, seçim tarayıcıda saklanır, varsayılan Türkçedir. Metinlerin anahtarı İngilizce metnin kendisidir; Türkçeleri `src/i18n-tr.js` içindedir, eksik bir çeviri İngilizce görünür. Yöntem sayfasının uzun metinleri `src/pages/Methodology.jsx` içinde iki dilde tutulur. Kuyruktaki gerekçe metinleri, motorun Türkçe metni yerine kademe ve sayılardan seçilen dilde yeniden üretilir.

## Yapı

`src/api.js` backend istemcisi, `src/i18n.jsx` dil seçimi ve çeviri, `src/live-data.js` canlı kuyruk kayıtlarını tablo satırlarına çevirir, `src/main.jsx` ortak yerleşim, gezinme ve kuyruk durumunu, `src/state.jsx` kuyruk satırlarını, `src/chart.jsx` grafikleri içerir. Renk ve tipografi `tailwind.config.cjs`, uyarlanabilir ekran kuralları `src/styles.css` dosyasındadır.

## Kapsam

Kimlik doğrulama yok; düzeltmeler `dashboard-reviewer` adıyla kaydedilir. Belge çıkarma backend'de Gemini anahtarı gerektirir; anahtar yoksa Upload sayfası backend'in hata mesajını gösterir. Google Fonts için internet bağlantısı gerekir.
