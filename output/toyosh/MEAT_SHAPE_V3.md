# Pishgan, yirtilgan go‘sht shakli — v3

Bu go‘sht shaklining v3 bosqichi haqidagi tarixiy yozuv. Joriy v4 da shu shakl
saqlanib, go‘sht guruhlari yangi guruch uyumiga joylashtirilgan:
[Guruch va sabzi v4](FOOD_V4.md). Quyidagi umumiy v3 poligon soni va
non-meat saqlanishi v3 bosqichiga tegishli.

Go‘sht geometriyasi yuborilgan to‘rtta andozaga qarab qayta qurildi. Eski katta,
uzluksiz ustki qobiq va cho‘zilgan yon devorlar olib tashlandi.

- 16 ta turlicha hajmli uyum; ichida yoriqlari geometriyada o‘yilgan 16 ta
  notekis mushak o‘zagi bor.
- 48 ta yo‘g‘on va 48 ta ingichkaroq mushak bog‘lami. Ayrimlari bir uchidan
  uzilib, tarqalib chiqqan; boshqalarida qalinroq pishgan bo‘lak saqlangan.
- 18 ta alohida sochilgan parcha, 120 ta yirtilgan ingichka uch va 12 ta mahalliy
  jelatinli yog‘ bo‘lagi.
- Nam go‘sht yuzasiga 11 ta guruch donasi biriktirilgan.
- Oldingi 4096 × 4096 rang, normal va ORM xaritalari o‘zgartirilmagan.
  `meat_material_preservation.json` v2 va v3 ichidagi shu uchta rasmning
  SHA-256 tengligini qayd qiladi.

## Tayanch va shakl

Uyumlar haqiqiy guruch, sabzi va oldin qo‘yilgan go‘sht meshlariga pastga ray-cast
qilib joylashtirilgan. Har uyumda kamida bitta tayanch kontakti tekshirilgan.
Yirtilgan tolalarning ildizi go‘shtning haqiqiy yuzasidan olinadi, erkin uchlari
pastga egiladi. Bu statik kontaktga moslash, dinamik fizik simulyatsiya emas.

O‘zaktagi yoriqlar, bog‘lamlar orasidagi ochiq joylar va notekis uchlar modelning
geometriyasidir. `preview_meat_shape.png` teksturasiz shaklni ko‘rsatadi.

Guruch, sabzi va laganning mavjud geometriyasi hash bo‘yicha saqlangan. Faqat
eski go‘sht tasviri pastdan ko‘rinib qolmasligi uchun guruch asosidagi eski
go‘sht izlari tozalangan; lagan tasviri o‘zgartirilmagan. Yog‘li ko‘rinish katta
uzluksiz shaffof qobiq orqali emas, material roughness va mahalliy yog‘ orqali
beriladi.

## Fayllar va tekshirish

- `toyosh.blend` — tahrirlanadigan yakuniy nusxa.
- `toyosh.glb` — kamera va studiya chiroqlarisiz, teksturalari ichiga joylangan.
- `preview_meat_4k.png` — 3840 × 2160 yaqin rakurs.
- `preview_meat_shape.png` — teksturasiz geometriya renderi.
- `preview_top.png`, `preview_angle.png`, `preview_side.png` — umumiy rakurslar.
- `meat_shape_v3.json` — tarkib, kontaktlar va andoza fayllari.
- `validation.json`, `geometry_audit.json`, `glb_audit.json` — qayta import,
  topologiya, bufferlar, UV, normal vektorlar va 4K rasmlar tekshiruvi.
- `archive/v2/` — oldingi ko‘rinishning zaxirasi.

Joriy model: **149 696 uchburchak**. Tangent oqimi GLB ichiga takroran yozilmaydi;
glTF ko‘ruvchi uni normal va UV bo‘yicha hisoblaydi. 4K xaritalar va geometrik
normal vektorlar saqlangan, Blender’da qayta import tekshiriladi.

Authoring: `rebuild_pulled_meat.py` → tozalangan guruch asosini JPEG sifatida
saqlash → `pack_clean_rice_bed.py` → `render_shape_draft.py` →
`finalize_toyosh.py` → `audit_geometry.py` → `validate_glb.py`.

Andozalar o‘lchangan fotogrammetrik to‘plam emas; o‘lchamlar, orqa tomonlar va
ichki tuzilish taxminiy. Maqsad — har rakursdan tekshiriladigan, pishib
tolalarga ajralgan go‘sht shaklini yaratish.
