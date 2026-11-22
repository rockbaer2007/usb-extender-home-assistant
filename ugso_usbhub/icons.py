"""Managed icon library. Archives are inspected in memory, never extracted."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import threading
import zipfile
import shutil
import tempfile
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from PIL import Image, ImageOps
from .storage import home, atomic_json, read_json

LOCK = threading.Lock()
CACHE_LOCK = threading.Lock()
THUMBNAIL_LOCK = threading.Lock()
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 96 * 1024 * 1024
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
MAX_FRAMES = 120


def thumbnail_path(ident):
    """Small static picker image; never decode animation frames or full previews."""
    if not re.fullmatch(r"[0-9a-f]{32}", str(ident)):
        raise ValueError("Ungültige Bild-ID")
    folder = home() / "icons"
    target = folder / ".cache" / "thumbnails" / (ident + ".png")
    with THUMBNAIL_LOCK:
        if target.is_file():
            return target
        entry = source_entry(ident)
        source = folder / entry["original_path"] if entry else _cache_path(ident)
        if not source.resolve().is_relative_to(folder.resolve()) or not source.is_file():
            raise FileNotFoundError("Icon nicht gefunden")
        if shutil.disk_usage(folder).free < 1024 * 1024:
            raise ValueError("Zu wenig Speicher für die Miniatur")
        data = raster(source.read_bytes(), source.suffix, size=48)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
            os.replace(temporary, target)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
        return target


def _cache_path(ident, suffix=".png"):
    folder = home() / "icons"
    path = folder / ".cache" / (ident + suffix)
    return path if path.exists() else folder / (ident + suffix)


@lru_cache(maxsize=4)
def _source_map(path, stamp):
    return {item["id"]:item for item in read_json(Path(path), []) if item.get("original_path")}


def source_entry(ident):
    path = home() / "icons" / "index.json"
    return _source_map(str(path), path.stat().st_mtime_ns).get(ident) if path.exists() else None


def ensure_cached(ident):
    if not re.fullmatch(r"[0-9a-f]{32}", str(ident)):
        raise ValueError("Ungültige Bild-ID")
    with CACHE_LOCK:
        folder = home() / "icons"
        cache = folder / ".cache"
        png = cache / (ident + ".png")
        marker = cache / (ident + ".animation.json")
        if png.exists() and marker.exists():
            return
        item = source_entry(ident)
        if not item:
            return  # Legacy cached icons have no original file.
        original = folder / item["original_path"]
        if not original.resolve().is_relative_to((folder / "IconPacks").resolve()) or not original.is_file():
            return
        data = original.read_bytes()
        rendered = raster(data, original.suffix)
        frames, durations = decode_animation(data, original.suffix)
        required = len(rendered) + sum(len(f.tobytes()) for f in frames) + 16*1024*1024
        if shutil.disk_usage(folder).free < required:
            raise ValueError("Zu wenig Speicher für die Iconvorschau")
        cache.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache, prefix=".render-") as temporary:
            staging = Path(temporary)
            if frames:
                target = cache / (ident + ".frames")
                target.mkdir(exist_ok=True)
                for index, frame in enumerate(frames):
                    path = staging / (str(index) + ".png")
                    frame.save(path)
                    os.replace(path, target / path.name)
                path = staging / "animation.webp"
                frames[0].save(path, format="WEBP", save_all=True, append_images=frames[1:], duration=durations, loop=0, lossless=True)
                os.replace(path, cache / (ident + ".webp"))
            (staging / "preview.png").write_bytes(rendered)
            os.replace(staging / "preview.png", png)
            atomic_json(marker, {"durations":durations})


def cached_path(ident, suffix=".png"):
    path = _cache_path(ident, suffix)
    if not path.exists():
        ensure_cached(ident)
        path = _cache_path(ident, suffix)
    return path


def animation(ident):
    if not re.fullmatch(r"[0-9a-f]{32}", str(ident)):
        return []
    path = _cache_path(ident, ".animation.json")
    if not path.exists() and (source_entry(ident) or {}).get("animated"):
        ensure_cached(ident)
        path = _cache_path(ident, ".animation.json")
    return _animation(str(path), path.stat().st_mtime_ns if path.exists() else 0)


@lru_cache(maxsize=128)
def _animation(path, stamp):
    return read_json(Path(path), {}).get("durations", []) if stamp else []


def frame_path(ident, index=0):
    durations = animation(ident)
    if durations:
        return cached_path(ident, ".frames") / (str(index % len(durations)) + ".png")
    return cached_path(ident)


def decode_animation(data, suffix):
    if suffix.lower() not in (".gif", ".webp", ".png"):
        return [], []
    frames, durations = [], []
    with Image.open(io.BytesIO(data)) as source:
        count = getattr(source, "n_frames", 1)
        if count <= 1:
            return [], []
        if count > MAX_FRAMES or source.width * source.height > 16_000_000:
            raise ValueError("Animation zu groß: maximal 120 Bilder und 16 Megapixel je Quellbild")
        for index in range(count):
            source.seek(index)
            frame = ImageOps.contain(source.convert("RGBA"), (256, 256))
            canvas = Image.new("RGBA", (256, 256))
            canvas.alpha_composite(frame, ((256-frame.width)//2, (256-frame.height)//2))
            frames.append(canvas)
            durations.append(max(100, min(10000, int(source.info.get("duration", 100) or 100))))
    return frames, durations


def library():
    return read_json(home() / "icons" / "index.json", [])


@lru_cache(maxsize=2)
def _catalog(path, stamp):
    items, licenses, refs, unique = [], {}, {}, {}
    for item in read_json(Path(path), []):
        key = item.get("package_folder") or item.get("collection") or "Eigene Icons"
        text = item.get("license", "")
        reference = (key, text)
        if reference not in refs:
            licenses.setdefault(key, []).append(text)
            refs[reference] = len(licenses[key]) - 1
        identity = (key, item["id"])
        alias = {k:item.get(k) for k in ("name", "filename", "subfolder", "tags", "original_path")}
        if identity in unique:
            primary = unique[identity]
            canonical = {k:primary.get(k) for k in alias if k != "tags"}
            if {k:v for k,v in alias.items() if k != "tags"} != canonical and alias not in primary.setdefault("aliases", []):
                primary["aliases"].append(alias)
            primary["tags"] = list(dict.fromkeys([*primary.get("tags", []), *item.get("tags", [])]))
            if refs[reference] not in primary["license_refs"]:
                primary["license_refs"].append(refs[reference])
        else:
            packed = {**{k:v for k,v in item.items() if k != "license"}, "license_ref":refs[reference], "license_refs":[refs[reference]]}
            items.append(packed)
            unique[identity] = packed
    return {"items":items, "licenses":licenses}


def catalog():
    """Compact wire format: a repeated package licence is transferred once."""
    path = home() / "icons" / "index.json"
    return _catalog(str(path), path.stat().st_mtime_ns) if path.is_file() else {"items":[], "licenses":{}}


def remove_package(package, config):
    """Remove only unused indexed icons after creating a full library backup."""
    with LOCK:
        items = library()
        removed = [i for i in items if (i.get("package_folder") or i.get("collection")) == package]
        if not removed:
            raise ValueError("Paket nicht gefunden")
        identifiers = {i["id"] for i in removed}
        def used(value):
            if isinstance(value, dict):
                return any(used(v) for v in value.values())
            if isinstance(value, list):
                return any(used(v) for v in value)
            return isinstance(value, str) and value in identifiers
        if used(config):
            raise ValueError("Paket wird von einer Taste verwendet. Zuerst andere Icons wählen und speichern.")
        folder = home() / "icons"
        backups = home() / "backups"
        backups.mkdir(exist_ok=True)
        backup = backups / ("icons-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + ".zip")
        with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in folder.rglob("*"):
                if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(folder.resolve()):
                    archive.write(path, path.relative_to(folder))
        remaining = [i for i in items if i not in removed]
        atomic_json(folder / "index.json", remaining)
        keep_ids = {i["id"] for i in remaining}
        keep_originals = {i.get("original_path") for i in remaining}
        for item in removed:
            original = folder / item.get("original_path", "missing")
            if item.get("original_path") and item["original_path"] not in keep_originals and original.resolve().is_relative_to((folder / "IconPacks").resolve()):
                original.unlink(missing_ok=True)
                parent = original.parent
                while parent != folder / "IconPacks" and parent.is_relative_to(folder / "IconPacks"):
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent
            ident = item["id"]
            if ident in keep_ids or not re.fullmatch(r"[0-9a-f]{32}", ident):
                continue
            for suffix in (".png", ".webp", ".animation.json"):
                for base in (folder, folder / ".cache"):
                    (base / (ident+suffix)).unlink(missing_ok=True)
            (folder / ".cache" / "thumbnails" / (ident + ".png")).unlink(missing_ok=True)
            frames = cached_path(ident, ".frames")
            if frames.exists() and not frames.is_symlink() and frames.resolve().is_relative_to(folder.resolve()):
                shutil.rmtree(frames)
        _animation.cache_clear()
        return {"ok":True, "removed":len(removed), "backup":str(backup)}


def validate_svg(data):
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


def raster(data, suffix, size=256):
    if len(data) > MAX_FILE:
        raise ValueError("Icon ist größer als 8 MB")
    if suffix.lower() == ".svg":
        validate_svg(data)
        import cairosvg
        data = cairosvg.svg2png(bytestring=data, output_width=size, output_height=size)
    with Image.open(io.BytesIO(data)) as source:
        if source.width * source.height > 16_000_000:
            raise ValueError("Icon-Abmessungen zu groß")
        source.seek(0)  # Static preview for animated packs.
        image = ImageOps.contain(source.convert("RGBA"), (size, size))
        canvas = Image.new("RGBA", (size, size))
        canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
        out = io.BytesIO()
        canvas.save(out, format="PNG")
        return out.getvalue()


def inspect_source(data, suffix):
    if len(data) > MAX_FILE:
        raise ValueError("Icon ist größer als 8 MB")
    if suffix.lower() == ".svg":
        validate_svg(data)
        return False, 1
    with Image.open(io.BytesIO(data)) as image:
        if image.width * image.height > 16_000_000:
            raise ValueError("Icon-Abmessungen zu groß")
        image.verify()
    with Image.open(io.BytesIO(data)) as image:
        frames = getattr(image, "n_frames", 1)
        if frames > MAX_FRAMES:
            raise ValueError("Animation zu groß: maximal 120 Bilder")
        return frames > 1, frames


class ImportBatch:
    def __init__(self):
        self.items = library()
        self.paths = {item["original_path"]:item for item in self.items if item.get("original_path")}
        self.changed = False


@contextmanager
def import_batch():
    with LOCK:
        batch = ImportBatch()
        yield batch
        if batch.changed:
            atomic_json(home() / "icons" / "index.json", batch.items)


def add(data, name, collection="Eigene Icons", tags=None, author="", license_text="", subfolder="", package_folder="", _batch=None, display_name=""):
    if _batch is None:
        with import_batch() as batch:
            return add(data, name, collection, tags, author, license_text, subfolder, package_folder, batch, display_name)
    animated, frames = inspect_source(data, Path(name).suffix)
    folder = home() / "icons"
    folder.mkdir(parents=True, exist_ok=True)
    relative = PurePosixPath(str(subfolder).replace("\\", "/"))
    filename = PurePosixPath(str(name).replace("\\", "/")).name
    if relative.is_absolute() or ".." in relative.parts or ":" in str(relative) or not filename or filename in (".", ".."):
        raise ValueError("Ungültiger Iconpfad")
    package = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", str(package_folder or collection)).strip(". ")[:120] or "Eigene Icons"
    original = folder / "IconPacks" / package / str(relative) / filename
    if not original.resolve().is_relative_to((folder / "IconPacks").resolve()):
        raise ValueError("Ungültiger Iconpfad")
    path = original.relative_to(folder).as_posix()
    old = _batch.paths.get(path)
    if original.exists() and original.read_bytes() != data:
        raise ValueError("Dateiname bereits mit anderem Inhalt vorhanden: " + filename)
    if shutil.disk_usage(folder).free < len(data) + 16*1024*1024:
        raise ValueError("Zu wenig freier Speicher für dieses Icon")
    # Retain every existing mapping on reimport; new IDs need no rasterization.
    ident = old["id"] if old else hashlib.sha256(b"original-v1\0" + data).hexdigest()[:32]
    original.parent.mkdir(parents=True, exist_ok=True)
    if not original.exists():
        original.write_bytes(data)
    record = {"id":ident, "name":display_name or Path(name).stem, "collection":collection,
              "tags":[str(t)[:100] for t in tags] if isinstance(tags,list) else [],
              "author":author or (old or {}).get("author",""),
              "license":license_text[:32000] or (old or {}).get("license",""),
              "subfolder":str(subfolder)[:500], "animated":animated, "frames":frames,
              "duration_ms":(old or {}).get("duration_ms",0), "filename":filename,
              "package_folder":package, "original_path":path}
    if old is None:
        _batch.items.append(record)
        _batch.paths[path] = record
    elif old == record:
        return ident
    else:
        old.update(record)
    _batch.changed = True
    return ident


def import_favorites():
    """Opt-in, offline import; never modify device/broker assignments."""
    pack = Path(__file__).parent / "bundled" / "ha-mdi-favorites.streamDeckIconPack"
    return import_archive(pack.read_bytes(), pack.name)


def import_archive(data, name, progress=None):
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
        names = set(archive.namelist())
        packages = []
        for manifest_name in sorted((n for n in names if n.endswith("manifest.json")), key=len, reverse=True):
            try:
                manifest = json.loads(archive.read(manifest_name))
            except (ValueError, UnicodeError):
                manifest = {}
            if not isinstance(manifest, dict):
                manifest = {}
            root = manifest_name.rsplit("/",1)[0]+"/" if "/" in manifest_name else ""
            index_name = root+"icons.json"
            index = json.loads(archive.read(index_name)) if index_name in names else []
            if not isinstance(index,list):
                raise ValueError("icons.json muss eine Liste sein")
            metadata = {str(x.get("path","")).lstrip("/"):x for x in index if isinstance(x,dict)}
            license_name = next((n for n in names if n.startswith(root) and "/" not in n[len(root):]
                                 and PurePosixPath(n).name.lower() in ("license","licence","license.txt","licence.txt","license.md","licence.md")),None)
            license_text = archive.read(license_name).decode("utf-8",errors="replace") if license_name else str(manifest.get("License",manifest.get("Licence","")))
            package = PurePosixPath(root.rstrip("/")).name if root else Path(name).stem
            packages.append({"root":root, "collection":str(manifest.get("Name",package)), "package":package,
                             "author":str(manifest.get("Author","")), "license":license_text, "metadata":metadata, "manifest":True})
        roots = {p["root"] for p in packages}
        for item in entries:
            parts = PurePosixPath(item.filename).parts
            root = None
            for index, part in enumerate(parts[:-1]):
                if part.lower().endswith(".sdiconpack"):
                    root = "/".join(parts[:index+1])+"/"
                    break
            if root is None and Path(name).stem.lower()=="iconpacks" and len(parts)>2 and parts[0].lower()=="iconpacks":
                root = "/".join(parts[:2])+"/"
            if root is not None and root not in roots:
                folder = PurePosixPath(root.rstrip("/")).name
                packages.append({"root":root,"collection":folder,"package":folder,"author":"","license":"","metadata":{},"manifest":False})
                roots.add(root)
        if not packages:
            prefix = Path(name).stem+"/"
            root = prefix if all(n.startswith(prefix) for n in names) else ""
            packages = [{"root":root, "collection":Path(name).stem, "package":Path(name).stem, "author":"", "license":"", "metadata":{},"manifest":False}]
        packages.sort(key=lambda p:len(p["root"]),reverse=True)
        candidates = []
        for item in entries:
            if item.is_dir() or Path(item.filename).suffix.lower() not in EXTENSIONS:
                continue
            package = next((p for p in packages if item.filename.startswith(p["root"])),None)
            if not package:
                continue
            relative = item.filename[len(package["root"]):]
            if package["manifest"] and not relative.startswith(("icons/","images/","imgs/")):
                continue
            candidates.append((item,package,relative))
        result = {"imported":0, "skipped":[], "collection":packages[0]["collection"] if len(packages)==1 else "Mehrere Pakete"}
        if progress:
            progress(0,len(candidates),result["collection"])
        with import_batch() as batch:
            for index,(item,package,relative) in enumerate(candidates):
                meta = package["metadata"].get(relative,package["metadata"].get(relative.removeprefix("icons/"),{}))
                try:
                    add(archive.read(item),item.filename,package["collection"],meta.get("tags",[]),package["author"],package["license"],
                        str(PurePosixPath(relative).parent),package["package"],_batch=batch,display_name=str(meta.get("name","")))
                    result["imported"] += 1
                except (ValueError,OSError,ImportError) as exc:
                    result["skipped"].append({"file":item.filename,"reason":str(exc)})
                if progress:
                    progress(index+1,len(candidates),item.filename)
        if not result["imported"] and not result["skipped"]:
            result["skipped"].append({"file":name,"reason":"Keine unterstützten Bilder unter icons/, images/ oder imgs/ gefunden"})
        return result


def import_folder(path):
    source = Path(path).expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Kein Iconordner")
    files = [f for f in source.rglob("*") if not f.is_symlink() and f.is_file()
             and f.suffix.lower() in EXTENSIONS and f.resolve().is_relative_to(source)]
    if len(files)>10000 or sum(f.stat().st_size for f in files)>MAX_TOTAL:
        raise ValueError("Ordner überschreitet das Importlimit")
    result = {"imported":0,"skipped":[]}
    metadata = {}
    with import_batch() as batch:
        for file in files:
            try:
                relative = file.relative_to(source)
                package = source
                for parent in file.parents:
                    if not parent.is_relative_to(source):
                        break
                    if (parent/"manifest.json").is_file() or parent.suffix.lower()==".sdiconpack":
                        package = parent
                        break
                if source.name.lower()=="iconpacks" and package==source and len(relative.parts)>1:
                    package = source/relative.parts[0]
                if package not in metadata:
                    try:
                        meta = json.loads((package/"manifest.json").read_bytes())
                    except (OSError,ValueError,UnicodeError):
                        meta = {}
                    if not isinstance(meta,dict):
                        meta = {}
                    license_file = next((p for p in package.iterdir() if p.is_file() and not p.is_symlink()
                                         and p.name.lower() in ("license","licence","license.txt","licence.txt","license.md","licence.md")),None)
                    legal = license_file.read_text(encoding="utf-8",errors="replace") if license_file else str(meta.get("License",meta.get("Licence","")))
                    metadata[package] = (meta,legal)
                meta,legal = metadata[package]
                add(file.read_bytes(),file.name,str(meta.get("Name",package.name)),author=str(meta.get("Author","")),
                    license_text=legal,subfolder=file.relative_to(package).parent.as_posix(),package_folder=package.name,_batch=batch)
                result["imported"] += 1
            except (ValueError,OSError,ImportError) as exc:
                result["skipped"].append({"file":file.name,"reason":str(exc)})
    return result
