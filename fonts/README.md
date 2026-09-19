# Fonts

Used only to render synthetic Urdu text. All are SIL Open Font License 1.1
(licence texts next to each font), sourced from the google/fonts repository.

| File | Style | Notes |
|---|---|---|
| NotoNastaliqUrdu.ttf | Nastaliq | variable weight |
| Gulzar-Regular.ttf | Nastaliq | |
| Lateef-Regular.ttf | Naskh-like | |
| NotoNaskhArabic.ttf | Naskh | variable weight |
| ScheherazadeNew-Regular.ttf | Naskh | |

Jameel Noori Nastaleeq (the font of most Pakistani print) is not openly licensed and is not included.
To add a font: drop the file here and add a `FontSpec` line in `urdulens/fonts.py`.
Text shaping needs Pillow with RAQM (the normal `pip install pillow` wheels include it).
