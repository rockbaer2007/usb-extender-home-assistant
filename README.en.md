# USB Extender for Home Assistant

**Connect USB input devices and Stream Decks through MQTT — for Raspberry Pi.**

Version **0.1.5** · [Deutsch](README.md) · **English** · [Download ZIP](https://github.com/rockbaer2007/usb-extender-home-assistant/releases/latest)

Illustrated documentation: [English](https://opensource.ugso-software.de/en/projects/usb-extender/)
· [German](https://opensource.ugso-software.de/projects/usb-extender/)
· [French](https://opensource.ugso-software.de/fr/projects/usb-extender/).
The application interface currently uses German labels; the screenshots show that interface.

A Raspberry Pi 4 receives USB keyboard/media-key events and sends them to up to
**three independent MQTT brokers**, including Home Assistant and ioBroker at the
same time. The password-protected web interface is for configuration and can be
stopped completely. USB input and MQTT continue in a separate service.

This is an independent project, not official Home Assistant or Elgato software.
It is an input-to-MQTT bridge, **not a general USB-over-IP tunnel**.

![Key list with readable topics and individual channel controls](docs/screenshots/live-0.1.5/key-list.png)

## Device discovery versus working support

Linux can list many connected USB devices. Being listed does not mean that a
device's protocol is supported. A matching driver and your explicit input
permission are required before events become MQTT messages.

| Device class | Available functionality | Verification |
| --- | --- | --- |
| USB keyboards, including Windows multimedia keyboards | Press/release, click/double-click/hold, toggling switch, pressed-state channel | Trust/HCT keyboards used in the practical setup |
| Media/volume keys | `KEY_VOLUMEUP`, `KEY_VOLUMEDOWN`, `KEY_MUTE`; other reported media keys; configurable volume repeat | Volume/mute inputs observed; test other keys per model |
| HID macro pads, USB pedals and keyboard-like devices | Existing input path if Linux reports normal key codes | Model-dependent; reports welcome |
| Physical Elgato Stream Decks | Dedicated HID driver, display and input features below | Implemented; no physical Stream Deck tested in this project yet |
| Other LCD-key devices resembling a Stream Deck | Keyboard events may work through HID; displays require their own protocol/driver | No blanket compatibility claim |
| Printers, cameras, storage, audio interfaces, serial devices and other controllers | Inventory listing; specific functionality needs a separate adapter | No general print/camera/audio/MIDI/serial forwarding |
| Stream Deck Mobile / tablet app | Not a physical USB Stream Deck connected to the Pi | Not integrated |

### Stream Deck features

- Key press/release/hold and single/double-click recognition, with per-key MQTT routing.
- Custom icons and text on supported display keys; brightness per device.
- MQTT state feedback can change an active icon; targeted display commands are supported.
- On models with dials: rotation direction and dial presses as events.
- On touchscreen models: touch events, **not** a freely designed touchscreen layout.
- Local icon folders, individual images, ZIP files and locally obtained `.streamDeckIconPack` archives.
  Respect each pack's licence; no Marketplace content is bundled. Animated images use the first frame.
- Models without displays, such as Pedal, provide input but do not show display-key icons.

The included `python-elgato-streamdeck` 0.10.0 driver supports models including
Original/MK.2, Mini, XL, Neo, Pedal and Plus. This is a driver capability list,
**not a hardware-tested list for this project**. There is one fixed key layout;
profile/page switching and animated key icons are not implemented.

## Installation and updates

Recommended: Raspberry Pi 4, Raspberry Pi OS Lite **64-bit Bookworm or newer**,
Python 3.11+, systemd, sudo and internet access for apt/PyPI. A powered USB hub may
be needed for multiple display devices. 32-bit Pi OS has not been practically verified.
The ZIP is an installation package, not an offline firmware image.

```bash
sudo apt-get update && sudo apt-get install -y unzip
unzip USB-Extender-Home-Assistant-0.1.5-Raspi4.zip
cd USB-Extender-Home-Assistant-0.1.5
sudo bash install.sh
```

The installer shows nine steps: system/package checks, missing dependencies,
backup, service account/data directory, isolated Python installation, validation,
USB permissions, systemd startup and final status. Existing settings are retained.
It backs up existing data under `/var/backups/` and can restore the previous
program link if the update fails. For an update, extract the new ZIP separately
and run its installer again.

Set a web password when prompted, or run `sudo usb-extender password`. There is
no installed default password. Start the web UI with `sudo usb-extender web start`
and open `http://<raspberry-pi-address>:8098` in your browser.

## First setup and learning

1. Open **MQTT-Broker**, configure up to three brokers and save. Enable HA discovery
   on HA brokers; select **Aus – nur MQTT-Daten senden** for ioBroker.
2. Open **USB-Geräte**, name and explicitly enable the input device, select its
   destination brokers and save. Inventory detection alone does not enable input.
3. Open **Tasten & Anzeigen**, select the device and click **Anlernen starten**.
4. Press and release each wanted key once. Existing assignments and repeated
   presses are not added twice. The selected device does not send actions while learning.
5. Click **Anlernen beenden**, then **Tasten übernehmen**, then **Speichern**.
6. Edit individual names, topics, icons and channel checkboxes in the saved list.
   **Bearbeiten** opens per-key routing, switch behaviour and timing options.

If the browser disconnects, learning expires within 15 seconds. Unsaved learning
drafts remain in the browser only. Existing individual bindings stay available.

## Topics and payloads

New keys receive readable topics such as `trust-keyboard-key-f1/press`. Device
names become MQTT-safe slugs; duplicate names receive readable numeric suffixes.
Saved topics remain stable when the display name is later changed. Explicit
topics have the same name on every selected broker.

| Topic suffix | Payload / behaviour |
| --- | --- |
| `/press` | `press` when pressed |
| `/release` | `release` when released |
| `/press-plus`, `/release-plus` | Same action, then an empty payload after 50 ms |
| `/switch` | First press `ON`, next press `OFF`; release does not toggle |
| `/state` | `ON` while pressed, `OFF` after release |
| `/button` | `click`, `double_click` or `hold` |
| `/button-plus` | Same button event, then an empty payload after 50 ms |
| `/click`, `/double-click`, `/hold` | The respective individual gesture |

All eleven channels are prepared and enabled for newly learned keys. New extra
channels on existing rows remain disabled until selected. Original topics and
plus behaviour on older rows are retained. From 0.1.5, Switch defaults to toggling;
the former momentary mode remains an explicit compatibility option.

Single-click waits for the double-click window (default 300 ms after release).
Double-click does not also send a single-click. Hold fires once after 700 ms and
does not produce a click on release. Holding the second press replaces the
pending click sequence with hold. These times are configurable per key.

Volume keys default to repeating active Press/Press+ channels after 500 ms, every
150 ms while held. Release, Switch and button gestures are not repeated by this
mechanism. It stops on release, known device removal, configuration reload and
after 30 seconds. Your HA/ioBroker automation determines the volume step.

Switch values persist in `switches.json` and are synchronized after reconnecting.
Data messages use QoS 0, are not retained, and offline key events are not replayed.
The UI's “passed to MQTT” indication confirms local publication acceptance, not
broker receipt or the creation of a downstream entity.

## Home Assistant and ioBroker

HA discovery groups all keys of a USB device under the same stable device
identifier and selected device name. Actions are device triggers with payload
filters; Switch and pressed state are separate binary sensors. An automation or
mapping is needed to control another device — the binary sensor is a state indicator.

In ioBroker, keep HA discovery off and use the MQTT topics. The MQTT adapter can
create separate states when their first messages arrive. Empty plus-channel
resets appear as `(null)` in the supplied practical setup; this is expected.
Discovery configuration messages themselves remain JSON, as required by HA.

![Separate MQTT states in ioBroker](docs/screenshots/live-0.1.5/iobroker-states.png)

The user's 0.1.5 screenshots show three broker profiles online, function-key
messages, individual ioBroker states and HA Switch/pressed-state values after
key use. They visibly include `press`, `release`, `click`, `hold`, `ON` and `OFF`.
They do not establish every function on every physical device. Double-click,
restart persistence and failure paths have automated tests; physical Stream Deck
verification remains open. There are **61 Python tests** plus JavaScript/DOM checks.

## Web UI and backups

```bash
sudo usb-extender web start
sudo usb-extender web stop
sudo usb-extender web status
sudo usb-extender web enable
sudo usb-extender web disable
sudo usb-extender backup
sudo journalctl -u ugso-usbhub -n 50
```

Closing a browser tab does not stop the web service; `web stop` closes the HTTP
listener while USB/MQTT keep running. The data directory is
`/var/lib/ugso-usbhub/`; the previous ten configuration versions are backed up
automatically. Full CLI backups also include icons and saved switch state.
The internal service name remains `ugso-usbhub`.

Use HTTP only in a trusted local network, or put it behind VPN/HTTPS. Do not
expose the interface directly to the internet. The service's Linux `input` group
access is wider than the app's per-device software permission. MQTT credentials
must be locally readable for connections; configuration files and backups are
restricted, and passwords are not returned by the web configuration API.

## Please test your Stream Deck or similar device

[Submit a hardware test](https://github.com/rockbaer2007/usb-extender-home-assistant/issues/new?template=hardware-test.yml).
Please include the exact model/revision, Pi model, OS and app version. Explain
whether the device is merely listed or actually produces key codes, and which
features work: press/release, click/double-click/hold, icons/text, brightness,
dials, touch and unplug/replug. For other LCD-key devices, a report may help assess
whether a separate adapter can be written; it does not imply existing support.

Use a harmless MQTT topic first, without controlling real devices. Screenshots
of inventory and input events help. Do not publish passwords, tokens,
`config.json` or backup archives. Bug reports and contributions are welcome.

More: [Changelog](CHANGELOG.md) · [Roadmap](ROADMAP.md) · [Test report, German](TESTBERICHT.md).
The new `docs/screenshots/live-0.1.5/` images are user-supplied practical screenshots;
older `*-demo.jpg` files show synthetic local data. Dependencies and iconpacks
retain their respective licences. No third-party Marketplace content is bundled.
