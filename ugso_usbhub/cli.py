import argparse
import getpass
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from . import __version__
from .storage import home, load_config, save_config, password_hash, atomic_json, read_json, status_path


def main():
    parser = argparse.ArgumentParser(description="USB Extender für Home Assistant – Raspberry Pi / USB / MQTT")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("daemon", "serve-web", "status", "devices", "password", "init", "backup"):
        sub.add_parser(name)
    web = sub.add_parser("web", help="Getrennte Weboberfläche steuern")
    web.add_argument("action", choices=("start", "stop", "status", "enable", "disable"))
    icon = sub.add_parser("icons")
    icon.add_argument("path", help="Lokaler Ordner, Bild, ZIP oder .streamDeckIconPack")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        if args.command == "daemon":
            from .core import Core
            Core().run()
        elif args.command == "serve-web":
            from .web import run
            run()
        elif args.command == "web":
            actions = {"enable": ["enable", "--now"], "disable": ["disable", "--now"]}
            return subprocess.call(["systemctl", *actions.get(args.action, [args.action]), "ugso-usbhub-web.service"])
        elif args.command == "init":
            load_config()
            print("Konfiguration bereit:", home() / "config.json")
        elif args.command == "password":
            password = getpass.getpass("Neues Webpasswort (mindestens 12 Zeichen): ")
            if len(password) < 12 or password != getpass.getpass("Wiederholen: "):
                raise ValueError("Passwörter stimmen nicht überein oder sind zu kurz")
            config = load_config()
            config["password_hash"] = password_hash(password)
            save_config(config)
            print("Webpasswort gespeichert. Ein laufender Webdienst wird neu gestartet.")
            if sys.platform == "linux":
                subprocess.run(["systemctl", "try-restart", "ugso-usbhub-web.service"], check=False)
        elif args.command == "status":
            print(json.dumps(read_json(status_path(), {"info": "Dienst noch nicht gestartet"}), ensure_ascii=False, indent=2))
        elif args.command == "devices":
            from .hardware import inventory
            print(json.dumps(inventory(), ensure_ascii=False, indent=2))
        elif args.command == "backup":
            import datetime
            import tarfile
            folder = home() / "exports"
            folder.mkdir(exist_ok=True)
            target = folder / ("usb-extender-backup-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".tar.gz")
            with tarfile.open(target, "w:gz") as archive:
                for path in home().iterdir():
                    if path.name != "exports":
                        archive.add(path, arcname="ugso-usbhub/" + path.name)
            os.chmod(target, 0o600)
            print(target)
        elif args.command == "icons":
            from . import icons
            path = Path(args.path)
            if path.is_dir():
                result = icons.import_folder(path)
            elif path.suffix.lower() in (".zip", ".streamdeckiconpack"):
                result = icons.import_archive(path.read_bytes(), path.name)
            else:
                result = {"imported": 1, "id": icons.add(path.read_bytes(), path.name)}
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Fehler: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
