# cq-sim

CarbonQueue K2: deterministik karbon motoru, efor kuralları, kuyruk politikaları ve kuyruk simülatörü.
Web sitesi ya da backend olmadan bütün deney sonuçlarını üretir.

## Kurulum ve çalıştırma

Girdi olarak [cq-model](https://github.com/CarbonTalks/cq-model) çıktıları gerekir (`applications.parquet` ve `predictions/`).
Varsayılan yol yan klasördeki `../cq-model/data/processed`; başka bir yer için `--data`.

```sh
pip install pandas pyarrow pytest
PYTHONPATH=src python -m cqsim all                                        # bütün yıllar x politikalar + results/summary.md
PYTHONPATH=src python -m cqsim simulate --year 2022 --policy carbonqueue  # results/2022-carbonqueue.json
PYTHONPATH=src python -m cqsim rank                                       # results/live-queue.json (canlı kuyruk sıralaması)
PYTHONPATH=src python -m cqsim sensitivity                                # results/sensitivity.json + sensitivity.md
PYTHONPATH=src python -m pytest -q
```

Windows PowerShell'de `PYTHONPATH=src` yerine önce `$env:PYTHONPATH="src"` çalıştırın.

## Politikalar (ablasyon sırasıyla)

| Politika | Sıralama |
|---|---|
| `fifo` | Başvuru tarihi |
| `carbon` | Günlük tCO₂ |
| `carbon_withdrawal` | (1 − P(geri çekilme)) × günlük tCO₂ |
| `carbon_withdrawal_effort` | (1 − P(geri çekilme)) × günlük tCO₂ ÷ efor |
| `carbonqueue` | Önce azami beklemeyi aşanlar, sonra küçük proje kotası, sonra yukarıdaki skor; eşitlikte başvuru tarihi |

FIFO dışındaki bütün politikalarda skorsuz dosyalar (depolama, biyoenerji, kapasitesi eksik) ayrı bir yoldan gider:
kapasitenin efor payları kadarını alır ve kendi içinde başvuru tarihine göre ilerler.

## Simülasyon kuralları

- **Tek İngiltere havuzu.** Kurum başına yıllık dosya sayısı medyan 2–5; kurum içinde sıralamanın etkisi olmaz. Ortak bir uzman havuzu varsayılır.
- **Kapasite yıl yıl kalibre edilir:** haftalık kapasite, FIFO simülasyonundaki medyan bekleme aynı dosyaların gerçek medyan karar süresine eşit olacak şekilde bulunur. Yalnızca medyan eşleştirilir; gerçek ve simüle P90 kontrol olarak raporlanır (`calibration`). Tek sıralı FIFO gerçekteki uzun kuyruğu üretmez: gerçek P90 simülasyondakinin 2–3 katıdır. Kuyruk boşalana kadar aynı kapasiteyle devam edilir.
- **Karşılaştırma yalnızca simülasyonlar arasında.** Gerçek tarihler dosyanın kuyruğa giriş tarihini ve sonucunu belirler; karar tarihleri simülasyondan çıkar.
- **Karbon kazancı gerçekleşen sonuçla:** yalnızca nihai izin almış ve terk edilmemiş dosyalar sayılır. Kazanç = Σ günlük tCO₂ × (FIFO'daki karar günü − politikadaki karar günü) × α.
- **Geri çekilen ve redsiz temyize giden dosya:** gerçek çıkış tarihine kadar incelenmediyse o tarihte kuyruktan çıkar; daha önce sırası gelirse eforu harcar. Katkısı sıfır.
- **Sonucu belli olmayan dosya:** eforu harcar, katkısı sıfır, sayısı `unresolved_files` alanında.

Bütün sayısal varsayımlar [assumptions.toml](assumptions.toml) içinde. `DOGRULANACAK` işaretli değerler (yük faktörü, emisyon faktörü) yer tutucudur.

## Sonuç dosyası (K2 → K4)

`results/{yıl}-{politika}.json`:

| Alan | Açıklama |
|---|---|
| `calibration` | Kalibre kapasite (`capacity_hours_per_week`), kalibrasyonsuz kapasite, katsayı; gerçek ve FIFO medyan/P90 bekleme |
| `lane_share` | Yolların kapasite payı |
| `files`, `reviewed`, `left_before_review`, `unresolved_files`, `carbon_files` | Dosya sayıları |
| `wait_days.{all,small_scored,large_scored,unscored}` | Bekleme (gün): `n`, `median`, `p90`, `max` |
| `over_max_wait_share` | Azami beklemeyi aşan incelenmiş dosya payı |
| `carbon_weighted_wait_days` | Karbona katkısı olan dosyaların günlük tCO₂ ağırlıklı ortalama beklemesi |
| `carbon_gain_tco2_vs_fifo.alpha_{α}.{low,central,high}` | FIFO'ya göre kazanç; α ve emisyon faktörü ayrı eksenlerdir |
| `wasted_hours_on_withdrawn`, `hours_on_unresolved` | Geri çekilen ve sonucu belirsiz dosyalara harcanan saat |
| `assumptions` | Koşuda kullanılan `assumptions.toml` |

## Canlı kuyruk (K2 → K4)

`results/live-queue.json`: canlı kuyruğun bugünkü kapasiteyle simüle edilmesinden çıkan sıra. Kapasite = son 365 günde karar verilen dosyaların eforu ÷ 52 × 2023 kalibrasyon katsayısı (canlı kuyrukta gerçek sonuç olmadığı için ayrıca kalibre edilemez).
Canlı kuyrukta gerçek sonuç bilinmediği için karbon kazancı raporlanmaz.

| Alan | Açıklama |
|---|---|
| `as_of`, `calibration`, `lane_counts` | Sıralamanın tarihi, kapasite ve katsayısı, kademe başına dosya sayısı |
| `files[]` | CarbonQueue sırasına göre dosyalar |
| `files[].position.{fifo,carbon,carbonqueue}` | Üç politikadaki sıra (dashboard'daki politika seçici için) |
| `files[].planned_week.{…}` | Dosyanın kaçıncı haftada incelenmesinin planlandığı (0 = bu hafta) |
| `files[].lane` | `max_wait`, `small_quota`, `carbon`, `unscored` |
| `files[].reason` | Sıranın gerekçesi (Türkçe, ekranda doğrudan gösterilebilir) |
| `files[].daily_tco2.{low,central,high}` | Günlük yer değiştirilen emisyon bandı; skorsuz dosyada `null` |
| `files[].effort_hours`, `p_withdraw_12m`, `wait_days`, `generation_mw`, `has_storage` | Dosya bilgileri |
| `needs_confirmation[]` | 5 yıldan uzun süredir bekleyen dosyalar: sıraya konmaz, kurumla teyit edilmek üzere ayrı listelenir (`--include-stale` ile sıraya girer) |

## Duyarlılık

`results/sensitivity.md`: 2021–2023 için CarbonQueue'nun tek bir varsayım değiştiğinde verdiği sonuç
(kapasite ×0,8 / ×1,2, azami bekleme 180 gün, zorunlu kademe sınırsız, sabit efor, küçük proje kotası, 5 yıldan eski dosyalar hariç).
Her varyantta kapasite yeniden kalibre edilir ve FIFO da aynı varsayımla yeniden koşar.

`max_wait_capacity_share` (varsayılan 0,5): zorunlu kademenin haftalık kapasiteden alabileceği azami pay.
1,0 iken kuyruğun çoğu azami beklemeyi aşmışsa CarbonQueue FIFO'ya dönüşür.
