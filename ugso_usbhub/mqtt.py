import json
import hashlib
import logging
import ssl
import threading
import paho.mqtt.client as mqtt
from .storage import canonical_control, home, atomic_json, read_json

LOG = logging.getLogger(__name__)


def resolve_targets(config, device, binding):
    if binding.get("targets") is not None:
        return binding["targets"]
    return config.get("devices", {}).get(device, {}).get("targets", config["default_targets"])


class Brokers:
    def __init__(self, config, receive, start=True):
        self.config = config
        self.receive = receive
        self.clients = {}
        self.states = {}
        self.lock = threading.Lock()
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
            if broker.get("discovery"):
                client.subscribe("homeassistant/status")
            for binding in self.config["bindings"]:
                device = self.config["devices"].get(binding["device"], {})
                if device.get("receive_broker") == ident and binding.get("state_topic"):
                    client.subscribe(binding["state_topic"])
            self.discovery(broker)
        return callback

    def _disconnected(self, ident):
        def callback(client, userdata, flags, reason, properties):
            self.states[ident] = "offline"
        return callback

    def _message(self, broker):
        def callback(client, userdata, message):
            try:
                if len(message.payload) > 16384:
                    LOG.warning("Zu großer MQTT-Anzeigeauftrag verworfen")
                    return
                if message.topic == "homeassistant/status" and message.payload == b"online":
                    self.discovery(broker)
                else:
                    self.receive(broker["id"], message.topic, message.payload.decode("utf-8"))
            except Exception:
                LOG.exception("MQTT-Anzeigeauftrag verworfen")
        return callback

    def event_topic(self, broker, binding):
        return binding.get("topic") or f"{broker['prefix']}/event/{binding['device']}/{binding['id']}"

    def discovery_topic(self, binding):
        return f"homeassistant/device_automation/ugso_{self.config['hub_id']}_{binding['id']}/config"

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
            for b in self.config["bindings"]:
                if broker["id"] not in resolve_targets(self.config, b["device"], b):
                    continue
                kind = {"press": "button_short_press", "release": "button_short_release", "hold": "button_long_press"}.get(b["gesture"], b["gesture"])
                payload = {"automation_type": "trigger", "topic": self.event_topic(broker, b),
                           "type": kind, "subtype": canonical_control(b["control"]).replace(":", "_"),
                           "device": {"identifiers": [f"ugso_{self.config['hub_id']}_{b['device']}"],
                                      "name": self.config["devices"].get(b["device"], {}).get("name") or b["device"],
                                      "manufacturer": "UGSo", "model": "USB Hub"}}
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

    def send_report(self, device, control, gesture, value=1):
        control = canonical_control(control)
        delivered = 0
        matched = 0
        transmissions = []
        for binding in self.config["bindings"]:
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
                    result = client.publish(self.event_topic(broker, binding), payload, qos=0, retain=False)
                    transmission["state"] = "sent" if result.rc == mqtt.MQTT_ERR_SUCCESS else "failed"
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        delivered += 1
        reason = "sent" if delivered else "no_binding" if not matched else "no_targets" if not transmissions else "not_connected"
        return {"delivered": delivered, "matched": matched, "reason": reason, "transmissions": transmissions}

    def cleanup_removed(self, replacement):
        new = {b["id"]: b for b in replacement.get("bindings", [])}
        new_brokers = {b["id"]: b for b in replacement["brokers"]}
        for binding in self.config["bindings"]:
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
