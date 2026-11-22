"""The icon selector uses only 48px stills, authenticated and cached separately."""
import io
import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from PIL import Image
from ugso_usbhub import icons
from ugso_usbhub.storage import home, load_config
from tests.test_hub import TemporaryHome


def gif():
    stream=io.BytesIO()
    images=[Image.new('RGB',(100,100),color) for color in ('red','blue')]
    images[0].save(stream,format='GIF',save_all=True,append_images=images[1:],duration=200)
    return stream.getvalue()


class ThumbnailTests(TemporaryHome):
    def test_catalog_deduplicates_licences_preserves_metadata_and_invalidates(self):
        icons.import_favorites()
        original=icons.library();wire=icons.catalog()
        self.assertIs(wire,icons.catalog())
        self.assertLess(len(json.dumps(wire)),len(json.dumps(original))*.2)
        for item,packed in zip(original,wire['items']):
            key=packed.get('package_folder') or packed['collection']
            restored={k:v for k,v in packed.items() if k not in ('license_ref','license_refs')}
            restored['license']=wire['licenses'][key][packed['license_ref']]
            self.assertEqual(restored,item)
        icons.add(gif(),'another.gif')
        self.assertEqual(len(icons.catalog()['items']),41)

    def test_identical_file_aliases_group_per_package_without_touching_originals_or_settings(self):
        first=icons.add(gif(),'home.svg.gif','Material Black',tags=['home'],license_text='MIT',package_folder='black')
        second=icons.add(gif(),'home-outlined.gif','Material Black',tags=['outlined'],license_text='Apache',package_folder='black')
        third=icons.add(gif(),'home.gif','Other pack',package_folder='other')
        self.assertEqual(first,second);self.assertEqual(second,third)
        before=load_config();raw=icons.library()
        wire=icons.catalog();self.assertEqual(len(wire['items']),2)
        black=wire['items'][0]
        self.assertEqual(black['aliases'][0]['filename'],'home-outlined.gif')
        self.assertEqual(black['tags'],['home','outlined'])
        self.assertEqual(black['license_refs'],[0,1])
        self.assertEqual(icons.library(),raw);self.assertEqual(load_config(),before)
        self.assertEqual(len(list((home()/'icons/IconPacks').rglob('*.gif'))),3)
        icons.add(gif(),'home-outlined.gif','Material Black',tags=['outlined'],license_text='Apache',package_folder='black')
        self.assertEqual(len(icons.catalog()['items']),2)

    def test_small_still_cache_no_animation_or_full_preview_and_parallel_reuse(self):
        ident=icons.add(gif(),'signal.gif')
        before=load_config()
        with patch.object(icons,'decode_animation',side_effect=AssertionError('No animation in picker')), patch.object(icons,'ensure_cached',side_effect=AssertionError('No full preview')), patch.object(icons,'raster',wraps=icons.raster) as render:
            with ThreadPoolExecutor(max_workers=4) as pool:
                paths=list(pool.map(icons.thumbnail_path,[ident]*4))
            self.assertEqual(render.call_count,1)
            self.assertEqual(render.call_args.kwargs,{'size':48})
            self.assertEqual(len(set(paths)),1)
            with Image.open(paths[0]) as image:
                self.assertEqual(image.size,(48,48))
                self.assertEqual(image.convert('RGB').getpixel((24,24)),(255,0,0))
        with patch.object(icons,'raster',side_effect=AssertionError('Cache must survive renderer restart')):
            self.assertTrue(icons.thumbnail_path(ident).is_file())
        self.assertFalse((home()/'icons'/'.cache'/(ident+'.png')).exists())
        self.assertFalse((home()/'icons'/'.cache'/(ident+'.animation.json')).exists())
        self.assertEqual(load_config(),before)

    def test_legacy_cache_missing_ids_and_removal(self):
        root=home()/'icons';root.mkdir();ident='a'*32
        Image.new('RGB',(256,256),'green').save(root/(ident+'.png'))
        with Image.open(icons.thumbnail_path(ident)) as image:self.assertEqual(image.size,(48,48))
        for bad in ['../config', 'z'*32, 'b'*32]:
            with self.assertRaises((ValueError,FileNotFoundError)):icons.thumbnail_path(bad)
        other=icons.add(gif(),'second.gif','Temporary')
        path=icons.thumbnail_path(other)
        icons.remove_package('Temporary',load_config())
        self.assertFalse(path.exists())

    def test_failed_render_is_retryable_without_partial_png(self):
        ident=icons.add(gif(),'signal.gif')
        with patch.object(icons,'raster',side_effect=OSError('temporary renderer error')):
            with self.assertRaises(OSError):icons.thumbnail_path(ident)
        self.assertFalse(list((home()/'icons'/'.cache').rglob('*.tmp')))
        with patch.object(icons.os,'replace',side_effect=OSError('temporary rename error')):
            with self.assertRaises(OSError):icons.thumbnail_path(ident)
        self.assertFalse(list((home()/'icons'/'.cache').rglob('*.tmp')))
        self.assertTrue(icons.thumbnail_path(ident).is_file())
