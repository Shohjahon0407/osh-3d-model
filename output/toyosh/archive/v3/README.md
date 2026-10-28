# ToyOsh — joriy nusxa v3

Go‘sht yuborilgan andozalar asosida yirtilgan mushak bog‘lamlari va sochilgan
parchalar shaklida qayta qurildi. [Geometriya haqida](MEAT_SHAPE_V3.md).
[4K material manbasi va prompt](MEAT_4K.md).

- `toyosh.blend` — tahrirlanadigan model; `ToyOsh` sahnasi, `ToyOsh_Asset` kolleksiyasi.
- `toyosh.glb` — barcha teksturalari ichida, kamera va studiya chiroqlarisiz.
- `preview_meat_4k.png` — 3840 × 2160 yaqin rakurs.
- `preview_meat_shape.png` — teksturasiz shakl renderi.
- `preview_top.png`, `preview_angle.png`, `preview_side.png` — umumiy rakurslar.

Model: **149,696 uchburchak**, **9 mesh**.
GLB: **19,150,444 bayt** (19.15 MB / 18.26 MiB).
O‘lcham taxminan **28.0 × 27.5 × 6.6 sm**.
Go‘sht xaritalari **4096 × 4096**. Oldingi `Scene` va uning obyektlari saqlangan.

Go‘sht: 16 ta yoriqli o‘zak, 96 ta mushak bog‘lami,
18 ta sochilgan parcha, 120 ta yirtilgan ingichka uch,
12 ta yog‘ bo‘lagi va 11 ta yopishgan guruch donasi.
Guruch, sabzi va laganning geometriyasi saqlangan; guruch asosidan eski go‘sht tasvir izi tozalangan.

GLB qayta import, topologiya va mustaqil buffer/UV/normal/rasm tekshiruvlaridan o‘tgan.
Dalillar: `validation.json`, `geometry_audit.json`, `glb_audit.json`,
`meat_shape_v3.json`, `meat_material_preservation.json`.
Bu statik kontaktga moslangan model; o‘lchangan skan yoki dinamik fizik simulyatsiya emas.
Marketplace yuklash va ilova integratsiyasi bajarilmagan.

Oldingi nusxalar: `archive/v1/` va `archive/v2/`.
