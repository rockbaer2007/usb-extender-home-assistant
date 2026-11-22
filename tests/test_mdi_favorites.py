"""Check real generated colours, offline pack and installed-package preservation."""
import io
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from PIL import Image
from tools import build_mdi_favorites as builder
from ugso_usbhub import icons
from ugso_usbhub.storage import load_config, save_config, home
from tests.test_hub import TemporaryHome


class FavouriteTests(TemporaryHome):
    def test_all_colors_real_metadata_pairs_and_licences(self):
        colors = list((builder.SOURCE / "colors").glob("*.svg"))
        self.assertEqual(len(colors), 147)
        self.assertEqual(len(builder.catalog()), 20)
        for source in colors:
            folder, files, raw = builder.build_pack(source.stem)
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(len(archive.namelist()), 43)
            entries = json.loads(files["icons.json"])
            self.assertEqual(len(entries), 40)
            for entry in entries:
                self.assertIn(source.stem, entry["tags"])
                icons.validate_svg(files[entry["path"]])
                self.assertIn("mdi:", ET.fromstring(files[entry["path"]]).find("{http://www.w3.org/2000/svg}title").text)
            self.assertIn(b"Apache License", files["license.txt"])
            self.assertIn(b"Copyright 2021 Corsair/Elgato", files["license.txt"])
            self.assertTrue(folder.endswith(".sdIconPack"))

    def test_bundle_is_reproducible_import_and_reimport_keep_ids_and_config(self):
        before = load_config()
        self.assertEqual(icons.import_favorites()["imported"], 40)
        items = icons.library()
        ident = items[0]["id"]
        before["devices"]["existing"] = {"enabled":True,"name":"Existing","targets":["broker1"],"deck_keys":{"0":{"icon":ident}}}
        save_config(before)
        config_bytes = (home() / "config.json").read_bytes()
        bundled = Path(icons.__file__).parent / "bundled/ha-mdi-favorites.streamDeckIconPack"
        self.assertEqual(bundled.read_bytes(), builder.build_pack("steelblue")[2])
        with zipfile.ZipFile(bundled) as archive:
            self.assertTrue(all(info.create_system == 0 for info in archive.infolist()))
        self.assertEqual(icons.import_favorites()["imported"], 40)
        self.assertEqual([x["id"] for x in icons.library()], [x["id"] for x in items])
        self.assertEqual((home() / "config.json").read_bytes(), config_bytes)
        self.assertFalse((home() / "icons/.cache").exists())
        # Fresh library load simulates the restart path without changing stored assignments.
        icons._source_map.cache_clear()
        self.assertEqual(load_config(), before)
        self.assertEqual(len(icons.library()), 40)

    def test_light_dark_and_colored_svg_render_and_states_differ(self):
        for color in ["white", "black", "red", "steelblue"]:
            paths = []
            for state in ["lightbulb", "lightbulb-off"]:
                data = builder.compose(color, state)
                root = ET.fromstring(data)
                self.assertEqual((root.attrib["width"], root.attrib["height"]), ("48", "48"))
                paths.append(icons.raster(data, ".svg"))
                with Image.open(io.BytesIO(paths[-1])) as image:
                    self.assertEqual(image.size, (256, 256))
                    rgb = builder.background(color)[1]
                    self.assertEqual(image.convert("RGB").getpixel((0, 0)), tuple(int(rgb[i:i+2], 16) for i in [1,3,5]))
            self.assertNotEqual(*paths)
        self.assertEqual(builder.foreground("#ffffff"), "#000000")
        self.assertEqual(builder.foreground("#000000"), "#ffffff")

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            sentinel = Path(folder) / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                builder.build(folder, bundle=False)
            self.assertEqual(sentinel.read_text(), "keep")
