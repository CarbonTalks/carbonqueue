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

## Sayfalar

- `/#/queue`: Başvuru kuyruğu; arama, teknoloji / kapasite / bekleme filtreleri, örnek sıralama, CSV dışa aktarma.
- `/#/project`: Riverside Solar proje detayı.
- `/#/upload`: Belge seçme / sürükleyip bırakma, örnek kanıt alanı inceleme, oturum içi değer düzenleme ve yerel taslak kaydı.
- `/#/simulation`: Referans simülasyon sonuçları, teknoloji / proje büyüklüğü sekmeleri, CSV dışa aktarma.

## Yapı

`src/pages/` dört ekranı, `src/main.jsx` ortak yerleşim ve gezinmeyi, `src/state.jsx` örnek proje verilerini ve kuyruk satırlarını içerir. Renk ve tipografi ayarları `tailwind.config.cjs`, uyarlanabilir ekran kuralları `src/styles.css` dosyasındadır. Orijinal tasarımlar `references/` altında korunmuştur.

## Kapsam

Bu bir ön yüz prototipidir. Tasarımlardaki 42 başvuruluk özet ve tarihsel simülasyon metrikleri referans verileridir; etkileşimli tabloda tasarımların içerdiği 7 örnek proje bulunur. Sıralama düğmeleri basitleştirilmiş gösterimlerdir; gerçek CarbonQueue modelini çalıştırmaz. Orijinal kaynak PDF'ler ZIP dosyalarında bulunmadığı için PDF alanı tasarım önizlemesidir.

Seçilen dosyalar sunucuya gönderilmez. OCR, AI belge çıkarımı, gerçek simülasyon, kullanıcı kimlik doğrulaması ve kalıcı sunucu kaydı bağlı değildir. Taslak kaydı bu tarayıcının localStorage alanına yapılır. Google Fonts için internet bağlantısı gerekir; CSS derleme sırasında yerel üretilir, Tailwind CDN kullanılmaz.
