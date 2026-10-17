# Karbon varsayımları: kaynaklar

`assumptions.toml` içindeki karbon değerlerinin kaynağı ve seçim gerekçesi. Bütün kaynaklar Birleşik Krallık hükümetinin
resmî yayınlarıdır; değerler dosyalardan okunmuştur (erişim: 10 Ekim 2026).

Formül: günlük tCO₂ = üretim MW × 24 × yük faktörü × emisyon faktörü (tCO₂e/MWh).

## Yük faktörü

**Kaynak:** DUKES 2026, Tablo 6.3 "Load factors for renewable electricity generation" (DESNZ, 30 Temmuz 2026).
<https://www.gov.uk/government/statistics/renewable-sources-of-energy-chapter-6-digest-of-united-kingdom-energy-statistics-dukes>

Tabloda iki taban var. "Unchanged configuration" tabanını kullanıyoruz (yıl boyunca kapasitesi değişmeyen santraller):
yıl içinde devreye giren santrallerin kısmi üretimi oranı bozmaz.

| Yıl | Güneş PV | Kara rüzgârı |
|---|---|---|
| 2021 | 10,64 | 23,30 |
| 2022 | 10,82 | 26,94 |
| 2023 | 10,58 | 24,56 |
| 2024 | 9,57 | 25,11 |
| 2025 | 11,08 | 24,08 |
| **2021–2025 ortalaması** | **10,54** | **24,80** |

Kullanılan değerler: güneş 0,105, kara rüzgârı 0,248. Tek yıl yerine beş yıllık ortalama, çünkü hava koşulları yıldan yıla
oynuyor (kara rüzgârı 23,3–26,9).

Sınırlama: değerler UK geneli. Simülasyon yalnızca İngiltere'yi kapsıyor; İngiltere'de güneş biraz daha yüksek, kara rüzgârı
biraz daha düşük olabilir. Yük faktörü sıralamayı etkileyen tek karbon varsayımıdır (rüzgâr/güneş oranı 2,36).

## Emisyon faktörü

Yenilenebilir bir santralin ürettiği 1 MWh'in şebekede neyin yerini aldığı kesin bilinemez; bu yüzden üç seviye
raporluyoruz. Faktör aynı yıl içinde her teknolojiye aynı çarpan olarak uygulanır: **sıralamayı değiştirmez**, yalnızca
raporlanan tonu değiştirir.

| Seviye | Tanım | Kaynak |
|---|---|---|
| Düşük | Şebeke ortalaması, üretim bazlı | Green Book ek rehberi veri tabloları, Tablo 1 ("Grid average, Generation-based") |
| Merkezi | Uzun dönem marjinal, üretim bazlı | Green Book ek rehberi veri tabloları, Tablo 1 ("Long-run marginal, Generation-based") |
| Yüksek | Gaz santrali üretiminin CO₂ yoğunluğu | DUKES 2026, Tablo 5.14 ("Gas", tCO₂/GWh supplied) |

- Green Book ek rehberi: "Valuation of energy use and greenhouse gas emissions for appraisal", veri tabloları 1–19 (DESNZ, Kasım 2023).
  <https://www.gov.uk/government/publications/valuation-of-energy-use-and-greenhouse-gas-emissions-for-appraisal>
- DUKES 2026, Tablo 5.14 (DESNZ, 30 Temmuz 2026).
  <https://www.gov.uk/government/statistics/electricity-chapter-5-digest-of-united-kingdom-energy-statistics-dukes>

**Merkezi değer neden uzun dönem marjinal:** Green Book rehberi, üretimdeki ya da tüketimdeki küçük değişikliklerin etkisi
ölçülürken uzun dönem marjinal faktörün, ayak izi hesabında ise şebeke ortalamasının kullanılmasını söyler. Bir santralin
daha erken devreye girmesi birinci duruma girer. **Üretim bazlı** seçildi, çünkü santral şebekeye üretim noktasında enerji
verir; iletim ve dağıtım kayıpları dahil edilmedi (temkinli taraf).

| Yıl | Düşük | Merkezi | Yüksek |
|---|---|---|---|
| 2021 | 0,198 | 0,255 | 0,377 |
| 2022 | 0,144 | 0,241 | 0,381 |
| 2023 | 0,133 | 0,226 | 0,378 |
| 2024 | 0,138 | 0,210 | 0,377 |
| 2025 | 0,120 | 0,193 | 0,365 |
| 2026 | 0,090 | 0,174 | (2025 değeri) |
| 2027 | 0,067 | 0,154 | (2025 değeri) |
| 2028 | 0,058 | 0,133 | (2025 değeri) |

**Hangi yılın faktörü:** iznin erken çıkmasıyla kazanılan üretim, izin yılında değil santral işletmeye girdiğinde gerçekleşir.
Bu yüzden faktör kuyruk yılı + 2 yıl için okunur (`operation_lag_years`). REPD'de izinden işletmeye geçen süre, tamamlanan
güneş ve kara rüzgârı projelerinde medyan yaklaşık 1 yıl (363 gün); ancak yeni izinlerin çoğu henüz işletmede olmadığı için bu
değer aşağı yanlı. Faktörler yıllar içinde düştüğünden 2 yıl temkinli taraftır.

Sınırlamalar:
- Green Book değerleri 2023'te yayımlanmış projeksiyonlardır; 2023 sonrası yıllar gerçekleşen değil, öngörülen değerdir.
- Yüksek seviye yalnızca CO₂'dir (CH₄ ve N₂O hariç) ve gelecek yıllar için son gerçekleşen yılın (2025) değeri kullanılır.

## Karşılaştırma için (kullanılmıyor)

| Değer | tCO₂e/MWh | Kaynak |
|---|---|---|
| Şirket raporlaması dönüşüm faktörü 2026, "UK electricity – electricity generated" | 0,131 | DESNZ, GHG conversion factors 2026 (flat file, Temmuz 2026) |
| Tüm yakıtların gerçekleşen CO₂ yoğunluğu, 2023 / 2024 / 2025 | 0,175 / 0,154 / 0,147 | DUKES 2026, Tablo 5.14 ("All fuels") |

Bunlar şebeke ortalamasıdır ve düşük seviyeyle aynı büyüklüktedir. Dönüşüm faktörleri şirketlerin ayak izi raporlaması
içindir; DUKES 5.14'ün notu da iki serinin yöntem farkı yüzünden birbirini tutmadığını belirtir.
<https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2026>

## Türkiye (yalnızca backend motoru, `country = "TR"`)

Geçmiş simülasyon ve canlı kuyruk İngiltere'dir. Yüklenen bir projenin ülkesi Türkiye ise motor aşağıdaki resmi faktörleri
kullanır. Üç seviye İngiltere'dekiyle aynı mantıkta:

| Seviye | Değer | Ne | Kaynak |
|---|---|---|---|
| Düşük | 0,434 tCO₂-eşd./MWh | Türkiye geneli elektrik üretimi emisyon faktörü, 2023 (ortalama, brüt üretim başına) | ETKB EVÇED, "Türkiye Elektrik Üretimi ve Elektrik Tüketim Noktası Emisyon Faktörleri Bilgi Formu", ETKB-EVÇED-FRM-042 Rev.01, hesaplama dönemi 2023, yayım 26.12.2025 |
| Merkezi | 0,6345 tCO₂/MWh | Birleşik marj (güneş ve rüzgâr), 2021: yeni yenilenebilir üretimin yer değiştirdiği emisyon | ETKB EVÇED, "Türkiye Ulusal Elektrik Şebekesi Emisyon Faktörü Bilgi Formu", ETKB-EVÇED-FRM-039 Rev.03, hesaplama dönemi 2021, yayım 18.03.2024; UNFCCC CDM Tool 07 v07.0 |
| Yüksek | 0,7279 tCO₂/MWh | Faaliyet temelli marj (devredeki fosil santraller), 2021 | Aynı form |

Aynı formdaki diğer değerler: gelişim temelli marj 0,3541; birleşik marj (diğer yenilenebilir) 0,5410 tCO₂/MWh.
Kaynak dosyalar: <https://enerji.gov.tr/Media/Dizin/EVCED/tr/%C3%87evreVe%C4%B0klim/%C4%B0klimDe%C4%9Fi%C5%9Fikli%C4%9Fi/TUESEmisyonFktr/Belgeler/TUESEF_Bilgi_Formu.pdf>
ve <https://enerji.gov.tr/Media/Dizin/EVCED/tr/%C3%87evreVe%C4%B0klim/%C4%B0klimDe%C4%9Fi%C5%9Fikli%C4%9Fi/EmisyonFaktorleri/2023_Turkiye_Elektrik_UretimiveElektrik_Tuketim_Noktasi_Emisyon_Faktorleri.pdf>

Notlar:
- Marj faktörleri yalnızca CO₂, üretim faktörü CO₂-eşdeğeri; fark %1'in altında.
- Tablolar tek yıllık; motor her yıl için en yakın önceki yılın değerini kullanır (İngiltere'deki gibi kuyruk yılı + 2
  yıl aranır, Türkiye'de 2021 ve 2023 değerleri kullanılır).
- Türkiye şebekesi kömür ağırlıklı olduğu için faktörler İngiltere'nin 3–5 katı: aynı MWh beyanı Türkiye'de çok daha
  büyük günlük etki verir.
- **Yük faktörü yok.** Resmi bir güneş/rüzgâr kapasite faktörü bulunamadı; yıl sonu kurulu güç ile yıllık üretimden
  hesaplamak, kurulumun yıl içinde hızla arttığı yıllarda yanıltıcı. Bu yüzden Türkiye'deki güneş/rüzgâr projesi MW'tan
  hesaplanmaz; belgedeki yıllık üretim (MWh) beyanı kullanılır, beyan yoksa proje skorsuz yoldan gider.
- Tanımlı olmayan bir ülkede yalnızca yıllık tCO₂e beyanı kullanılabilir (ülke faktörü gerekmez); MWh beyanı ve MW
  formülü için o ülkenin faktörleri `assumptions.toml` içinde `[carbon.country.XX]` altına eklenmelidir.

## Yansıma oranı (α)

α bir kaynaktan gelmez; bizim varsayımımızdır: iznin N gün erken çıkmasının ne kadarının işletmeye N gün erken girmeye
yansıdığı. %20 / %50 / %100 olarak ayrı raporlanır ve emisyon faktörü belirsizliğiyle karıştırılmaz.
