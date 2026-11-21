"""Deterministic button gestures; independent of OS key-repeat events."""


class Buttons:
    def __init__(self):
        self.keys = {}

    def cancel(self, key=None, device=None):
        for ident in list(self.keys):
            if (key is None or key == ident) and (device is None or ident[0] == device):
                self.keys.pop(ident, None)

    def feed(self, key, gesture, now, row):
        emitted = self.tick(now)
        if gesture not in ("press", "release"):
            return emitted
        if gesture == "release" and key not in self.keys:
            return emitted
        state = self.keys.setdefault(key, {"down": False, "pending": None, "held": False})
        if gesture == "press" and not state["down"]:
            state.update(down=True, since=now, held=False, second=state["pending"] is not None,
                         hold_ms=row.get("hold_ms", 700), double_ms=row.get("double_ms", 300))
            state["pending"] = None
        elif gesture == "release" and state["down"]:
            state["down"] = False
            if state["held"]:
                self.keys.pop(key, None)
            elif state.get("second"):
                emitted.append((key, "button_double_click"))
                self.keys.pop(key, None)
            else:
                state["pending"] = now + state["double_ms"] / 1000
        return emitted

    def tick(self, now):
        emitted = []
        for key, state in list(self.keys.items()):
            if state["down"] and not state["held"] and now - state["since"] >= state["hold_ms"] / 1000:
                state["held"] = True
                emitted.append((key, "button_hold"))
            elif not state["down"] and state["pending"] is not None and now >= state["pending"]:
                emitted.append((key, "button_click"))
                self.keys.pop(key, None)
        return emitted
