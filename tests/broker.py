"""Small local MQTT 3.1.1 test peer; not part of the installed application."""
import socket
import threading
import time


def packet(kind, data):
    length = len(data)
    encoded = bytearray()
    while True:
        value = length % 128
        length //= 128
        encoded.append(value | (128 if length else 0))
        if not length:
            break
    return bytes([kind]) + encoded + data


def string(value):
    value = value.encode() if isinstance(value, str) else value
    return len(value).to_bytes(2, "big") + value


class Broker:
    def __init__(self):
        self.socket = socket.socket()
        self.socket.bind(("127.0.0.1", 0))
        self.port = self.socket.getsockname()[1]
        self.socket.listen()
        self.socket.settimeout(0.2)
        self.running = True
        self.clients = []
        self.messages = []
        self.subscriptions = []
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while self.running:
            try:
                client, _ = self.socket.accept()
                self.clients.append(client)
                threading.Thread(target=self.handle, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def handle(self, client):
        def read(size):
            data = b""
            while len(data) < size:
                part = client.recv(size - len(data))
                if not part:
                    raise EOFError()
                data += part
            return data
        try:
            while self.running:
                kind = read(1)[0]
                size, mult = 0, 1
                while True:
                    byte = read(1)[0]
                    size += (byte & 127) * mult
                    mult *= 128
                    if not byte & 128:
                        break
                body = read(size)
                action = kind >> 4
                if action == 1:
                    client.sendall(b"\x20\x02\x00\x00")
                elif action == 8:
                    length = int.from_bytes(body[2:4], "big")
                    self.subscriptions.append(body[4:4 + length].decode())
                    client.sendall(b"\x90\x03" + body[:2] + b"\x00")
                elif action == 3:
                    length = int.from_bytes(body[:2], "big")
                    topic = body[2:2 + length].decode()
                    offset = 2 + length
                    qos = (kind >> 1) & 3
                    if qos:
                        client.sendall(b"\x40\x02" + body[offset:offset + 2])
                        offset += 2
                    self.messages.append((topic, body[offset:], bool(kind & 1)))
                elif action == 12:
                    client.sendall(b"\xd0\x00")
                elif action == 14:
                    break
        except (OSError, EOFError):
            pass
        finally:
            client.close()

    def publish(self, topic, payload):
        data = packet(0x30, string(topic) + payload.encode())
        for client in list(self.clients):
            try:
                client.sendall(data)
            except OSError:
                pass

    def close(self):
        self.running = False
        self.socket.close()
        for client in self.clients:
            try:
                client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            client.close()
        self.thread.join(timeout=1)


def wait_for(predicate, timeout=6):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.03)
    raise AssertionError("Condition did not become true before timeout")
