"""Stream Deck key artwork shared by the hardware renderer and web preview."""
import re
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .storage import home

PAGE_SIZE = 128
MAX_PAGES = 8


def page_count(config, ident):
    return config.get("devices", {}).get(ident, {}).get("deck_page_count", 1)


def page_slots(config, ident):
    return config.get("devices", {}).get(ident, {}).get("deck_page_order", list(range(page_count(config, ident))))


def page_slot(config, ident, page):
    return page_slots(config, ident)[page]


def logical_key(key, page=0):
    return page * PAGE_SIZE + key


def binding_allowed(config, ident, control):
    match = re.fullmatch(r"key:(\d+)", control)
    if not match:
        return True
    key = int(match[1])
    return key // PAGE_SIZE in page_slots(config, ident) and config.get("devices", {}).get(ident, {}).get("deck_keys", {}).get(str(key), {}).get("action", "mqtt") == "mqtt"


def validate_artwork(style):
    if not isinstance(style, dict):
        raise ValueError("Tastengestaltung muss ein Objekt sein")
    if style.get("action", "mqtt") not in ("mqtt", "next", "previous", "home", "goto"):
        raise ValueError("Ungültige Tastenfunktion")
    if style.get("action") == "goto" or "target_page" in style:
        if type(style.get("target_page")) is not int or not 1 <= style["target_page"] <= MAX_PAGES:
            raise ValueError("Zielseite: 1 bis 8")
    if "show_page" in style and type(style["show_page"]) is not bool:
        raise ValueError("Seitennummer anzeigen muss ein/aus sein")
    for name in ("background", "text_color"):
        if name in style and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(style[name])):
            raise ValueError("Farbe muss als #RRGGBB angegeben werden")
    for name in ("pressed_background", "pressed_text_color"):
        if style.get(name) and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(style[name])):
            raise ValueError("Farbe muss als #RRGGBB angegeben werden")
    for name in ("icon", "background_image", "pressed_icon"):
        if style.get(name) and not re.fullmatch(r"[0-9a-f]{32}", str(style[name])):
            raise ValueError("Ungültige Bild-ID")
    if not isinstance(style.get("text", ""), str) or len(style.get("text", "")) > 80:
        raise ValueError("Beschriftung: maximal 80 Zeichen")
    if style.get("text_position", "bottom") not in ("top", "center", "bottom"):
        raise ValueError("Ungültige Textposition")
    if style.get("fit", "contain") not in ("contain", "cover"):
        raise ValueError("Ungültige Bildanpassung")
    if type(style.get("font_size", 14)) is not int or not 8 <= style.get("font_size", 14) <= 32:
        raise ValueError("Schriftgröße: 8 bis 32")
    return style


def artwork(config, ident, key, page=0):
    return config.get("devices", {}).get(ident, {}).get("deck_keys", {}).get(str(logical_key(key, page_slot(config, ident, page))), {})


def key_image(size, style, icon="", label="", pressed=False, frame_index=0, page=0, pages=1):
    validate_artwork(style)
    if pressed:
        style = dict(style)
        icon = style.get("pressed_icon") or icon
        for name in ("background", "text_color"):
            if style.get("pressed_" + name):
                style[name] = style["pressed_" + name]
    image = Image.new("RGB", size, style.get("background", "#000000"))
    if not label:
        label = {"next":"Vor", "previous":"Zurück", "home":"Home", "goto":f"Seite {style.get('target_page', 1)}"}.get(style.get("action"), "")
    badge_height = max(10, int(12 * size[0] / 72)) if style.get("show_page") else 0

    def paste(ident, cover=False, box=None, animate=False):
        if not re.fullmatch(r"[0-9a-f]{32}", str(ident)):
            return
        from .icons import frame_path, cached_path
        path = frame_path(ident, frame_index) if animate else cached_path(ident)
        if path.is_file():
            with Image.open(path) as source:
                source = source.convert("RGBA")
                if cover and source.getbbox():
                    source = source.crop(source.getbbox())
                x, y, width, height = box or (0, 0, *size)
                tile = ImageOps.fit(source, (width, height)) if cover else ImageOps.contain(source, (width, height))
                image.paste(tile, (x+(width-tile.width)//2, y+(height-tile.height)//2), tile)

    paste(style.get("background_image", ""), True)
    icon_box = (0, badge_height, size[0], size[1]-badge_height) if badge_height else None
    if label:
        draw = ImageDraw.Draw(image)
        font_size = max(8, int(style.get("font_size", 14) * size[0] / 72))
        for name in ("DejaVuSans.ttf", "C:/Windows/Fonts/segoeui.ttf"):
            try:
                font = ImageFont.truetype(name, size=font_size)
                break
            except OSError:
                continue
        else:
            font = ImageFont.load_default(size=font_size)
        label = str(label)[:80]
        while label and draw.textbbox((0, 0), label, font=font)[2] > size[0]-4:
            label = label[:-1]
        height = draw.textbbox((0, 0), "Ag", font=font)[3] + 4
        position = style.get("text_position", "bottom")
        if label and position in ("top", "bottom"):
            reserved = min(size[1]-badge_height-1, height+2)
            icon_box = (0, badge_height+reserved if position == "top" else badge_height, size[0], size[1]-badge_height-reserved)
        y = {"top": badge_height+2, "center": badge_height+(size[1]-badge_height-height)//2, "bottom": size[1]-height}[position]
    paste(icon, style.get("fit") == "cover", icon_box, True)
    if label:
        draw = ImageDraw.Draw(image)
        draw.text((size[0]//2, y), label, fill=style.get("text_color", "#ffffff"), anchor="mt", font=font,
                  stroke_width=1, stroke_fill=style.get("background", "#000000"))
    if badge_height:
        draw = ImageDraw.Draw(image)
        badge_font = ImageFont.load_default(size=max(8, badge_height-2))
        draw.text((size[0]-2, 0), f"{page+1}/{pages}", fill=style.get("text_color", "#ffffff"), font=badge_font, anchor="rt")
    return image
