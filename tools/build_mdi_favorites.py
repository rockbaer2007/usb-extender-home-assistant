"""Build small, offline HA favourite packs from the vendored MDI/CSS SVG sources."""
import argparse
import copy
import hashlib
import html
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name("mdi-favorites-source")
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)


def catalog():
    return json.loads((SOURCE / "catalog.json").read_text(encoding="utf-8"))


def background(color):
    root = ET.fromstring((SOURCE / "colors" / (color + ".svg")).read_bytes())
    match = re.search(r"#[0-9a-fA-F]{6}", ET.tostring(root, encoding="unicode"))
    if not match:
        raise ValueError("Missing RGB colour: " + color)
    return root, match.group().lower()


def foreground(rgb):
    def linear(channel):
        value = int(channel, 16) / 255
        return value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4
    luminance = sum(weight * linear(rgb[pos:pos+2]) for weight, pos in ((.2126, 1), (.7152, 3), (.0722, 5)))
    return "#000000" if (luminance + .05) / .05 >= 1.05 / (luminance + .05) else "#ffffff"


def compose(color, mdi):
    root, rgb = background(color)
    root = copy.deepcopy(root)
    # Flatten the supplied CSS fill into SVG attributes: the icon importer
    # intentionally rejects style sheets, even for these static backgrounds.
    for node in list(root):
        if node.tag in ("{" + SVG + "}defs", "{" + SVG + "}style"):
            root.remove(node)
    for node in root.iter():
        if node.attrib.pop("class", None):
            node.set("fill", rgb)
    root.set("width", "48")
    root.set("height", "48")
    root.set("viewBox", "0 0 144 144")
    root.set("role", "img")
    ET.SubElement(root, "{" + SVG + "}title").text = "mdi:" + mdi + " / " + color
    group = ET.SubElement(root, "{" + SVG + "}g", {"fill":foreground(rgb), "transform":"translate(24 24) scale(4)"})
    icon = ET.fromstring((SOURCE / "mdi" / (mdi + ".svg")).read_bytes())
    for path in icon.findall(".//{" + SVG + "}path"):
        ET.SubElement(group, "{" + SVG + "}path", {"d":path.attrib["d"]})
    if not len(group):
        raise ValueError("Missing MDI paths: " + mdi)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_pack(color):
    folder = "ha-mdi-favoriten-" + color + ".sdIconPack"
    legal = ("HA MDI Favorites: composed colour backgrounds and MDI symbols.\n"
             "Backgrounds adapted from CSS Color Icons 1.0 / Crafty Lime.\n\n"
             + (SOURCE / "CSS-LICENSE.txt").read_text(encoding="utf-8") + "\n\n"
             + (SOURCE / "MDI-LICENSE.txt").read_text(encoding="utf-8") + "\n\n"
             + (SOURCE / "LICENSE-APACHE-2.0.txt").read_text(encoding="utf-8") + "\n\n"
             + (SOURCE / "LICENSE-MIT.txt").read_text(encoding="utf-8"))
    manifest = {"Name":"HA MDI Favoriten · " + color, "Author":"Pictogrammers / Crafty Lime; composition: USB Extender",
                "Version":"1.0.0", "Description":"20 Ein-/Aus-Paare; 48×48; contrasting symbols; MDI 7.4.47",
                "License":"MDI: Apache-2.0; CSS backgrounds: MIT; see license.txt"}
    files, metadata = {}, []
    for entry in catalog():
        for state, label in (("on", "Ein"), ("off", "Aus")):
            filename = entry["id"] + "-" + state + "--" + entry[state] + ".svg"
            files["icons/" + filename] = compose(color, entry[state])
            metadata.append({"path":"icons/" + filename,
                             "name":entry["name"] + " · " + label + " · " + color,
                             "tags":["HA", "MDI", entry["id"], entry[state], state, label.lower(), color, *entry["tags"]]})
    files["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
    files["icons.json"] = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
    files["license.txt"] = legal.encode("utf-8")
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(folder + "/" + name, date_time=(2026, 11, 21, 0, 0, 0))
            # Match the shipped pack, independent of the build host OS.
            info.create_system = 0
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return folder, files, result.getvalue()


def build(output, bundle=True):
    output = Path(output)
    # Validate all input first; a missing licence must not leave a partial output.
    build_pack("steelblue")
    if output.exists():
        raise FileExistsError("Output already exists; choose a new directory: " + str(output))
    output.mkdir(parents=True)
    packs = output / "Pakete"
    packs.mkdir()
    colors = sorted(p.stem for p in (SOURCE / "colors").glob("*.svg"))
    listing, checksums = [], []
    for color in colors:
        folder, files, data = build_pack(color)
        package = packs / ("HA-MDI-Favoriten-" + color + ".zip")
        package.write_bytes(data)
        checksums.append(hashlib.sha256(data).hexdigest() + "  Pakete/" + package.name)
        for name, raw in files.items():
            path = output / "IconPacks" / folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        _, rgb = background(color)
        listing.append({"color":color, "rgb":rgb, "foreground":foreground(rgb), "icons":40, "file":"Pakete/" + package.name})
    (output / "Farben.json").write_text(json.dumps(listing, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="ascii")
    (output / "README.txt").write_text(
        "HA MDI Favoriten - 147 CSS-Farben, 20 Paare / 40 Icons je Farbe\n\n"
        "In Iconbibliothek > Dateien importieren genau ein Farb-ZIP aus Pakete auswaehlen.\n"
        "Alternativ einen einzelnen Farb-Ordner aus IconPacks importieren.\n"
        "Nicht den gesamten Ausgabeordner mit ZIPs und entpackten Kopien importieren.\n"
        "Nur benoetigte Farben importieren, um SD-Speicher zu sparen.\n"
        "Originale 48x48-SVGs; weiss/schwarz nach Kontrast der CSS-Farbe.\n"
        "Je Entity zwei Symbole (on/off). Bei Tueren/Fenstern: offen/geschlossen;\n"
        "bei Schloss: verriegelt/entriegelt; Medien: Wiedergabe/Pause.\n"
        "Keine automatische HA-Zustandsbindung: normal/gedrueckt oder MQTT-Feedback selbst zuordnen.\n"
        "CSS-Hintergruende: Crafty Lime, MIT. MDI 7.4.47: Pictogrammers, Apache-2.0.\n"
        "Lizenztexte liegen einmal je Farbpaket.\n", encoding="utf-8")
    cards = []
    for row in listing:
        color = row["color"]
        images = []
        for entry in catalog():
            for state in ("on", "off"):
                name = entry["id"] + "-" + state + "--" + entry[state] + ".svg"
                path = "IconPacks/ha-mdi-favoriten-" + color + ".sdIconPack/icons/" + name
                images.append('<img loading="lazy" width="48" height="48" src="' + path + '" title="' + html.escape(entry["name"] + " / " + state) + '">')
        cards.append('<details><summary><span style="background:' + row["rgb"] + '"></span>' + color + ' (' + row["rgb"] + ')</summary><p><a href="' + row["file"] + '">Farbpaket ZIP</a> · 40 Icons</p><div>' + ''.join(images) + '</div></details>')
    (output / "Vorschau.html").write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>HA MDI Favoriten</title><style>body{background:#101820;color:#eee;font:16px system-ui;max-width:1050px;margin:24px auto}details{border:1px solid #455;padding:10px;margin:5px}summary{cursor:pointer}summary span{display:inline-block;width:24px;height:24px;margin-right:12px;vertical-align:middle;border:1px solid #888}img{margin:2px}a{color:#8df}</style><h1>HA MDI Favoriten</h1><p>147 Farben · 20 Ein-/Aus-Paare je Farbe. Paket aufklappen und Vorschau ansehen.</p>' + ''.join(cards) + '</html>', encoding="utf-8")
    if bundle:
        target = ROOT / "ugso_usbhub/bundled/ha-mdi-favorites.streamDeckIconPack"
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(build_pack("steelblue")[2])
    print(str(output) + ": " + str(len(colors)) + " packs, " + str(len(colors)*40) + " icons")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--no-bundle", action="store_true")
    args = parser.parse_args()
    build(args.output, not args.no_bundle)
