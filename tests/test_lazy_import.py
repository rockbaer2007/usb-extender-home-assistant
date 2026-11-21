"""Batch commits and on-demand rendering without changing existing mappings."""
import io
import json
import zipfile
import hashlib
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from PIL import Image
from ugso_usbhub import icons
from ugso_usbhub.storage import home, load_config, save_config, atomic_json
from tests.test_hub import TemporaryHome


def png(color='red'):
    out=io.BytesIO();Image.new('RGB',(16,16),color).save(out,format='PNG');return out.getvalue()


def package(count=80):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        z.writestr('demo.sdIconPack/manifest.json',json.dumps({'Name':'Readable'}))
        z.writestr('demo.sdIconPack/icons.json',json.dumps([{'path':'icons/0.png','name':'Label','tags':['tag']}]))
        for n in range(count):z.writestr(f'demo.sdIconPack/icons/{n}.png',png((n%256,n//256,50)))
    return out.getvalue()


class LazyImportTests(TemporaryHome):
    def test_pi_folder_uses_one_index_commit(self):
        source=home()/'source';source.mkdir()
        for n in range(5):(source/f'{n}.png').write_bytes(png((n,30,70)))
        with patch.object(icons,'atomic_json',wraps=icons.atomic_json) as write, patch.object(icons,'raster',side_effect=AssertionError('eager')):
            self.assertEqual(icons.import_folder(source)['imported'],5)
            self.assertEqual(sum(c.args[0].name=='index.json' for c in write.call_args_list),1)

    def test_archive_writes_index_once_and_renders_only_requested_icon(self):
        before=load_config()
        with patch.object(icons,'atomic_json',wraps=icons.atomic_json) as write, patch.object(icons,'raster',side_effect=AssertionError('eager render')):
            self.assertEqual(icons.import_archive(package(),'demo.zip')['imported'],80)
            self.assertEqual(sum(call.args[0].name=='index.json' for call in write.call_args_list),1)
        self.assertFalse((home()/'icons'/'.cache').exists())
        items=icons.library();self.assertEqual(items[0]['name'],'Label');self.assertEqual(items[0]['tags'],['tag'])
        with patch.object(icons,'raster',wraps=icons.raster) as render:
            ident=items[0]['id']
            with ThreadPoolExecutor(max_workers=4) as pool:paths=list(pool.map(lambda _:icons.cached_path(ident),range(4)))
            self.assertEqual(render.call_count,1)
            self.assertTrue(all(p==paths[0] for p in paths))
        self.assertEqual(len(list((home()/'icons'/'.cache').glob('*.png'))),1)
        self.assertEqual(before,load_config())

    def test_existing_original_and_legacy_id_survive_reimport(self):
        data=png();old_png=icons.raster(data,'.png');ident=hashlib.sha256(old_png).hexdigest()[:32]
        root=home()/'icons';source=root/'IconPacks'/'demo.sdIconPack'/'icons'/'0.png';source.parent.mkdir(parents=True)
        source.write_bytes(data);(root/(ident+'.png')).write_bytes(old_png)
        atomic_json(root/'index.json',[{'id':ident,'collection':'demo.sdIconPack','name':'0','original_path':'IconPacks/demo.sdIconPack/icons/0.png','filename':'0.png'}])
        cfg=load_config();cfg['devices']['deck']={'deck_keys':{'0':{'icon':ident}}};save_config(cfg)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('demo.sdIconPack/manifest.json',json.dumps({'Name':'Renamed'}));z.writestr('demo.sdIconPack/icons/0.png',data)
        with patch.object(icons,'raster',side_effect=AssertionError('no eager conversion')):
            icons.import_archive(out.getvalue(),'demo.zip')
        self.assertEqual(icons.library()[0]['id'],ident);self.assertEqual(len(icons.library()),1)
        self.assertEqual(load_config(),cfg);self.assertEqual(icons.cached_path(ident).read_bytes(),old_png)

    def test_folder_upload_archive_multiple_packages_preserves_paths(self):
        ident=icons.add(png(),'Signal.png','One',subfolder='icons',package_folder='one.sdIconPack')
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('IconPacks/one.sdIconPack/manifest.json',json.dumps({'Name':'One'}))
            z.writestr('IconPacks/one.sdIconPack/icons/Signal.png',png())
            z.writestr('IconPacks/BLUE ICONS/Lamp.png',png('blue'))
        with patch.object(icons,'atomic_json',wraps=icons.atomic_json) as write:
            self.assertEqual(icons.import_archive(out.getvalue(),'IconPacks.zip')['imported'],2)
            self.assertEqual(sum(c.args[0].name=='index.json' for c in write.call_args_list),1)
        self.assertEqual(len(icons.library()),2);self.assertEqual(icons.library()[0]['id'],ident)
        self.assertEqual(icons.library()[1]['original_path'],'IconPacks/BLUE ICONS/Lamp.png')

    def test_failed_final_commit_keeps_previous_index_and_settings(self):
        icons.add(png(),'Existing.png');root=home()/'icons';before=(root/'index.json').read_bytes();cfg=load_config()
        with patch.object(icons,'atomic_json',side_effect=OSError('simulated full disk')):
            with self.assertRaises(OSError):icons.import_archive(package(3),'demo.zip')
        self.assertEqual((root/'index.json').read_bytes(),before);self.assertEqual(load_config(),cfg)

    def test_failed_preview_can_retry_without_losing_original(self):
        ident=icons.add(png(),'Original.png');before=icons.library()
        with patch.object(icons,'raster',side_effect=OSError('temporary renderer failure')):
            with self.assertRaises(OSError):icons.cached_path(ident)
        self.assertEqual(icons.library(),before)
        self.assertTrue(icons.cached_path(ident).is_file())
