# cq-model veri sözleşmesi (K1 → K2, K4)

Dosyalar repoya girmez; README'deki komutlarla üretilir.

## 1. `data/processed/applications.parquet`: ortak veri seti

REPD'deki her kayıt için bir satır (14.657). Herkes bu tabloyu kullanır; REPD'yi ayrıca temizlemeyin.

| Kolon | Tip | Açıklama |
|---|---|---|
| `app_id` | int | REPD `Ref ID`. Bütün dosyalarda birleştirme anahtarı |
| `site_name`, `technology`, `authority`, `county`, `region`, `country`, `status` | str | REPD alanları (boşluklar temizlenmiş). `technology` ham REPD teknolojisi |
| `category` | str | `solar`, `onshore_wind`, `storage`, `bioenergy_waste`, `other_renewable`, `out_of_scope` (deniz üstü rüzgâr, hidrojen, yakıt hücresi, ısı pompası, bilinmeyen) |
| `capacity_mw` | float | Kurulu güç. **%9 boş** (çoğu batarya ve güneş) |
| `solar_mounting`, `storage_type`, `solar_area_sqm` | str/float | Alt tür bilgisi |
| `operator` | str | Başvuru sahibi. "Private Developer", "Unknown" ve "Private Client" boş yapıldı |
| `chain_id`, `in_chain` | int, bool | Aynı projenin yeniden başvuruları aynı `chain_id`'yi alır. Bölme zincir düzeyinde yapılır |
| `d_submitted` | date | Başvuru tarihi |
| `d_first_decision` | date | Kurumun ilk kararı: `min(izin, red, SoS izin, SoS red)`. Redsiz temyizde temyiz tarihi |
| `decision_via_nondetermination_appeal` | bool | İlk karar tarihi, redsiz açılan bir temyizden mi geliyor (77 kayıt) |
| `d_withdrawn` | date | Geri çekilme tarihi |
| `event` | str | Kurum kuyruğundan çıkış: `decision`, `withdrawal`, `open`. **Kararın izin mi red mi olduğu bilerek yok** |
| `d_event` | date | `event` tarihi (`open` ise boş) |
| `duration_days` | float | Başvurudan olaya (ya da veri kesim tarihi 24.07.2026'ya) kadar geçen gün |
| `d_permitted` | date | Nihai izin tarihi (temyiz ve SoS dahil). **Yalnızca simülasyonda gerçekleşen karbon için; modele girmez** |
| `d_construction`, `d_operational` | date | İnşaat ve işletme tarihleri |
| `abandoned_or_expired` | bool | Proje terk edilmiş ya da izin süresi dolmuş |
| `exclude_reason` | str | Model eğitiminden çıkarılma nedeni (boşsa uygun) |
| `model_eligible` | bool | Model eğitimine uygun (13.572) |
| `post_2021` | bool | 2021 ve sonrası başvuru (kayıt eşiği değişikliği) |
| `small_project` | bool | < 1 MW |
| `special_route` | bool | S36, National Infrastructure, NSIP, Marine |
| `in_england` | bool | Ülke İngiltere |
| `sim_eligible` | bool | Simülasyona uygun: modele uygun, İngiltere, özel yol değil (9.834) |
| `live_queue` | bool | Bugün karar bekleyen simülasyon dosyası. Demodaki canlı kuyruk (921) |
| `stale_or_uncertain` | bool | 5 yıldan uzun süredir bekleyen canlı kuyruk dosyası (36). Silinmez, ayrıca raporlanır |

`exclude_reason` değerleri: `outcome_without_date` (347; durumu bir sonuç gösteriyor ama tarihi yok), `no_submission_date` (291), `pre2021_below_1mw` (251), `out_of_scope_technology` (177), `event_before_submission` (17), `date_after_snapshot` (2).

## 2. `data/processed/predictions/predictions_{yıl}.parquet` ve `predictions_live.parquet`

Y yılının simülasyon kuyruğu için tahminler. Y yılı içinde kuyrukta bulunan her `sim_eligible` dosyayı kapsar.

| Kolon | Tip | Açıklama |
|---|---|---|
| `app_id` | int | `applications.parquet` ile birleştirme anahtarı |
| `cutoff_year` | int | Modelin bilgi kesim yılı (Y yılı için Y−1; canlı kuyrukta 2026) |
| `as_of_date` | date | Tahminin yapıldığı an: `max(başvuru tarihi, 1 Ocak Y)` |
| `p_withdraw_12m` | float | 360 gün içinde geri çekilme olasılığı |
| `decision_dist` | list[float], 13 eleman | 30 günlük 12 dilimde ilk kararın çıkma olasılığı + son eleman "360 gün içinde karar yok". Toplamı 1 |
| `is_fake` | bool | `True` ise sahte dosya |

**Şu anki dosyalar sahte (`is_fake=True`):** her dosyaya aynı taban oran veriliyor (geri çekilme %4,1; 2015–2022 başvurularından). Bu yüzden bu dosyalarla yapılan sıralama "sadece karbon" ablasyonuna denk geliyor. Gerçek model dosyaları aynı yola ve aynı kolonlarla yazılacak.

Simülasyon kuyruk büyüklükleri (İngiltere): 2019: 163, 2020: 271, 2021: 815, 2022: 1.533, 2023: 2.014, canlı: 921.

## Kurallar
- **Red olasılığı hiçbir dosyada yok.** Model yalnızca "ne zaman karar çıkar" ve "geri çekilir mi" sorularını cevaplar.
- Simülasyonda sıralamayı tahmin yapar; karbon kazancı gerçekleşen sonuçla (`event`, `d_permitted`, `abandoned_or_expired`) hesaplanır.
