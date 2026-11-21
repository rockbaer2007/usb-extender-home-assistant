import json
import logging
import ssl
import threading
import paho.mqtt.client as mqtt

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

    def discovery(self, broker):
        if not broker.get("discovery"):
            return
        client = self.clients[broker["id"]]
        for b in self.config["bindings"]:
            if broker["id"] not in resolve_targets(self.config, b["device"], b):
                continue
            unique = f"ugso_{self.config['hub_id']}_{b['id']}"
            kind = {"press": "button_short_press", "release": "button_short_release", "hold": "button_long_press"}.get(b["gesture"], b["gesture"])
            payload = {"automation_type": "trigger", "topic": self.event_topic(broker, b),
                       "type": kind, "subtype": b["control"].replace(":", "_"),
                       "device": {"identifiers": [f"ugso_{self.config['hub_id']}_{b['device']}"],
                                  "name": self.config["devices"].get(b["device"], {}).get("name") or b["device"],
                                  "manufacturer": "UGSo", "model": "USB Hub"}}
            client.publish(f"homeassistant/device_automation/{unique}/config", json.dumps(payload), qos=1, retain=True)

    def send(self, device, control, gesture, value=1):
        delivered = 0
        for binding in self.config["bindings"]:
            if (binding["device"], binding["control"], binding["gesture"]) != (device, control, gesture):
                continue
            payload = binding.get("payload")
            if not payload:
                payload = json.dumps({"device": device, "control": control, "event_type": gesture, "value": value}, ensure_ascii=False)
            for broker in self.config["brokers"]:
                client = self.clients.get(broker["id"])
                if broker["id"] in resolve_targets(self.config, device, binding) and client and client.is_connected():
                    # QoS 0 + explicit connectivity check: no replay of offline key presses.
                    result = client.publish(self.event_topic(broker, binding), payload, qos=0, retain=False)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        delivered += 1
        return delivered

    def cleanup_removed(self, replacement):
        new = {b["id"]: b for b in replacement.get("bindings", [])}
        for binding in self.config["bindings"]:
            for broker in self.config["brokers"]:
                client = self.clients.get(broker["id"])
                old_target = broker["id"] in resolve_targets(self.config, binding["device"], binding)
                updated = new.get(binding["id"])
                remains = updated and broker["id"] in resolve_targets(replacement, updated["device"], updated)
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
