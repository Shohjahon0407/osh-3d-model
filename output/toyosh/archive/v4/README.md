# ToyOsh — joriy nusxa v4

Guruch va sabzi qayta qurildi: asosiy uyumda **10,000 ta donadan
iborat olti qatlam**, chet va oraliq to‘ldirmalari; **90 ta pishgan sabzi**.
Go‘shtning shakli va 4K xaritalari saqlanib, guruhlari yangi uyumga joylashtirildi.
[Batafsil v4 yozuvi](FOOD_V4.md).

- `toyosh.blend` — `ToyOsh` sahnasi / `ToyOsh_Asset` kolleksiyasidagi tahrirlanadigan nusxa.
- `toyosh.glb` — kamera va studiya chiroqlarisiz, teksturalari ichiga joylangan nusxa.
- `preview_rice_carrot_4k.png` — 3840 × 2160 guruch-sabzi yaqin renderi.
- `preview_meat_4k.png` — yangi uyumdagi go‘shtning yaqin renderi.
- `preview_top.png`, `preview_angle.png`, `preview_side.png` — umumiy rakurslar.
- `preview_front_low.png`, `preview_back_low.png`, `preview_left_low.png`, `preview_right_low.png` — past rakurslar.
- `preview_meat_shape.png` — teksturasiz geometriya.

**348,892 uchburchak**, **10 mesh**;
GLB **31,271,616 bayt** (29.82 MiB).
Limitlar: **350 000 uchburchak / 35 MiB**.
O‘lcham: taxminan **28.0 × 27.5 × 6.3 sm**.
Go‘sht xaritalari 4096 × 4096, yangi guruch/sabzi xaritalari 1024 × 1024.

GLB qayta import qilindi; bufferlar, indekslar, normal va UV, ichki rasmlar,
qatlamlar zichligi va geometriya tekshirildi. v3 go‘sht rasm xaritalari bilan
SHA-256 tengligi tasdiqlangan. Avvalgi `Scene` va uning obyektlari saqlangan.

Hisobotlar: `food_v4.json`, `food_geometry_audit_v4.json`, `validation.json`,
`geometry_audit.json`, `glb_audit.json`, `meat_material_preservation.json`.
Bu statik joylashtirilgan vizual model; o‘lchangan skan yoki dinamik simulyatsiya emas.
Marketplace’ga yuklash va ilova integratsiyasi bajarilmagan.

Oldingi nusxalar: `archive/v1/`, `archive/v2/`, `archive/v3/`.
Tarixiy yozuvlar: [4K material manbasi](MEAT_4K.md), [v3 go‘sht shakli](MEAT_SHAPE_V3.md).
