"""Opt-in local Stream Deck Mobile server; independent of the configuration UI."""
import copy
from collections import deque
import hashlib
import io
import json
import logging
import re
import secrets
import socket
import threading
import time
import uuid
from urllib.parse import urlencode
from PIL import Image
from nacl.public import PrivateKey
from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosed
from . import __version__
from .deck import artwork, key_image, logical_key, page_count, page_slot
from .keymap import all_bindings
from .mobile_protocol import ClientMessage, ServerMessage, encrypt, decrypt, shared_key
from .storage import home, atomic_json, read_json

LOG = logging.getLogger(__name__)
# Hello.version is a desktop-protocol compatibility field, not our product version.
# Android requires Stream Deck 6.3 or newer here. Keep our version in osVersion/UI.
DESKTOP_COMPATIBILITY_VERSION = "6.3.0"
HEARTBEAT_INTERVAL = 5
HEARTBEAT_TIMEOUT = 20
# Return to input and heartbeat handling between small image batches.
IMAGE_BATCH_SIZE = 4
IMAGE_BATCH_SECONDS = 0.025
DEFAULTS = {"enabled": False, "host": "0.0.0.0", "port": 28198, "advertise_host": "", "columns": 5, "rows": 3}


class RequestError(ValueError):
    def __init__(self, request, code, message):
        super().__init__(message)
        self.request,self.code=request,code


def settings(config):
    return {**DEFAULTS, **config.get("mobile", {})}


def validate_options(config):
    options = settings(config)
    if type(options["enabled"]) is not bool or type(options["port"]) is not int or not 1024 <= options["port"] <= 65535:
        raise ValueError("Mobile: ungültiger Port oder Aktivierungswert")
    for name in ("host", "advertise_host"):
        value = options[name]
        if not isinstance(value,str) or (value and not re.fullmatch(r"[a-zA-Z0-9.-]{1,253}",value)):
            raise ValueError("Mobile: IPv4-Adresse oder Hostname ohne Pfad angeben")
    if options["enabled"] and (not options["advertise_host"] or not config.get("password_hash")):
        raise ValueError("Mobile: Serveradresse und Webpasswort zuerst festlegen")
    if options["port"] == config.get("web",{}).get("port"):
        raise ValueError("Mobile- und Web-Port müssen verschieden sein")
    if any(type(options[name]) is not int or not 1<=options[name]<=8 for name in ("columns","rows")):
        raise ValueError("Mobile-Raster: 1 bis 8 Zeilen und Spalten, maximal 64 Tasten")


def pairing_info(config):
    import base64
    import qrcode
    options = settings(config)
    if not options["enabled"] or not options["advertise_host"]:
        raise ValueError("Mobile-Server zuerst konfigurieren und aktivieren")
    query = urlencode({"w":"usb-extender-"+config["hub_id"], "av2":options["advertise_host"]+":"+str(options["port"])})
    url = "https://streamdeck.elgato.com/c/?"+query
    out=io.BytesIO()
    qrcode.make(url).save(out,format="PNG")
    return {"url":url,"qr":base64.b64encode(out.getvalue()).decode()}


def control(body, config):
    if not settings(config)["enabled"]:
        raise ValueError("Mobile-Server ist deaktiviert")
    value=read_json(home()/"mobile-control.json",{})
    action=body.get("action")
    if action == "open":
        value={"until":time.time()+120,"decisions":{}}
    elif action == "close":
        value={"until":0,"decisions":{}}
    elif action in ("allow","deny"):
        token=body.get("token","")
        if not re.fullmatch(r"[a-f0-9]{32}",str(token)):
            raise ValueError("Ungültige Kopplungsanfrage")
        value.setdefault("decisions",{})[token]=action
    else:
        raise ValueError("Unbekannter Kopplungsbefehl")
    atomic_json(home()/"mobile-control.json",value)
    return {"until":value.get("until",0)}


class MobileDeck:
    """PILHelper-compatible adapter. Core calls never perform network writes."""
    def __init__(self, session):
        self.session=session

    def deck_type(self): return "Stream Deck Mobile · experimentell"
    def key_count(self): return self.session.key_count()
    def key_layout(self): return self.session.layout
    def is_visual(self): return True
    def connected(self): return not self.session.closed
    def key_image_format(self): return {"size":self.session.size,"format":"PNG","rotation":0,"flip":(False,False)}
    def set_brightness(self, value): pass  # Android controls its display brightness.
    def set_key_image(self, key, data):
        with self.session.owner.lock:
            if not self.session.closed and 0<=key<self.key_count():
                self.session.images[key]=bytes(data)


class Session:
    def __init__(self, owner, ws):
        self.owner,self.ws=owner,ws
        self.public=b""
        self.client_id=""
        self.name="Android"
        self.key=None
        self.authorized=False
        self.closed=False
        self.device=""
        self.size=(72,72)
        self.image_format=2
        options=settings(owner.config)
        self.layout=(options["rows"],options["columns"])
        self.reported_layout=False
        self.tablet_layout=None
        self.images={}
        self.sent_images={}
        self.last_context=None
        self.images_sent=0
        self.contexts_sent=0
        self.last_ping=time.monotonic()
        self.pending_pong=None
        self.pings_sent=0
        self.pongs_received=0
        self.request=None
        self.token=secrets.token_hex(16)
        self.pressed=set()
        self.created=time.monotonic()
        self.pending_until=0
        self.context_due=False
        self.context_force=False
        self.nonces=set()
        self.packets_received=0
        self.last_receive=time.monotonic()
        self.last_kind="hello"

    def send(self, message, plain=False):
        data=message.SerializeToString()
        self.ws.send(data if plain else encrypt(data,self.key))

    def heartbeat(self):
        now=time.monotonic()
        if self.pending_pong is not None:
            if self.pending_pong.is_set():
                self.pongs_received+=1
                self.pending_pong=None
            elif now-self.last_ping>=HEARTBEAT_TIMEOUT:
                self.ws.close(1001,"Mobile heartbeat timeout")
                return
        if self.pending_pong is None and now-self.last_ping>=HEARTBEAT_INTERVAL:
            # Android's native handler replies with an EMPTY Pong, regardless of
            # Ping payload. An empty Ping also keeps its receive watchdog alive.
            self.pending_pong=self.ws.ping(b"")
            self.last_ping=now
            self.pings_sent+=1

    def ok(self, request): self.send(ServerMessage(ok={"requestID":request}))
    def error(self, request, code, text): self.send(ServerMessage(error={"requestID":request,"code":code,"reason":text}))

    def trusted(self):
        with self.owner.lock:
            return self.owner.trust.get(self.client_id,{}).get("key")==self.public.hex()

    def hello(self, message):
        public=bytes(message.publicKey)
        if len(public)!=32 or not 1<=message.clientInformation.protocolVersion<=100:
            raise ValueError("Ungültige Mobile-Begrüßung")
        self.public=public
        self.client_id=hashlib.sha256(public).hexdigest()[:24]
        self.name=message.clientInformation.name[:80] or "Android"
        self.key=shared_key(public,self.owner.secret)
        self.authorized=self.trusted()
        window=read_json(home()/"mobile-control.json",{})
        if not self.authorized and window.get("until",0)<time.time():
            raise ValueError("Kopplungsfenster ist geschlossen")
        if not self.authorized:
            self.pending_until=min(window["until"],time.time()+120)
        options=settings(self.owner.config)
        self.send(ServerMessage(hello={"workstationID":"usb-extender-"+self.owner.config["hub_id"],
                 "hostname":socket.gethostname(),"version":DESKTOP_COMPATIBILITY_VERSION,"protocolVersion":2,
                 "publicKey":self.owner.public,"clientNeedsAuthentication":not self.authorized,
                 "osName":"Linux","osVersion":"USB Extender "+__version__,"endpoints":{"addresses":[options["advertise_host"]],"port":options["port"]}}),plain=True)
        if self.authorized:self.device_list()

    def device_list(self):
        with self.owner.lock:
            devices=[{"id":ident,"name":d["name"]} for ident,d in self.owner.registry.items() if d["owner"]==self.client_id]
        self.send(ServerMessage(virtualDeviceList={"devices":devices}))

    def decisions(self):
        if self.authorized or not self.public:return
        value=read_json(home()/"mobile-control.json",{})
        decision=value.get("decisions",{}).get(self.token)
        if decision=="allow" and value.get("until",0)>time.time() and self.pending_until>time.time():
            with self.owner.lock:
                self.owner.trust[self.client_id]={"key":self.public.hex(),"name":self.name}
                atomic_json(home()/"mobile-trust.json",self.owner.trust)
            self.authorized=True
            if self.request is not None:self.ok(self.request)
            self.request=None
            self.device_list()
        elif decision=="deny" or min(value.get("until",0),self.pending_until)<time.time():
            if self.request is not None:self.error(self.request,3,"Kopplung abgelehnt oder abgelaufen")
            self.request=None
            self.ws.close(1008,"Pairing rejected")

    def open_device(self, request, create=False):
        formats=list(request.keypadConfig.supportedIconImageFormats)
        if 2 in formats:self.image_format=2
        elif 5 in formats:self.image_format=5
        else:
            self.error(request.requestID,5,"LZ4 oder PNG als Iconformat benötigt")
            return
        size=request.keypadConfig.iconSize
        if not 16<=size.width<=256 or not 16<=size.height<=256:
            self.error(request.requestID,5,"Icongröße muss zwischen 16 und 256 liegen")
            return
        with self.owner.lock:
            for other in self.owner.sessions:
                if other is not self and other.device and other.device==getattr(request,"deviceID","") and not other.closed:
                    raise RequestError(request.requestID,2,"Gerät bereits verbunden")
            if create:
                name=request.name.strip()[:80] or self.name
                own=[d for d in self.owner.registry.values() if d["owner"]==self.client_id]
                if len(own)>=8:
                    raise RequestError(request.requestID,2,"Maximal acht virtuelle Geräte je Client")
                if not request.skipUniquenessOfNameValidation and any(d["name"]==name for d in own):
                    raise RequestError(request.requestID,1,"Gerätename bereits vorhanden")
                ident="mobile-"+uuid.uuid4().hex
                self.owner.registry[ident]={"owner":self.client_id,"name":name}
                atomic_json(home()/"mobile-devices.json",self.owner.registry)
            else:
                ident=request.deviceID
                if self.owner.registry.get(ident,{}).get("owner")!=self.client_id:
                    raise RequestError(request.requestID,0,"Gerät nicht gefunden")
                name=self.owner.registry[ident]["name"]
            if self.device:
                self.owner.emit(self.device,"_mobile_disconnect","release",0)
            self.pressed.clear()
            self.images.clear()
            self.sent_images.clear()
            self.last_context=None
            self.device=ident
            self.size=(size.width,size.height)
            self.set_layout(request.keypadConfig.layoutCrop)
        self.context_due=False
        self.send(ServerMessage(virtualDeviceOpened={"requestID":request.requestID,"device":{"id":ident,"name":name}}))
        self.context()
        self.owner.refresh_required.set()
        self.owner.remember(self)

    def context(self, force=False):
        if not self.device:return
        actions=[]
        bindings=all_bindings(self.owner.config)
        pages=page_count(self.owner.config,self.device)
        page=max(0,min(self.owner.current_page(self.device),pages-1))
        for key in range(self.key_count()):
            style=artwork(self.owner.config,self.device,key,page)
            binding=next((b for b in bindings if b["device"]==self.device and b["control"]==f"key:{logical_key(key,page_slot(self.owner.config,self.device,page))}"),{})
            title=style.get("text",binding.get("text",f"Taste {page*self.key_count()+key+1}"))
            if not title:title={"next":"Vor","previous":"Zurück","home":"Home","goto":f"Seite {style.get('target_page',1)}"}.get(style.get("action"),title)
            actions.append({"index":key,"title":title,"name":title,"category":"Navigation" if style.get('action','mqtt')!='mqtt' else "MQTT"})
        message=ServerMessage(context={"profileID":self.device,"totalPages":pages,"currentPage":page,"actions":actions})
        signature=message.SerializeToString()
        if force or signature!=self.last_context:
            self.send(message)
            self.last_context=signature
            self.contexts_sent+=1

    def flush_images(self):
        if not self.authorized or not self.device:return
        if self.context_due:
            self.context_due=False
            force,self.context_force=self.context_force,False
            self.context(force=force)
        started=time.monotonic()
        for _ in range(IMAGE_BATCH_SIZE):
            with self.owner.lock:
                if not self.images:break
                key=next(iter(self.images))
                data=self.images.pop(key)
            with Image.open(io.BytesIO(data)) as source:
                size=source.size
                raw=source.convert("RGBA").tobytes("raw","BGRA")
            if size!=self.size:
                self.owner.refresh_required.set()
                continue
            signature=(self.image_format,size,hashlib.sha256(raw).digest())
            if self.sent_images.get(key)==signature:
                continue
            if self.image_format==2:
                import lz4.block
                data=lz4.block.compress(raw,store_size=False)
            self.send(ServerMessage(icon={"index":key,"image":{"format":self.image_format,"type":1,
                      "size":{"width":size[0],"height":size[1]},"rowBytes":size[0]*4,"image":data}}))
            self.sent_images[key]=signature
            self.images_sent+=1
            if time.monotonic()-started>=IMAGE_BATCH_SECONDS:break

    def process(self, message):
        kind=message.WhichOneof("payload")
        self.packets_received+=1
        self.last_receive=time.monotonic()
        self.last_kind=kind or "extension"
        if kind=="authenticate":
            if self.authorized:
                self.ok(message.authenticate.requestID)
                self.device_list()
            elif self.request is not None:self.error(message.authenticate.requestID,2,"Kopplung läuft bereits")
            else:
                self.request=message.authenticate.requestID
                self.pending_until=time.time()+120
            return
        if kind=="cancelAuthenticate":
            if self.request is not None:self.error(self.request,4,"Kopplung abgebrochen")
            self.request=None
            self.pending_until=0
            self.ok(message.cancelAuthenticate.requestID)
            return
        if kind=="clientCapabilities":return  # Metadata never grants trust or Pro features.
        if not self.authorized:raise ValueError("Client ist nicht freigegeben")
        if kind in ("createVirtualDevice","openVirtualDevice"):
            self.open_device(getattr(message,kind),kind=="createVirtualDevice")
        elif kind=="keyPress" and self.device:
            key=message.keyPress.index
            if not 0<=key<self.key_count():raise ValueError("Ungültige Mobile-Taste")
            pressed=message.keyPress.pressed
            if pressed==(key in self.pressed):return
            if pressed:self.pressed.add(key)
            else:self.pressed.discard(key)
            self.owner.emit(self.device,f"key:{key}","press" if pressed else "release",int(pressed))
        elif kind=="updateKeypadConfig" and self.device:
            self.set_layout(message.updateKeypadConfig.layoutCrop)
            size=message.updateKeypadConfig.iconSize
            if 16<=size.width<=256 and 16<=size.height<=256 and self.size!=(size.width,size.height):
                self.size=(size.width,size.height)
                self.images.clear()
                self.sent_images.clear()
                self.owner.refresh_required.set()
                self.owner.remember(self)
        elif kind in ("nextPage","previousPage","pageByIndex"):
            if self.device:
                action={'nextPage':'next','previousPage':'previous','pageByIndex':'index'}[kind]
                self.owner.emit(self.device,'_deck_page',action,message.pageByIndex.index if kind=='pageByIndex' else 0)
        elif kind=="deleteVirtualDevice":
            self.ws.close(1008,"Entfernen nur in der Serververwaltung; Daten bleiben erhalten")
        elif kind=="removeShortcut":
            self.error(message.removeShortcut.requestID,5,"Shortcuts werden nicht unterstützt")
        elif kind in ("assignShortcut","triggerShortcut") or kind is None:
            # Optional commands must not tear down an authenticated deck session.
            LOG.debug("Optionale Mobile-Nachricht nicht unterstützt: %s",kind or "neuer Nachrichtentyp")
        elif kind not in ("clientCapabilities",):
            raise ValueError("Unbekannte Mobile-Nachricht")

    def key_count(self):return self.layout[0]*self.layout[1]

    def set_layout(self, crop):
        if 1<=crop.width<=8 and 1<=crop.height<=8:
            self.reported_layout=True
            self.tablet_layout=(crop.height,crop.width)
        self.apply_tablet_layout()

    def apply_tablet_layout(self):
        options=settings(self.owner.config)
        # Legacy server overrides stay stored for compatibility but are inert.
        layout=self.tablet_layout or (options["rows"],options["columns"])
        self.apply_layout(*layout)

    def apply_layout(self, rows, columns):
        layout=(rows,columns)
        if layout!=self.layout:
            if self.pressed and self.device:self.owner.emit(self.device,"_mobile_disconnect","release",0)
            self.pressed.clear()
            self.images.clear()
            self.sent_images.clear()
            self.layout=layout
            self.context_due=True
            self.owner.refresh_required.set()
            if self.device:self.owner.remember(self)


class MobileServer:
    def __init__(self, emit):
        self.emit=emit
        self.config={}
        self.options=None
        self.lock=threading.RLock()
        self.sessions=[]
        self.server=None
        self.thread=None
        self.error=""
        self.trust={}
        self.registry={}
        self.public=self.secret=b""
        self.refresh_required=threading.Event()
        self.disconnects=deque(maxlen=8)
        self.current_page=lambda ident:0

    def page_changed(self, ident, force=False):
        with self.lock:
            for session in self.sessions:
                if session.device==ident:
                    session.context_due=True
                    session.context_force=session.context_force or force

    def configure(self, config):
        self.config=config
        options=settings(config)
        transport=("enabled","host","port")
        if self.options is not None and all(options[name]==self.options[name] for name in transport) and (not options["enabled"] or self.server is not None):
            self.options=options
            with self.lock:
                for session in self.sessions:
                    session.context_due=True
                    session.apply_tablet_layout()
            return
        self.close()
        self.options=options
        self.error=""
        if not options["enabled"]:return
        try:
            validate_options(config)
            identity=read_json(home()/"mobile-identity.json",None)
            if identity is None:
                key=PrivateKey.generate()
                identity={"secret":bytes(key).hex()}
                atomic_json(home()/"mobile-identity.json",identity)
            key=PrivateKey(bytes.fromhex(identity["secret"]))
            self.secret,self.public=bytes(key),bytes(key.public_key)
            self.trust=read_json(home()/"mobile-trust.json",{})
            self.registry=read_json(home()/"mobile-devices.json",{})
            self.server=serve(self.handle,options["host"],options["port"],compression=None,
                              max_size=65536,max_queue=8,open_timeout=5,close_timeout=1,ping_interval=None,
                              subprotocols=["streamdeck.vsd2"],select_subprotocol=lambda conn,offered:"streamdeck.vsd2" if "streamdeck.vsd2" in offered else None)
            self.thread=threading.Thread(target=self.server.serve_forever,daemon=True,name="streamdeck-mobile")
            self.thread.start()
        except Exception as exc:
            self.error=str(exc)[:200]
            self.close()
            LOG.warning("Mobile-Server konnte nicht gestartet werden: %s",self.error)

    def handle(self, ws):
        session=Session(self,ws)
        with self.lock:
            accepted=len(self.sessions)<4
            if accepted:self.sessions.append(session)
        if not accepted:
            ws.close(1013,"Maximal vier Verbindungen")
            return
        reason="Verbindung beendet"
        try:
            first=ws.recv(timeout=10)
            if not isinstance(first,bytes) or len(first)>4096:raise ValueError("Binäre Begrüßung erwartet")
            message=ClientMessage.FromString(first)
            if message.WhichOneof("payload")!="hello":raise ValueError("Begrüßung erwartet")
            session.hello(message.hello)
            count=0;second=time.monotonic()
            while self.server is not None:
                session.decisions()
                session.heartbeat()
                session.flush_images()
                if not session.authorized and time.monotonic()-session.created>125:break
                try:data=ws.recv(timeout=.01 if session.images else .15)
                except TimeoutError:continue
                now=time.monotonic()
                if now-second>=1:count=0;second=now
                count+=1
                if count>100:raise ValueError("Zu viele Mobile-Nachrichten")
                if not isinstance(data,bytes) or data[:24] in session.nonces:
                    raise ValueError("Ungültiges oder wiederholtes Mobile-Paket")
                if len(session.nonces)>=4096:session.nonces.clear()
                session.nonces.add(data[:24])
                try:
                    session.process(ClientMessage.FromString(decrypt(data,session.key)))
                except RequestError as exc:
                    session.error(exc.request,exc.code,str(exc))
        except ConnectionClosed as exc:
            reason=str(exc)[:180]
        except Exception as exc:
            reason=str(exc)[:180]
            LOG.info("Mobile-Verbindung beendet: %s",str(exc)[:120])
            ws.close(1008,"Mobile-Protokoll oder Kopplung ungültig")
        finally:
            with self.lock:
                session.closed=True
                if session in self.sessions:self.sessions.remove(session)
                last_receive_age=round(max(0,time.monotonic()-session.last_receive),2)
                self.disconnects.append({"time":time.time(),"name":session.name,"device":session.device,"reason":reason,"images_sent":session.images_sent,"contexts_sent":session.contexts_sent,
                    "pings_sent":session.pings_sent,"pongs_received":session.pongs_received,"packets_received":session.packets_received,
                    "last_packet":session.last_kind,"last_packet_age":last_receive_age,"queued_images":len(session.images)})
            LOG.info("Mobile getrennt · %s · %s · Bilder %s · Context %s · Ping/Pong %s/%s · letzte Nachricht %s vor %.2fs · Bildwarteschlange %s",
                     session.name[:80],reason,session.images_sent,session.contexts_sent,session.pings_sent,session.pongs_received,
                     session.last_kind,last_receive_age,len(session.images))
            if session.device:self.emit(session.device,"_mobile_disconnect","release",0)

    def remember(self, session):
        if not session.device:return
        with self.lock:
            device=self.registry.get(session.device)
            info={"model":"Stream Deck Mobile · experimentell","keys":session.key_count(),"layout":list(session.layout),"visual":True,"size":list(session.size)}
            if device is not None and device.get("deck")!=info:
                device["deck"]=info
                atomic_json(home()/"mobile-devices.json",self.registry)

    def decks(self):
        with self.lock:
            return {s.device:MobileDeck(s) for s in self.sessions if s.device and s.authorized and not s.closed}

    def inventory(self):
        with self.lock:
            return [{"id":s.device,"kind":"streamdeck","connection":"mobile","name":self.registry[s.device]["name"],
                     "identity_hint":"Vertrauenswürdiger Mobile-Client · "+s.name,
                     "deck":{"model":"Stream Deck Mobile · experimentell","keys":s.key_count(),"layout":list(s.layout),"layout_source":"tablet" if s.reported_layout else "server","visual":True,"size":list(s.size)}}
                    for s in self.sessions if s.device and s.authorized and not s.closed]

    def status(self):
        with self.lock:
            return {"active":self.server is not None,"error":self.error,
                    "recent_disconnects":list(self.disconnects),
                    "known_decks":[{"id":ident,"kind":"streamdeck","connection":"mobile","name":device["name"],"deck":device["deck"]} for ident,device in self.registry.items() if device.get("deck")],
                    "pairing_until":read_json(home()/"mobile-control.json",{}).get("until",0),
                    "pending":[{"token":s.token,"name":s.name,"fingerprint":hashlib.blake2b(s.public,digest_size=32).hexdigest()[:6].upper()}
                               for s in self.sessions if s.public and not s.authorized and not s.closed and s.pending_until>time.time()],
                    "clients":[{"name":s.name,"device":s.device,"authorized":s.authorized,"images_sent":s.images_sent,"contexts_sent":s.contexts_sent,"pings_sent":s.pings_sent,"pongs_received":s.pongs_received} for s in self.sessions],
                    "trusted":[{"id":key,"name":value["name"]} for key,value in self.trust.items()]}

    def key_count(self):
        options=settings(self.config)
        return options["columns"]*options["rows"]

    def close(self):
        server,self.server=self.server,None
        if server:
            server.shutdown()
            with self.lock:sessions=list(self.sessions)
            for session in sessions:session.ws.close(1001,"Mobile-Server deaktiviert")
            if self.thread:self.thread.join(timeout=3)
        self.thread=None
