"""Configuration UI only. The input/MQTT service is a separate process."""
import base64
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlsplit
from . import icons
from .storage import home, load_config, check_password, public_config, merge_public, save_config, read_json, status_path

LOG = logging.getLogger(__name__)
STATIC = Path(__file__).parent / "static"


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, Handler)
        self.sessions = {}
        self.failures = {}
        self.mutation_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "UGSo-USB-Hub"

    def log_message(self, *_):
        pass  # Never log passwords, cookies or uploaded content.

    def reply(self, code, data, kind="application/json", headers=None):
        if kind == "application/json":
            data = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind + ("; charset=utf-8" if kind.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
            token = jar.get("ugso_session")
            return bool(token and self.server.sessions.get(token.value, 0) > time.time())
        except cookies.CookieError:
            return False

    def do_GET(self):
        route = urlsplit(self.path).path
        if route in ("/", "/app.js", "/keylist.js", "/style.css"):
            file = STATIC / {"/": "index.html", "/app.js": "app.js", "/keylist.js": "keylist.js", "/style.css": "style.css"}[route]
            self.reply(200, file.read_bytes(), {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}[file.suffix])
            return
        if not self.authorized():
            self.reply(401, {"error": "Bitte anmelden"})
            return
        if route == "/api/config":
            self.reply(200, public_config(load_config()))
        elif route == "/api/status":
            snapshot = read_json(status_path(), {"devices": [], "events": [], "brokers": {}, "errors": {}, "updated": 0})
            age = max(0, time.time() - snapshot.get("updated", 0))
            snapshot["age_seconds"] = age
            snapshot["active"] = bool(snapshot.get("updated") and age < 15 and not snapshot.get("stopped"))
            self.reply(200, snapshot)
        elif route == "/api/icons":
            self.reply(200, icons.library())
        elif route.startswith("/icons/"):
            name = route.removeprefix("/icons/")
            if len(name) == 36 and name.endswith(".png") and all(c in "0123456789abcdef" for c in name[:-4]):
                path = home() / "icons" / name
                if path.is_file():
                    self.reply(200, path.read_bytes(), "image/png")
                    return
            self.reply(404, {"error": "Icon nicht gefunden"})
        else:
            self.reply(404, {"error": "Nicht gefunden"})

    def do_POST(self):
        # A non-simple header plus same-origin check protects cookie-authenticated writes.
        origin = self.headers.get("Origin")
        if self.headers.get("X-UGSo-Request") != "1" or (origin and urlsplit(origin).netloc != self.headers.get("Host")):
            self.reply(403, {"error": "Ungültiger Anfrageursprung"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 46 * 1024 * 1024:
                raise ValueError("Anfrage ist leer oder zu groß")
            self.connection.settimeout(30)
            body = json.loads(self.rfile.read(size))
            route = urlsplit(self.path).path
            if route == "/api/login":
                ip = self.client_address[0]
                attempts = [x for x in self.server.failures.get(ip, []) if x > time.time() - 300]
                if len(attempts) >= 8:
                    self.reply(429, {"error": "Zu viele Versuche. Bitte fünf Minuten warten."})
                    return
                if not check_password(str(body.get("password", "")), load_config()["password_hash"]):
                    attempts.append(time.time())
                    self.server.failures[ip] = attempts
                    self.reply(401, {"error": "Passwort stimmt nicht"})
                    return
                self.server.failures.pop(ip, None)
                now = time.time()
                self.server.sessions = {k: v for k, v in self.server.sessions.items() if v > now}
                token = secrets.token_urlsafe(32)
                self.server.sessions[token] = now + 3600
                self.reply(200, {"ok": True}, headers={"Set-Cookie": f"ugso_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600"})
                return
            if not self.authorized():
                self.reply(401, {"error": "Bitte anmelden"})
                return
            with self.server.mutation_lock:
                if route == "/api/config":
                    config = merge_public(body, load_config())
                    save_config(config)
                    self.reply(200, {"ok": True})
                elif route == "/api/learning":
                    from .learning import command
                    self.reply(200, command(body, load_config()))
                elif route == "/api/logout":
                    jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
                    self.server.sessions.pop(jar["ugso_session"].value, None)
                    self.reply(200, {"ok": True}, headers={"Set-Cookie": "ugso_session=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict"})
                elif route == "/api/icons/folder":
                    self.reply(200, icons.import_folder(str(body["path"])))
                elif route == "/api/icons/upload":
                    data = base64.b64decode(body["data"], validate=True)
                    name = str(body["name"])
                    if Path(name).suffix.lower() in (".zip", ".streamdeckiconpack"):
                        result = icons.import_archive(data, name)
                    else:
                        result = {"imported": 1, "id": icons.add(data, name), "skipped": []}
                    self.reply(200, result)
                else:
                    self.reply(404, {"error": "Nicht gefunden"})
        except (ValueError, KeyError, TypeError, OSError, __import__("zipfile").BadZipFile) as exc:
            self.reply(400, {"error": str(exc)[:300]})
        except Exception:
            LOG.exception("Webanfrage fehlgeschlagen")
            self.reply(500, {"error": "Interner Fehler; siehe Dienstprotokoll"})


def run():
    config = load_config()
    if not config.get("password_hash"):
        raise SystemExit("Zuerst mit 'sudo ugso-usbhub password' ein Webpasswort setzen.")
    address = config["web"]["host"], config["web"]["port"]
    server = Server(address)
    LOG.info("Web-Konfiguration auf %s:%s", *address)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
