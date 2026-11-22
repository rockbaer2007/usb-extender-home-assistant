"""Reproducible, source-only installation ZIP. No local configuration or venv."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.31"
NAME = f"USB-Extender-Home-Assistant-{VERSION}"
FILES = ["README.md", "README.en.md", "STAND.md", "ROADMAP.md", "CHANGELOG.md", "TESTBERICHT.md", "pyproject.toml", "requirements.txt", "install.sh", ".gitattributes", ".gitignore"]
FOLDERS = ["ugso_usbhub", "systemd", "scripts", "tests", "tools", "docs"]


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / (NAME + "-Raspi4.zip")
    files = [ROOT / name for name in FILES]
    for name in FOLDERS:
        files += [p for p in (ROOT / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    hashes = []
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(files):
            relative = file.relative_to(ROOT).as_posix()
            data = file.read_bytes()
            if file.suffix.lower() in {".md", ".py", ".js", ".cjs", ".css", ".html", ".json", ".toml", ".txt", ".sh", ".svg", ".service", ".rules"} or file.name in (".gitattributes", ".gitignore"):
                data = data.replace(b"\r\n", b"\n")
            info = zipfile.ZipInfo(NAME + "/" + relative, date_time=(2026, 11, 22, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if relative == "install.sh" or relative.startswith("scripts/") else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
            hashes.append(hashlib.sha256(data).hexdigest() + "  " + relative)
        archive.writestr(NAME + "/SHA256SUMS", "\n".join(hashes) + "\n")
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert not any(any(part in (".git", ".state", ".venv", "config.json", "status.json") for part in Path(name).parts) for name in archive.namelist())
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(digest + "  " + destination.name + "\n", encoding="ascii")
    print(destination)
    print(f"{destination.stat().st_size:,} bytes / SHA256 {digest}")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "dist"))
    build(parser.parse_args().output)
