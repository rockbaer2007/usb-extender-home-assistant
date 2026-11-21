# Sources and modifications

- MDI: `@mdi/svg` 7.4.47, https://registry.npmjs.org/@mdi/svg/-/svg-7.4.47.tgz
  / https://github.com/Templarian/MaterialDesign-SVG. Only 40 non-brand symbols
  named in catalog.json are vendored. Original SVG files are unchanged.
  Pictogrammers licence and Apache-2.0 text are included.
- CSS Color Icons 1.0, Crafty Lime: user-supplied
  `CSS_Color-1.0.0-windows_mac/com.craftylime.csscolors.sdIconPack/icons/`.
  All 147 background SVGs are copied without changes. The supplied MIT notice
  and full MIT permission text are included.
- Generated derivatives combine a CSS background with a contrasting MDI path,
  size 48x48, with a readable title and on/off filenames. The source colours
  are preserved; no Elgato or Home Assistant programme code is included.
- Generator: ../build_mdi_favorites.py. No network access is needed to rebuild.
