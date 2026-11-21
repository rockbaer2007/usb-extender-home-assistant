"""Managed icon library. Archives are inspected in memory, never extracted."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import threading
import zipfile
from PIL import Image, ImageOps
from .storage import home, atomic_json, read_json

LOCK = threading.Lock()
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 96 * 1024 * 1024
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def library():
    return read_json(home() / "icons" / "index.json", [])


def raster(data, suffix):
    if len(data) > MAX_FILE:
        raise ValueError("Icon ist größer als 8 MB")
    if suffix.lower() == ".svg":
        # Disallow resource fetching entirely, including CSS and XML entities.
        from defusedxml import ElementTree
        root = ElementTree.fromstring(data)
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] in ("script", "foreignObject", "style"):
                raise ValueError("SVG enthält nicht unterstützte aktive Inhalte oder CSS")
            for key, value in node.attrib.items():
                if key.rsplit("}", 1)[-1].lower() in ("base", "src") or key.lower().startswith("on"):
                    raise ValueError("Externe SVG-Ressourcen sind nicht erlaubt")
                if key.rsplit("}", 1)[-1] == "href" and not value.startswith("#"):
                    raise ValueError("Externe SVG-Verweise sind nicht erlaubt")
                if re.search(r"url\(\s*['\"]?(?!#)", value, re.I) or "@import" in value.lower():
                    raise ValueError("Externe SVG-Ressourcen sind nicht erlaubt")
        import cairosvg
        data = cairosvg.svg2png(bytestring=data, output_width=256, output_height=256)
    with Image.open(io.BytesIO(data)) as source:
        if source.width * source.height > 16_000_000:
            raise ValueError("Icon-Abmessungen zu groß")
        source.seek(0)  # Static preview for animated packs.
        image = ImageOps.contain(source.convert("RGBA"), (256, 256))
        canvas = Image.new("RGBA", (256, 256))
        canvas.alpha_composite(image, ((256 - image.width) // 2, (256 - image.height) // 2))
        out = io.BytesIO()
        canvas.save(out, format="PNG")
        return out.getvalue()


def add(data, name, collection="Eigene Icons", tags=None, author="", license_text=""):
    png = raster(data, Path(name).suffix)
    ident = hashlib.sha256(png).hexdigest()[:32]
    folder = home() / "icons"
    folder.mkdir(parents=True, exist_ok=True)
    with LOCK:
        items = library()
        if not any(x["id"] == ident and x["collection"] == collection for x in items):
            (folder / (ident + ".png")).write_bytes(png)
            safe_tags = [str(t)[:100] for t in tags] if isinstance(tags, list) else []
            items.append({"id": ident, "name": Path(name).stem, "collection": collection,
                          "tags": safe_tags, "author": author, "license": license_text[:32000]})
            atomic_json(folder / "index.json", items)
    return ident


def import_archive(data, name):
    if len(data) > 32 * 1024 * 1024:
        raise ValueError("Archiv größer als 32 MB")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > 10000 or sum(x.file_size for x in entries) > MAX_TOTAL:
            raise ValueError("Iconpaket zu groß (maximal 10.000 Dateien / 96 MB entpackt)")
        for item in entries:
            path = PurePosixPath(item.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or ":" in str(path) or (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Unsicherer Archivpfad")
            if item.file_size > MAX_FILE:
                raise ValueError("Einzeldatei größer als 8 MB")
        names = archive.namelist()
        manifest_name = next((n for n in names if n.endswith("manifest.json")), None)
        manifest = json.loads(archive.read(manifest_name)) if manifest_name else {}
        collection = str(manifest.get("Name", Path(name).stem))
        author = str(manifest.get("Author", ""))
        root = manifest_name.rsplit("/", 1)[0] + "/" if manifest_name and "/" in manifest_name else ""
        index_name = root + "icons.json"
        icon_index = json.loads(archive.read(index_name)) if index_name in names else []
        if not isinstance(icon_index, list):
            raise ValueError("icons.json muss eine Liste sein")
        metadata = {str(x.get("path", "")).lstrip("/"): x for x in icon_index if isinstance(x, dict)}
        license_name = next((n for n in names if n.lower().endswith(("license.txt", "licence.txt"))), None)
        license_text = archive.read(license_name).decode("utf-8", errors="replace") if license_name else str(manifest.get("License", manifest.get("Licence", "")))
        result = {"imported": 0, "skipped": [], "collection": collection}
        for item in entries:
            if item.is_dir() or Path(item.filename).suffix.lower() not in EXTENSIONS:
                continue
            # Pack cover icons are not key icons. Plain image ZIPs have no manifest.
            relative = item.filename[len(root):] if item.filename.startswith(root) else item.filename
            if manifest_name and not relative.startswith("icons/"):
                continue
            meta = metadata.get(relative, metadata.get(relative.removeprefix("icons/"), {}))
            try:
                ident = add(archive.read(item), item.filename, collection, meta.get("tags", []), author, license_text)
                if meta.get("name"):
                    with LOCK:
                        items = library()
                        for entry in items:
                            if entry["id"] == ident and entry["collection"] == collection:
                                entry["name"] = str(meta["name"])
                        atomic_json(home() / "icons" / "index.json", items)
                result["imported"] += 1
            except (ValueError, OSError, ImportError) as exc:
                result["skipped"].append({"file": item.filename, "reason": str(exc)})
        return result


def import_folder(path):
    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Kein Iconordner")
    result = {"imported": 0, "skipped": []}
    total = 0
    for file in source.rglob("*"):
        if file.is_symlink() or not file.is_file() or file.suffix.lower() not in EXTENSIONS:
            continue
        if not file.resolve().is_relative_to(source):
            continue
        total += file.stat().st_size
        if total > MAX_TOTAL or result["imported"] >= 10000:
            raise ValueError("Ordner überschreitet das Importlimit")
        try:
            add(file.read_bytes(), file.name, source.name)
            result["imported"] += 1
        except (ValueError, OSError, ImportError) as exc:
            result["skipped"].append({"file": file.name, "reason": str(exc)})
    return result
