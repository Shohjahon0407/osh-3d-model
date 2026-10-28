# Zich guruch va pishgan sabzi — v4

Asosiy uyum **10 000 ta hajmli guruch donasi**dan iborat: 6 500 ta batafsil
dona, 3 000 ta pastki qatlam donasi va 500 ta oraliq to‘ldiruvchi dona.
Go‘sht ustidagi avvalgi 11 ta yopishgan guruch donasi ham saqlangan.

Boshlang‘ich joylashuv olti qatlam va yon chetni qoplaydigan donalardan tuzilgan.
Keyin olti rakursdan ichki asos ko‘rinadigan nuqtalar aniqlanib, ko‘rinmay turgan
pastki donalarning bir qismi shu oraliqlarga ko‘chirilgan. Umumiy dona soni va
poligon budjeti oshirilmagan. 160 × 160 nurlik tekshiruvda ochiq ichki asosning
eng katta ulushi **0,102%**; yirik silliq maydonlar yopilgan, tabiiy mayda
soyali oraliqlar qolgan.

90 ta sabzi bo‘lagi: uzunligi 12–40 mm, eni 3–7 mm, qalinligi 2–4 mm.
Kesimlari yumaloqlashtirilgan, qalinligi va uchlari notekis, pishgandek egilgan;
ko‘pchiligi sariq/tillarang, oz qismi to‘q sariq. Guruch bilan aralashib,
ayrim joylari uyum ichiga botgan. Guruch va sabzi uchun yangi 1K PBR rang,
normal va ORM xaritalari yaratilgan; metallik 0, yoritish va soya geometriya
va sahna chiroqlaridan olinadi.

## Go‘sht va tayanch

Go‘shtning shakli, topologiyasi va UV xaritalari saqlangan. Guruhlar faqat
vertikal ko‘chirilgan; ularga bog‘langan tolalar, yog‘ va yopishgan donalar ham
o‘z guruhiga birga ko‘chgan. Maksimal shakl xatosi hisobda 0.

Yangi joylashuv haqiqiy guruch/sabzi meshlariga hamda oldin qo‘yilgan yo‘g‘on
mushak o‘zaklariga tayangan. Ingichka erkin tolalar boshqa katta bo‘lakka
tayanch bo‘la olmaydi. Har bir katta guruh va sochilgan parchada tayanch
kontakti qayd qilingan. Bu statik kontaktga moslash, dinamik fizik simulyatsiya emas.

4K go‘shtning uchta rasm xaritasi v3 GLB ichidagi rasmlar bilan SHA-256 bo‘yicha
bir xil. `meat_material_preservation.json` buning dalilini saqlaydi.

## Natija va tekshirish

- **348 892 uchburchak**, **10 ta mesh**.
- GLB: **31 271 616 bayt** — **29,82 MiB**.
- Tanlangan limitlar: **350 000 uchburchak**, **35 MiB**.
- Donalar va sabzining maksimal hisoblangan lagan yuzasiga kirishi 0,027 mm;
  bu 0,25 mm geometrik toleransdan kichik. Lagan ostidan chiqish aniqlanmagan.
- GLB qayta import qilindi; indekslar, bufferlar, UV, normal vektorlar,
  rasmlar yaxlitligi va 4K xaritalar tekshirildi.
- Topologiya tekshiruvida ochiq/non-manifold qirra va nol yuzali poligon topilmadi.

`food_geometry_audit_v4.json` dagi sabzi uchun yuqori/pastki nurlar oralig‘i
konservativ tekshiruvdir: kesishgan ikki sabzi orasidagi bo‘shliq ham shu
vertikal intervalga kirishi mumkin. U to‘liq hajmli penetratsiya testi emas.

## Ko‘rish va fayllar

- `toyosh.blend`, `toyosh.glb` — joriy nusxa.
- `preview_rice_carrot_4k.png` — 3840 × 2160 guruch-sabzi yaqin renderi.
- `preview_meat_4k.png` — go‘sht va yangi uyum bilan yangilangan yaqin render.
- `preview_top.png`, `preview_angle.png`, `preview_side.png` — umumiy rakurslar.
- `preview_front_low.png`, `preview_back_low.png`, `preview_left_low.png`,
  `preview_right_low.png` — to‘rtta past rakurs.
- `preview_meat_shape.png` — yangi uyumning teksturasiz geometriya ko‘rinishi.
- `archive/v3/` — ish boshlanishidan oldingi model va renderlar.

Hisobotlar: `food_v4.json`, `food_geometry_audit_v4.json`, `validation.json`,
`geometry_audit.json`, `glb_audit.json`.

Authoring ketma-ketligi: `build_dense_food_v4.py` → `refine_food_coverage_v4.py`
→ `tune_food_materials_v4.py` → `compress_food_v4_textures.py` →
`reload_food_v4_textures.py` → `render_shape_draft.py` → `finalize_toyosh.py`
→ `render_food_low_views_v4.py` → audit skriptlari. Qayta qurish v3 zaxirasidan
boshlanadi; avvalgi 4K go‘sht manbalari o‘zgartirilmaydi.
