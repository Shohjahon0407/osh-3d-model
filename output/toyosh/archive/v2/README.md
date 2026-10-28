# ToyOsh — bitta surat asosidagi 3D namuna

**Joriy nusxa: go‘sht 4K v2.** [Go‘shtdagi o‘zgarishlar va manba](MEAT_4K.md).
Oldingi nusxa `archive/v1/` papkasida saqlangan.

`toyosh.blend` — tahrirlanadigan sahna. Asosiy model `ToyOsh` sahnasida,
`ToyOsh_Asset` kolleksiyasida. Avvalgi `Scene` va uning obyektlari saqlangan.
Materiallarning ishlatiladigan teksturalari fayl ichiga joylangan.

`toyosh.glb` — marketplace uchun ajratilgan model. Kamera va studiya chiroqlari
eksportga kiritilmagan; teksturalar GLB ichida. Model metrlarda, asos markazi
koordinata boshida, eksport glTF ning Y-up yo‘nalishida.

`preview_top.png`, `preview_angle.png`, `preview_side.png` — Blender Cycles
renderlari, 1200 × 1200, shaffof fon.

- Geometriya: **149 136 uchburchak**, **9 ta mesh**.
- GLB: **20 873 380 bayt** (20,87 MB / 19,91 MiB).
- Go‘sht: **4096 × 4096 PBR xaritalar**, **360 ta ingichka hajmli tola**.
- `preview_meat_4k.png`: **3840 × 2160** yaqin rakursdagi qo‘shimcha render.
- Taxminiy o‘lcham: **28,0 × 27,5 × 5,0 sm**.
- Guruchning **2 420 ta donasi** alohida hajmli geometriya sifatida yaratilgan.
- Model bir tomonga qaragan rasm tekisligidan iborat emas; lagan tagi va taom
  bo‘laklarining yon tomonlari ham geometriyaga ega.

## Tekshirish

GLB Blender’ga qayta import qilindi: mesh va uchburchak sonlari mos.
Geometriya tekshiruvida ochiq chegaralar, non-manifold qirralar va nol yuzali
poligonlar topilmadi. Mustaqil GLB tekshiruvi indekslar, buffer chegaralari,
normal vektorlar, UV va ichki rasmlar yaxlitligini tekshirdi.

`validation.json`, `geometry_audit.json` va `glb_audit.json` tekshiruv dalillarini
saqlaydi. Khronos validator paketi npm ulanishidagi timeout sabab ishga
tushirilmadi; bu natija to‘liq Khronos sertifikatsiyasi sifatida talqin qilinmaydi.

## Aniqlik chegarasi

Manba: `toyosh.jpg`. Surat o‘zgartirilmagan. Lagan diametri 28 sm deb olindi;
balandliklar, yashirin tomonlar va materiallarning fizik qiymatlari taxminiy.
Ko‘rinadigan rang va detallar suratdan, yon tomonlar esa protsedurali
teksturalardan olingan. Protsedurali PBR maydonlari PNG teksturalarga hisoblab
yozilgan. Suratdagi keng yoritish farqlari taxminan tekislangan, ammo ayrim
asl yaltiroqlik va soyalar albedoda qolishi mumkin. Bu o‘lchangan fotogrammetrik
skan emas, bitta rasm asosidagi birinchi namuna.

Marketplace’ga yuklash va ilova integratsiyasi bajarilmagan.

## Qayta yaratish tartibi

Loyiha ildizidagi `scripts/` authoring kodini saqlaydi. Manba yo‘li va chiqish
papkasi skriptlarda aniq ko‘rsatilgan. Yangi Blender sessiyasida tartib:
`build_toyosh.py` → `refine_toyosh.py` → host Python/Pillow bilan
`optimize_textures.py` → Blender’da `reload_textures.py` → `polish_toyosh.py` →
`finalize_toyosh.py` → `audit_geometry.py`. Host Python/Pillow bilan
`validate_glb.py` yakuniy binar faylni tekshiradi.

`mcp_run.py` ochiq Blender MCP serveriga `127.0.0.1:9876` orqali ulanadigan
mijozdir. Yakuniy fayl `open_final_scene.py` yordamida ochiq Blender oynasiga
yuklangan. Qurish skriptlarini tayyor sahna ustida qayta ishlatish ko‘zda
tutilmagan; takroriy qurish uchun yangi Blender sessiyasidan foydalaniladi.
