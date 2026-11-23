import json
import hashlib
import logging
import ssl
import threading
import time
import paho.mqtt.client as mqtt
from .storage import canonical_control, home, atomic_json, read_json
from .keymap import all_bindings

LOG = logging.getLogger(__name__)


def touchpad_channels(settings):
    if not settings.get('enabled') or not settings.get('touchpad_gestures'):return {}
    channels={}
    if settings.get('touchpad_xy'):
        for axis in ('x','y'):channels[axis]=(axis.upper(),settings['touchpad_'+axis+'_topic'])
    if settings.get('touchpad_mode','directions')=='faders':
        for lane,value in settings.get('touchpad_faders',{}).items():
            if value.get('enabled',True):channels['fader_'+lane]=('Regler '+lane,value['topic'])
    else:
        for direction,value in settings.get('touchpad_slide_values',{}).items():
            if value.get('enabled'):channels['slide_'+direction.lower()]=('Slide '+direction.replace('_',' '),value['topic'])
    return channels


def resolve_targets(config, device, binding):
    if binding.get("targets") is not None:
        return binding["targets"]
    return config.get("devices", {}).get(device, {}).get("targets", config["default_targets"])


def numeric_channels(settings):
    if settings.get('scanner_enabled'):return {}
    from .gamepad import channels
    return {**{'touchpad_'+k:v for k,v in touchpad_channels(settings).items()},
            **{'gamepad_'+k:v for k,v in channels(settings).items()}}


class Brokers:
    def __init__(self, config, receive, start=True, management=None):
        self.config = config
        self.management = management
        self.receive = receive
        self.clients = {}
        self.states = {}
        self.discovery_errors = {}
        self.lock = threading.Lock()
        self.pending_resets = {}
        for broker in config["brokers"]:
            if not broker.get("enabled"):
                continue
            ident = broker["id"]
            self.states[ident] = "Verbindung wird aufgebaut"
            try:
                self.clients[ident] = self._create(broker)
            except (OSError, ValueError) as exc:
                self.states[ident] = "Konfigurationsfehler: " + str(exc)
        if start:
            self.start()

    def _create(self, broker):
        ident = broker["id"]
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                             client_id=f"ugso-{self.config['hub_id']}-{ident}")
        if broker.get("username"):
            client.username_pw_set(broker["username"], broker.get("password", ""))
        client.reconnect_delay_set(1, 30)
        if broker.get("tls"):
            client.tls_set(ca_certs=broker.get("ca_file") or None, cert_reqs=ssl.CERT_REQUIRED)
        client.will_set(broker["prefix"] + "/availability", "offline", qos=1, retain=True)
        client.on_connect = self._connected(broker)
        client.on_disconnect = self._disconnected(ident)
        client.on_message = self._message(broker)
        return client

    def start(self):
        if self.management:
            self.management.web_config=dict(self.config.get('web',{}))
            self.management.enabled=any(b.get('enabled') and b.get('control_enabled') for b in self.config['brokers'])
            if self.management.enabled:self.management.start()
        for broker in self.config["brokers"]:
            client = self.clients.get(broker["id"])
            if client:
                try:
                    client.connect_async(broker["host"], broker["port"], keepalive=30)
                    client.loop_start()
                except (ValueError, OSError) as exc:
                    self.states[broker["id"]] = "Verbindungsfehler: " + str(exc)

    def _connected(self, broker):
        def callback(client, userdata, flags, reason, properties):
            ident = broker["id"]
            if reason.is_failure:
                self.states[ident] = str(reason)
                return
            self.states[ident] = "online"
            client.publish(broker["prefix"] + "/availability", "online", qos=1, retain=True)
            client.subscribe(broker["prefix"] + "/display/+/set")
            if broker.get('control_enabled') and self.management:
                from .management import COMMANDS
                for topic in COMMANDS:client.subscribe(topic,qos=0)
                self.publish_management(self.management.snapshot(),broker['id'])
            if broker.get("discovery"):
                client.subscribe("homeassistant/status")
            for binding in all_bindings(self.config):
                if binding['control'].startswith('TOUCHPAD_SLIDE_') and self.config.get('devices',{}).get(binding['device'],{}).get('touchpad_mode')=='faders':continue
                device = self.config["devices"].get(binding["device"], {})
                if device.get("receive_broker") == ident and binding.get("state_topic"):
                    client.subscribe(binding["state_topic"])
            self.sync_discovery(broker)
            try:
                switches = read_json(home() / "switches.json", {})
                for binding in all_bindings(self.config):
                    if binding['control'].startswith('TOUCHPAD_SLIDE_') and self.config.get('devices',{}).get(binding['device'],{}).get('touchpad_mode')=='faders':continue
                    if binding.get("toggle") and binding["gesture"] == "toggle_on" and ident in resolve_targets(self.config, binding["device"], binding):
                        state = isinstance(switches, dict) and switches.get(binding["key_id"]) is True
                        client.publish(self.event_topic(broker, binding), "ON" if state else "OFF", qos=0, retain=False)
            except (OSError, ValueError):
                LOG.exception("Switch-Zustände konnten nicht abgeglichen werden")
        return callback

    def _disconnected(self, ident):
        def callback(client, userdata, flags, reason, properties):
            self.states[ident] = "offline"
            with self.lock:
                self.pending_resets = {k: v for k, v in self.pending_resets.items() if k[0] != ident}
        return callback

    def _message(self, broker):
        def callback(client, userdata, message):
            try:
                if len(message.payload) > 16384:
                    LOG.warning("Zu großer MQTT-Anzeigeauftrag verworfen")
                    return
                from .management import COMMANDS
                if message.topic in COMMANDS:
                    if broker.get('control_enabled') and self.management and not message.retain and not getattr(message,'dup',False) and len(message.payload)<=32:
                        self.management.submit(message.topic,message.payload.decode('utf-8'))
                    return
                if message.topic == "homeassistant/status" and message.payload == b"online":
                    self.sync_discovery(broker)
                else:
                    self.receive(broker["id"], message.topic, message.payload.decode("utf-8"))
            except Exception:
                LOG.exception("MQTT-Anzeigeauftrag verworfen")
        return callback

    def event_topic(self, broker, binding):
        if binding.get("key_topic"):
            return binding.get("topic") or f"{broker['prefix']}/{binding['key_topic']}"
        return binding.get("topic") or f"{broker['prefix']}/event/{binding['device']}/{binding['id']}"

    def publish_management(self,values,only=None):
        from .management import BASE
        for broker in self.config['brokers']:
            if not broker.get('control_enabled') or (only and broker['id']!=only):continue
            client=self.clients.get(broker['id'])
            if client and client.is_connected():
                for key,value in values.items():client.publish(BASE+'/state/'+key,value,qos=1,retain=True)

    def sync_discovery(self, broker):
        try:
            self.discovery(broker)
            self.discovery_errors.pop(broker["id"], None)
        except Exception as exc:
            # Discovery must never kill the MQTT network loop or stop key events.
            self.discovery_errors[broker["id"]] = str(exc)
            LOG.exception("Discovery fehlgeschlagen; MQTT-Daten bleiben aktiv")

    def discovery_topic(self, binding):
        return f"homeassistant/device_automation/ugso_{self.config['hub_id']}_{binding['id']}/config"

    def discovery_device(self, ident):
        return {"identifiers": [f"ugso_{self.config['hub_id']}_{ident}"],
                "name": self.config["devices"].get(ident, {}).get("name") or "USB-Gerät",
                "manufacturer": "USB Extender", "model": "USB input"}

    def known_discovery(self, broker, registry, endpoint):
        known = set(registry.get(endpoint, []))
        # Migrate deterministic announcements from 0.1.0/0.1.1 config backups.
        for path in sorted((home() / "backups").glob("*.json"))[-10:]:
            try:
                history = read_json(path, {})
                if history.get("hub_id") != self.config["hub_id"]:
                    continue
                old = next((b for b in history.get("brokers", []) if b.get("id") == broker["id"]), {})
                if not old.get("enabled") or not old.get("discovery") or (old.get("host"), old.get("port"), old.get("username", "")) != (broker["host"], broker["port"], broker.get("username", "")):
                    continue
                for binding in history.get("bindings", []):
                    if broker["id"] in resolve_targets(history, binding["device"], binding):
                        known.add(self.discovery_topic(binding))
            except (OSError, ValueError, KeyError, TypeError):
                LOG.warning("Alte Discovery-Zuordnung konnte nicht gelesen werden")
        return known

    def discovery(self, broker):
        client = self.clients[broker["id"]]
        desired = {}
        if broker.get("discovery"):
            if broker.get('control_enabled'):
                from .management import discovery
                desired.update(discovery(self.config['hub_id'],broker['prefix']+'/availability'))
            for ident,settings in self.config.get('devices',{}).items():
                if broker['id'] not in resolve_targets(self.config,ident,{}):continue
                from .scanner import topic as scanner_topic
                if scanner_topic(settings):
                    desired[f"homeassistant/tag/ugso_{self.config['hub_id']}_{ident}/config"]=json.dumps({
                        'topic':scanner_topic(settings),'device':self.discovery_device(ident)})
                for channel,(name,state_topic) in numeric_channels(settings).items():
                    unique=f"ugso_{self.config['hub_id']}_{ident}_{channel}"
                    topic=f'homeassistant/sensor/{unique}/config'
                    desired[topic]=json.dumps({'name':name,'unique_id':unique,'state_topic':state_topic,
                        'suggested_display_precision':0,'icon':'mdi:gamepad-variant' if channel.startswith('gamepad_') else 'mdi:gesture-swipe',
                        'availability_topic':broker['prefix']+'/availability',
                        'device':self.discovery_device(ident)})
            for b in all_bindings(self.config):
                if b['control'].startswith('TOUCHPAD_SLIDE_') and self.config.get('devices',{}).get(b['device'],{}).get('touchpad_mode')=='faders':continue
                if broker["id"] not in resolve_targets(self.config, b["device"], b):
                    continue
                if b.get("key_mode") in ("switch", "state"):
                    if b["gesture"] not in ("press", "toggle_on"):
                        continue
                    mode = b["key_mode"]
                    topic = f"homeassistant/binary_sensor/ugso_{self.config['hub_id']}_{b['key_id']}" + ("_state" if mode == "state" else "") + "/config"
                    desired[topic] = json.dumps({"name": (b.get("text") or b["control"]) + (" · Tastenzustand" if mode == "state" else " · Switch"),
                        "unique_id": f"ugso_{self.config['hub_id']}_{b['key_id']}_{mode}",
                        "state_topic": self.event_topic(broker, b), "payload_on": "ON", "payload_off": "OFF",
                        "availability_topic": broker["prefix"] + "/availability",
                        "device": self.discovery_device(b["device"])})
                    continue
                kind = {"press": "button_short_press", "release": "button_short_release", "hold": "button_long_press",
                        "button_click": "button_short_press", "button_double_click": "button_double_press",
                        "button_hold": "button_long_press"}.get(b["gesture"], b["gesture"])
                payload = {"automation_type": "trigger", "topic": self.event_topic(broker, b),
                           "type": kind, "subtype": (b.get("key_mode", "") + "_" if b.get("key_mode") else "") + canonical_control(b["control"]).replace(":", "_"),
                           "device": self.discovery_device(b["device"])}
                if b.get("key_mode"):
                    payload["payload"] = b["payload"]
                desired[self.discovery_topic(b)] = json.dumps(payload)
        endpoint = hashlib.sha256(json.dumps([broker["host"], broker["port"], broker.get("username", "")]).encode()).hexdigest()
        with self.lock:
            path = home() / "discovery.json"
            registry = read_json(path, {})
            known = self.known_discovery(broker, registry, endpoint)
            # Remember own topics before publishing, including across an offline reload.
            # Tombstones are idempotent and retried on reconnect until the broker receives them.
            tracked = sorted(known | desired.keys())
            if tracked != registry.get(endpoint, []):
                registry[endpoint] = tracked
                atomic_json(path, registry)
            for topic in known - desired.keys():
                client.publish(topic, "", qos=1, retain=True)
            for topic, payload in desired.items():
                client.publish(topic, payload, qos=1, retain=True)

    def send(self, device, control, gesture, value=1):
        return self.send_report(device, control, gesture, value)["delivered"]

    def send_position(self, device, x, y):
        settings=self.config.get('devices',{}).get(device,{})
        transmissions=[];delivered=0
        if not all(settings.get(name,False) for name in ('enabled','touchpad_gestures','touchpad_xy')):
            return {'delivered':0,'matched':0,'reason':'disabled','transmissions':[]}
        if any(type(v) is not int or not 0<=v<=100 for v in (x,y)):raise ValueError('Touchpad-X/Y: 0–100')
        for broker in self.config['brokers']:
            if broker['id'] not in resolve_targets(self.config,device,{}):continue
            client=self.clients.get(broker['id'])
            for axis,value in (('x',x),('y',y)):
                topic=settings['touchpad_'+axis+'_topic']
                transmission={'broker':broker['id'],'name':broker['name'],'topic':topic,
                              'state':'offline' if broker.get('enabled') else 'disabled'}
                transmissions.append(transmission)
                if client and client.is_connected():
                    result=client.publish(topic,str(value),qos=0,retain=False)
                    transmission['state']='sent' if result.rc==mqtt.MQTT_ERR_SUCCESS else 'failed'
                    delivered+=result.rc==mqtt.MQTT_ERR_SUCCESS
        return {'delivered':delivered,'matched':2,'reason':'sent' if delivered else 'no_targets' if not transmissions else 'not_connected','transmissions':transmissions}

    def send_slide_value(self, device, direction, value):
        from .touchpad import SLIDE_DIRECTIONS
        if direction not in SLIDE_DIRECTIONS or type(value) is not int or not 0<=value<=100:
            raise ValueError('Slide-Wert: bekannte Richtung und 0–100 erforderlich')
        return self.send_touchpad_value(device,'slide_'+direction.lower(),value)

    def send_fader_value(self, device, lane, value):
        if type(lane) is not int or not 1<=lane<=5 or type(value) is not int or not 0<=value<=100:
            raise ValueError('Regler: Platz 1–5 und Wert 0–100 erforderlich')
        return self.send_touchpad_value(device,'fader_'+str(lane),value)

    def send_touchpad_value(self, device, name, value):
        settings=self.config.get('devices',{}).get(device,{})
        channel=touchpad_channels(settings).get(name)
        return self.send_numeric_channel(device,channel,value)

    def send_gamepad_value(self,device,name,value):
        from .gamepad import AXES,channels
        if name not in AXES or type(value) is not int or not 0<=value<=100:raise ValueError('Gamepad: bekannte Achse und Wert 0–100 erforderlich')
        return self.send_numeric_channel(device,channels(self.config.get('devices',{}).get(device,{})).get(name),value)

    def send_numeric_channel(self,device,channel,value):
        return self._send_channel(device,channel,value)

    def send_scan(self,device,text):
        from .scanner import topic,tag_value
        settings=self.config.get('devices',{}).get(device,{})
        target=topic(settings)
        if not target:return {'delivered':0,'matched':0,'reason':'disabled','transmissions':[]}
        return self._send_channel(device,('Scanner',target),tag_value(text,settings))

    def _send_channel(self,device,channel,value):
        if not channel:return {'delivered':0,'matched':0,'reason':'disabled','transmissions':[]}
        transmissions=[];delivered=0
        for broker in self.config['brokers']:
            if broker['id'] not in resolve_targets(self.config,device,{}):continue
            client=self.clients.get(broker['id'])
            transmission={'broker':broker['id'],'name':broker['name'],'topic':channel[1],
                          'state':'offline' if broker.get('enabled') else 'disabled'}
            transmissions.append(transmission)
            if client and client.is_connected():
                result=client.publish(channel[1],str(value),qos=0,retain=False)
                transmission['state']='sent' if result.rc==mqtt.MQTT_ERR_SUCCESS else 'failed'
                delivered+=result.rc==mqtt.MQTT_ERR_SUCCESS
        return {'delivered':delivered,'matched':1,'reason':'sent' if delivered else 'no_targets' if not transmissions else 'not_connected','transmissions':transmissions}

    def send_report(self, device, control, gesture, value=1, repeat_key=False, switch_only=False):
        control = canonical_control(control)
        if control.startswith('TOUCHPAD_SLIDE_') and self.config.get('devices',{}).get(device,{}).get('touchpad_mode')=='faders':
            return {'delivered':0,'matched':0,'reason':'mode_inactive','transmissions':[]}
        delivered = 0
        matched = 0
        transmissions = []
        for binding in all_bindings(self.config, device=device, control=control):
            if switch_only and binding.get("key_mode") not in ("switch", "state"):
                continue
            if repeat_key and binding.get("key_mode") not in ("press", "press_plus"):
                continue
            if (binding["device"], canonical_control(binding["control"]), binding["gesture"]) != (device, control, gesture):
                continue
            matched += 1
            payload = binding.get("payload")
            if not payload:
                payload = json.dumps({"device": device, "control": control, "event_type": gesture, "value": value}, ensure_ascii=False)
            for broker in self.config["brokers"]:
                if broker["id"] not in resolve_targets(self.config, device, binding):
                    continue
                client = self.clients.get(broker["id"])
                transmission = {"broker": broker["id"], "name": broker["name"],
                                "topic": self.event_topic(broker, binding),
                                "state": "offline" if broker.get("enabled") else "disabled"}
                transmissions.append(transmission)
                if client and client.is_connected():
                    # QoS 0 + explicit connectivity check: no replay of offline key presses.
                    with self.lock:
                        pending = self.pending_resets.pop((broker["id"], self.event_topic(broker, binding)), None)
                        if pending:
                            client.publish(self.event_topic(broker, binding), "", qos=0, retain=False)
                    result = client.publish(self.event_topic(broker, binding), payload, qos=0, retain=False)
                    transmission["state"] = "sent" if result.rc == mqtt.MQTT_ERR_SUCCESS else "failed"
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        delivered += 1
                        if binding.get("reset"):
                            with self.lock:
                                self.pending_resets[(broker["id"], self.event_topic(broker, binding))] = (time.monotonic() + 0.05, client)
        reason = "sent" if delivered else "no_binding" if not matched else "no_targets" if not transmissions else "not_connected"
        return {"delivered": delivered, "matched": matched, "reason": reason, "transmissions": transmissions}

    def flush_resets(self, now=None):
        now = time.monotonic() if now is None else now
        with self.lock:
            ready = [(key, value) for key, value in self.pending_resets.items() if value[0] <= now]
            for key, (_, client) in ready:
                del self.pending_resets[key]
                if client.is_connected():
                    client.publish(key[1], "", qos=0, retain=False)

    def cleanup_removed(self, replacement):
        new = {b["id"]: b for b in all_bindings(replacement)}
        new_brokers = {b["id"]: b for b in replacement["brokers"]}
        for broker in self.config['brokers']:
            client=self.clients.get(broker['id'])
            updated=new_brokers.get(broker['id'],{})
            if broker.get('control_enabled') and client and client.is_connected() and not (updated.get('enabled') and updated.get('control_enabled') and all(broker.get(k)==updated.get(k) for k in ('host','port','username'))):
                from .management import BASE
                for key,value in {'webrun':'UNKNOWN','autorun':'UNKNOWN','state':'MQTT-Systemsteuerung deaktiviert'}.items():
                    client.publish(BASE+'/state/'+key,value,qos=1,retain=True).wait_for_publish(timeout=2)
            if not broker.get('discovery') or not client or not client.is_connected():continue
            updated=new_brokers.get(broker['id'],{})
            same_endpoint=all(broker.get(k)==updated.get(k) for k in ('host','port','username'))
            if broker.get('control_enabled') and not (same_endpoint and updated.get('enabled') and updated.get('discovery') and updated.get('control_enabled')):
                from .management import discovery
                for topic in discovery(self.config['hub_id'],broker['prefix']+'/availability'):
                    client.publish(topic,'',qos=1,retain=True).wait_for_publish(timeout=2)
            for ident,settings in self.config.get('devices',{}).items():
                if broker['id'] not in resolve_targets(self.config,ident,{}):continue
                channels=numeric_channels(replacement.get('devices',{}).get(ident,{}))
                remains=updated.get('enabled') and updated.get('discovery') and same_endpoint and broker['id'] in resolve_targets(replacement,ident,{})
                from .scanner import topic as scanner_topic
                if scanner_topic(settings) and (not remains or not scanner_topic(replacement.get('devices',{}).get(ident,{}))):
                    client.publish(f"homeassistant/tag/ugso_{self.config['hub_id']}_{ident}/config",'',qos=1,retain=True).wait_for_publish(timeout=2)
                for channel in numeric_channels(settings):
                    if not remains or channel not in channels:
                        topic=f"homeassistant/sensor/ugso_{self.config['hub_id']}_{ident}_{channel}/config"
                        client.publish(topic,'',qos=1,retain=True).wait_for_publish(timeout=2)
        for binding in all_bindings(self.config):
            for broker in self.config["brokers"]:
                client = self.clients.get(broker["id"])
                old_target = broker.get("discovery") and broker["id"] in resolve_targets(self.config, binding["device"], binding)
                updated = new.get(binding["id"])
                new_broker = new_brokers.get(broker["id"], {})
                remains = new_broker.get("enabled") and new_broker.get("discovery") and updated and broker["id"] in resolve_targets(replacement, updated["device"], updated)
                if old_target and not remains and client and client.is_connected():
                    client.publish(f"homeassistant/device_automation/ugso_{self.config['hub_id']}_{binding['id']}/config", "", qos=1, retain=True).wait_for_publish(timeout=2)

    def close(self):
        for broker in self.config["brokers"]:
            client = self.clients.get(broker["id"])
            if client:
                try:
                    if client.is_connected():
                        client.publish(broker["prefix"] + "/availability", "offline", qos=1, retain=True).wait_for_publish(timeout=2)
                except (RuntimeError, ValueError):
                    LOG.warning("Broker-Abmeldung nicht bestätigt")
                finally:
                    client.disconnect()
                    client.loop_stop()
