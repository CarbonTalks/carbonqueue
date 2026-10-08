# REPD veri profili (Temmuz 2026 sürümü)

Kaynak: `REPD_Publication_Q2_2026.csv` (GOV.UK). Sayılar `scripts/profile_repd.py` ile yeniden üretilir; ham çıktı `reports/repd_profile_raw.txt`.

**Genel:** 14.657 satır, 53 kolon. En son kayıt güncellemesi 24.07.2026; veri kesim tarihi olarak bu tarih (24.07.2026) kullanılıyor.

## 1. Önceki yazışmalardaki sayıların kontrolü

| İddia | Veri | Durum |
|---|---|---|
| 1.539 karar bekleyen başvuru | 1.539 (durumu "Planning Application Submitted") | ✅ |
| Doluluk: başvuru tarihi %98, izin %68,5, red %14,5, geri çekilme %6,1 | %98,0 / %68,5 / %14,5 / %6,1 | ✅ |
| 826 "Revised" kayıt | 826 | ✅ |
| 2.678 batarya, 533 Kuzey İrlanda | 2.678 / 533 | ✅ |
| 6.890 başvuru sahibi | 6.890 | ✅ |
| **493 planlama kurumu** | **388.** 493 sayısı, ham verideki baştaki/sondaki boşluklar yüzünden aynı kurumların iki kez sayılmasından geliyor | ❌ düzeltildi |

## 2. Kararları etkileyen bulgular

### 2.1 "Revised" kayıtlar kopya değil, gerçek başvurular
826 Revised kaydın her biri kendi sonucu olan eski bir başvuru: %37'sinde red, %27'sinde geri çekilme, %22'sinde izin tarihi var. %97'si `New REPD Ref` alanıyla yeni başvuruya bağlanıyor.
→ **Silinmemeli.** Her başvuru ayrı bir örnek olarak kalır; zincirdeki bütün başvurular aynı `chain_id`'yi alır ve hep aynı bölümde (eğitim/doğrulama/test) tutulur. "Yeniden başvuru mu" özelliği eklenebilir.

### 2.2 "İlk karar" tanımı: veride uygulanabilir
- Temyizle verilen izin `Planning Permission Granted` alanının üzerine yazılmış (577 temyiz izninin 531'inde iki tarih aynı). Bu yüzden `ilk karar = min(izin, red)` alındığında kurumun ilk kararı olan red yakalanıyor ve temyiz bunun dışında kalıyor.
- **90 temyiz redsiz açılmış.** Bunlar büyük olasılıkla kurumun süresinde karar vermediği için açılan temyizler (non-determination). Öneri: dosyanın kurum kuyruğundan çıktığı an temyiz tarihi kabul edilir ve "karar" olayı sayılır.

### 2.3 Sonucu olan ama tarihi olmayan kayıtlar
Başvuru tarihi olup karar ya da geri çekilme tarihi olmayan 1.929 kayıt var: 1.539'u gerçekten bekliyor, 136'sı Revised. **254'ünün durumu bir sonuç olduğunu söylüyor ama tarih yok** (Operational 84, Abandoned 72, Expired 30 …).
→ Bunlar sansürlü sayılırsa model "hiç karar çıkmadı" diye yanlış öğrenir. **Eğitimden çıkarılmalı** ve sayısı raporlanmalı.

### 2.4 Hatalı tarihler
Küçük sayılar, ama kurala bağlanmalı:
- Karar başvurudan önce: 10
- Geri çekilme başvurudan önce: 7
- Hem geri çekilme hem karar: 9 (önce gelen olay alınır)
- Kesim tarihinden (24.07.2026) sonraki tarihler: başvuru 1 (27.11.2026), izin 1 (15.12.2026)
- Başvuru tarihi yok: 291 (çoğu Operational)
- 1 kayıt ABD tarih biçiminde, okuyucuda düzeltildi

### 2.5 Yıllık kohortlar: test için 2024 uygun

| Başvuru yılı | n | Karar | Geri çekilme | Açık | Açık % |
|---|---:|---:|---:|---:|---:|
| 2015 | 829 | 749 | 59 | 9 | 1,1 |
| 2016 | 156 | 110 | 17 | 3 | 1,9 |
| 2017 | 199 | 133 | 10 | 13 | 6,5 |
| 2018 | 227 | 153 | 15 | 16 | 7,0 |
| 2019 | 328 | 251 | 28 | 29 | 8,8 |
| 2020 | 396 | 325 | 10 | 49 | 12,4 |
| 2021 | 849 | 731 | 38 | 73 | 8,6 |
| 2022 | 1.454 | 1.259 | 64 | 116 | 8,0 |
| 2023 | 1.864 | 1.598 | 87 | 170 | 9,1 |
| 2024 | 1.738 | 1.385 | 76 | 274 | 15,8 |
| 2025 | 1.861 | 1.222 | 55 | 582 | 31,3 |

(Açık sayısına Revised ve tarihsiz kayıtlar da dahil.)

- 2023'ün %91'i, 2024'ün %84'ü sonuçlanmış. Doğrulama 2023, test 2024 planı veriyle uyumlu.
- **2016–2018'de başvuru sayısı çöküyor** (2015: 829 → 2016: 156). Bunun sebebi teşviklerin kesilmesi; başvuru yılı özelliğinin gerekli olduğunu gösteriyor. Aynı sebeple **2019 ve 2020 simülasyon kuyrukları küçük** (328 ve 396 başvuru, bunun da yalnızca bir kısmı İngiltere'de).
- Geri çekilme toplamda nadir (yıllık %3–8). PR-AUC düşük taban oranla değerlendirilmeli.

### 2.6 1 MW altı projeler 2021'den önce de var
1 MW altı projelerin payı 2017'de %3, 2018'de %20, 2019'da %35, 2020'de %26. Eşik 2021'de değişmiş olsa da bu projeler büyük olasılıkla sonradan geriye dönük eklenmiş.
→ "2021 öncesinden yalnızca ≥1 MW" kuralı yine geçerli ve tutarlı, ama 2018–2020 kohortlarından küçük bir parçayı da çıkarıyor. Bunu bilerek yapıyoruz.

### 2.7 Kapasite eksik: 1.345 kayıt (%9)
Eksiklerin 592'si batarya, 488'i güneş, 106'sı kara rüzgârı. Hem ≥1 MW filtresini hem karbon hesabını etkiliyor.
→ **Berke'ye bildirilmeli.** Karbon tarafında kapasitesi olmayan projeler skorlanamaz ve "skor yok" yoluna düşer.

### 2.8 Yasal süreler sıklıkla aşılıyor
İlk karara kadar geçen süre: medyan 123 gün. Kararların %26'sı 8 hafta, %41'i 13 hafta, %47'si 16 hafta içinde çıkıyor.
→ Anlatı için güçlü bir veri ("kararların yarısından fazlası 16 haftayı aşıyor"). EDF'nin neden kaldırıldığını da destekliyor.
`Solar Site Area (sqm)` alanı güneş projelerinin %25'inde dolu. Bu, 1 hektar eşiğini yalnızca bir kısım güneş projesi için çıkarabilir; EDF'yi geri getirmeye yetmez.

### 2.9 Özel izin yolları (simülasyondan çıkacaklar)

| Kurum | n | İçerik |
|---|---:|---|
| Scottish Government (S36) | 639 | 336 kara rüzgârı, 219 batarya |
| The Planning Inspectorate – National Infrastructure | 129 | karışık |
| Welsh Government (NSIP) | 90 | |
| Marine Scotland | 44 | deniz |
| DECC (S36) | 40 | çoğu deniz üstü |
| Marine Management Organisation | 3 | deniz |

Simülasyon yalnızca İngiltere'yi kapsadığı için İskoçya ve Galler yolları zaten dışarıda kalıyor; İngiltere'de çıkan yalnızca National Infrastructure ve deniz üstü rüzgâr. **Model eğitiminde bu kayıtlar `special_route` bayrağıyla tutulabilir.**

### 2.10 Canlı kuyruk (demo)

| Kapsam | Bekleyen | Medyan yaş | >2 yıl | >5 yıl (`stale_or_uncertain`) |
|---|---:|---:|---:|---:|
| Tüm UK | 1.539 | 1,21 yıl | 466 | 101 |
| İngiltere, özel yol ve deniz üstü hariç | **936** | 1,07 yıl | 253 | 38 |

İngiltere kuyruğu: güneş 555, **batarya 294 (%31)**, kara rüzgârı 42, anaerobik çürütme 25.
→ **Canlı kuyruğun üçte biri karbon skoru olmayan batarya.** Depolama için ayrı yol kararı demoda doğrudan görünecek; Berke ve Büşra'nın bilmesi gerek.

### 2.11 Başvuru sahibi
"Private Developer" 441, "Unknown" 81 kayıt → eksik veri olarak işlenecek. Boş başvuru sahibi alanı yok.

## 3. 7 açık karar için öneriler

| # | Karar | Öneri (veriye göre) |
|---|---|---|
| 1 | İlk karar tanımı | `min(izin, red, SoS izin, SoS red)`. Redsiz temyizde temyiz tarihi karar sayılır. Geri çekilme karardan önceyse olay geri çekilmedir |
| 2 | Filtreler | Eğitim: tarihi olmayan ya da sonucu tarihsiz 254 kayıt ve hatalı tarihli kayıtlar çıkar; özel yollar bayrakla kalır. Simülasyon: yalnızca İngiltere, National Infrastructure ve deniz üstü rüzgâr hariç; >5 yıl bekleyenler `stale_or_uncertain` (38 dosya) |
| 3 | Gerçek sayılar | Yukarıdaki tablolar. Canlı kuyruk 936; ortak veri setinde kapsam dışı teknolojiler (hidrojen vb.) de çıkınca **921** (36 tanesi `stale_or_uncertain`) |
| 4 | Biyoenerji | Açık: Berke ile. Canlı kuyrukta yalnızca 25 AD + 7 diğer var; dışarıda bırakmak demoyu etkilemez |
| 5 | Azami bekleme | Öneri: 365 gün (13 haftanın yaklaşık 4 katı; kararların %79'u bu sürede çıkıyor; 180 günde %61). Duyarlılık için 180 gün |
| 6 | Yıl yıl eğitim | 2019 ve 2020 kuyrukları küçük. Öneri: ana sonuç 2021–2023; 2019–2020 ekte |
| 7 | Simülatör kuralları | Açık: Berke ile |
