# Go‘sht 4K — v2

Bu v2 material bosqichining tarixiy yozuvi. Joriy geometriya v3 ga yangilangan:
[Pishgan go‘sht shakli](MEAT_SHAPE_V3.md). Quyidagi 4K rang, normal va ORM
manbalari v3 da ham saqlangan; v2 model va renderlar `archive/v2/` da.

Go‘sht uchun alohida **4096 × 4096** rang, tangent normal va ORM xaritalari
tayyorlandi. Tolalar bo‘lakning uzun yo‘nalishiga mos UV bilan joylashtirilgan.
Tashqi yuzada to‘qroq pishgan qobiq, kesimda ingichka mushak tolalari, yog‘li
joylarda esa pastroq roughness va yumshoq coat akslanishi ishlatilgan.

**360 ta ingichka hajmli tola** go‘shtning haqiqiy yuzasiga ray-cast orqali
biriktirilgan. Ularning taxminiy diametri 0,11–0,23 mm. Yirtiq qirralar,
notekis yon devorlar va ko‘tarilgan jelatinli yog‘ bo‘laklari ham geometriyaga ega.
Guruch, sabzi, lagan va boshqa qismlarning geometriya hamda material tayinlovlari
oldingi nusxa bilan bir xil ekani hash orqali tekshirildi.

- Model: **149 136 uchburchak**.
- GLB: **20 873 380 bayt** (20,87 MB / 19,91 MiB).
- `preview_meat_4k.png`: **3840 × 2160** yaqin rakursdagi Blender renderi.
- `toyosh.blend` va `toyosh.glb`: yangilangan asosiy fayllar.
- `archive/v1/`: oldingi model, GLB va renderlar.

## 4K aniqlik va manba

Material manbasi **built-in image_gen** bilan, `toyosh.jpg` dagi pishgan
go‘shtning ko‘rinishi va rangini yo‘naltiruvchi reference sifatida ishlatib
yaratildi. [To‘liq prompt](material_sources/generation_prompt.txt).
Manba: [cooked_meat_source.png](material_sources/cooked_meat_source.png).

Generator qaytargan rang manbasi 1254 × 1254. Rang 4K ga qayta namunalangan;
ingichka fibril relyefi, rangning mayda o‘zgarishlari, yog‘ va moy roughness
maydonlari **4096 pikselli maydonda yangidan hisoblangan**. Bu 4K xaritalar
asl suratdan fizik ravishda o‘lchangan yoki native 4K fotografik skan degani emas.

Rang xaritasi JPEG, normal va ORM esa PNG. Barcha xaritalar 4096 × 4096 holatda
GLB ichiga joylangan. Normal yo‘nalishlari siqish uchun 256 rangga kvantlangan:
5000 ta tekshirish namunasida o‘rtacha burchak xatosi 2,54°, 95-persentil 4,47°.
Piksellar soni kamaytirilmagan. Go‘shtning metallic qiymati 0, AO kanali esa 1; teksturaga qo‘shimcha
qotirilgan soya qo‘shilmagan.

## Tekshirish va qayta yaratish

`meat_4k_material.json` xaritalar va manba o‘lchamini; `meat_upgrade.json`
geometriya va o‘zgarmagan qismlar tekshiruvini; `normal_compression.json`
normal siqish xatosini qayd qiladi. Yakuniy GLB va geometriya tekshiruvlari
`validation.json`, `glb_audit.json`, `geometry_audit.json` da.

Authoring tartibi: `bake_meat_4k_maps.py` (Blender background) →
`compress_meat_4k_maps.py` (Python/Pillow) → v1 sahnada `upgrade_meat_4k.py`
(Blender MCP) → `reload_textures.py` → `tune_meat_finish.py` → `finalize_toyosh.py` → `audit_geometry.py` → `validate_glb.py`.
Finalizer tashqi go‘sht materialining rang ko‘paytuvchisini standart glTF
`baseColorFactor` sifatida aniq saqlaydi va qayta importni tekshiradi.

Yakuniy finish: albedo saturation 0,84 va brightness 0,95; roughness 0,78 ko‘paytuvchi bilan namroq yuzaga moslangan; coat 0,30 va normal strength 0,40.
