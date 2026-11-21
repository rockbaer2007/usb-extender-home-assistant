"""Animation preservation, original paths, scheduler and library removal."""
import base64
import io
import json
import zipfile
from unittest.mock import Mock
from PIL import Image
from ugso_usbhub import icons
from ugso_usbhub.deck import key_image
from ugso_usbhub.hardware import Hardware
from ugso_usbhub.storage import home, load_config, save_config
from tests.test_hub import TemporaryHome, WebTests


def moving(fmt="GIF"):
    out = io.BytesIO()
    images = [Image.new("RGB", (24,24), color) for color in ("red", "blue")]
    images[0].save(out, format=fmt, save_all=True, append_images=images[1:], duration=[50,200], loop=0)
    return out.getvalue()


class AnimationTests(TemporaryHome):
    def test_archive_progress_counts_only_candidates_including_failures(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('demo.sdIconPack/manifest.json',json.dumps({'Name':'Readable package'}))
            z.writestr('demo.sdIconPack/icons/Good.gif',moving())
            z.writestr('demo.sdIconPack/icons/Broken.png',b'not an image')
            z.writestr('demo.sdIconPack/code.js','never execute')
        progress=[]
        result=icons.import_archive(out.getvalue(),'demo.zip',lambda *values:progress.append(values))
        self.assertEqual(result['imported'],1);self.assertEqual(len(result['skipped']),1)
        self.assertEqual([(x[0],x[1]) for x in progress],[(0,2),(1,2),(2,2)])
        self.assertEqual(icons.library()[0]['collection'],'Readable package')

    def test_reimport_renames_collection_without_duplicate_ids(self):
        ident=icons.add(moving(),'Signal.gif','demo.sdIconPack',package_folder='demo.sdIconPack')
        self.assertEqual(icons.add(moving(),'Signal.gif','Readable title',package_folder='demo.sdIconPack'),ident)
        self.assertEqual(len(icons.library()),1)
        self.assertEqual(icons.library()[0]['collection'],'Readable title')
    def test_identical_images_keep_distinct_original_names_and_old_ids_load(self):
        ident=icons.add(moving(),"One.gif","Alias")
        self.assertEqual(ident,icons.add(moving(),"Two.gif","Alias"))
        self.assertEqual({i["filename"] for i in icons.library()}, {"One.gif","Two.gif"})
        icons.add(moving(),"One.gif","Alias")
        self.assertEqual(len(icons.library()),2)
        legacy="f"*32
        out=io.BytesIO();Image.new("RGB",(10,10),"green").save(out,format="PNG")
        (home()/"icons"/(legacy+".png")).write_bytes(out.getvalue())
        self.assertEqual(key_image((72,72),{},legacy).getpixel((30,30)),(0,128,0))

    def test_full_disk_stops_import_before_original_write(self):
        from unittest.mock import patch
        with patch('ugso_usbhub.icons.shutil.disk_usage',return_value=__import__('types').SimpleNamespace(free=0)):
            with self.assertRaisesRegex(ValueError,"Speicher"):
                icons.add(moving(),"No-space.gif")
        self.assertFalse(icons.library())
        self.assertFalse(list((home()/"icons").rglob("No-space.gif")))
    def test_frames_original_filename_and_same_first_frame_differ(self):
        ident=icons.add(moving(), "Signal.gif", "Test", subfolder="Audio", package_folder="test.sdIconPack")
        item=icons.library()[0]
        self.assertEqual(item["filename"], "Signal.gif")
        self.assertEqual(item["original_path"], "IconPacks/test.sdIconPack/Audio/Signal.gif")
        self.assertEqual((home()/"icons"/item["original_path"]).read_bytes(), moving())
        self.assertEqual(icons.animation(ident), [100,200])
        self.assertEqual(key_image((72,72), {}, ident, frame_index=0).getpixel((30,30)), (255,0,0))
        self.assertEqual(key_image((72,72), {}, ident, frame_index=1).getpixel((30,30)), (0,0,255))
        out=io.BytesIO();Image.new("RGB",(24,24),"red").save(out,format="PNG")
        self.assertNotEqual(ident, icons.add(out.getvalue(),"Still.png"))
        with Image.open(icons.cached_path(ident,".webp")) as preview:
            self.assertEqual(preview.n_frames,2)

    def test_animated_webp_and_frame_limit(self):
        ident=icons.add(moving("WEBP"),"Motion.webp")
        self.assertEqual(len(icons.animation(ident)),2)
        from unittest.mock import patch
        with patch.object(icons,"MAX_FRAMES",1):
            with self.assertRaisesRegex(ValueError,"maximal"):
                icons.add(moving(),"Too-many.gif")

    def test_scheduler_switches_normal_pressed_and_static_stays_quiet(self):
        normal=icons.add(moving(),"Normal.gif")
        out=io.BytesIO();Image.new("RGB",(24,24),"green").save(out,format="PNG")
        static=icons.add(out.getvalue(),"Green.png")
        pressed=icons.add(moving("WEBP"),"Pressed.webp")
        hardware=Hardware(lambda *a:None)
        deck=Mock();deck.connected.return_value=True;deck.key_count.return_value=1;deck.is_visual.return_value=True
        deck.key_image_format.return_value={"size":(72,72),"format":"BMP","rotation":0,"flip":(False,False)}
        hardware.decks["deck"]=deck
        style={"icon":normal,"pressed_icon":pressed}
        hardware.config={"devices":{"deck":{"deck_keys":{"0":style}}},"bindings":[]}
        hardware.display("deck",0,normal)
        job=hardware.animations[("deck",0)]
        first=deck.set_key_image.call_args.args[1]
        hardware.animate(job["start"]+.15)
        self.assertNotEqual(deck.set_key_image.call_args.args[1],first)
        count=deck.set_key_image.call_count;hardware.animate(job["start"]+.16)
        self.assertEqual(deck.set_key_image.call_count,count)
        hardware.set_pressed("deck",0,True)
        self.assertEqual(hardware.animations[("deck",0)]["index"],0)
        hardware.set_pressed("deck",0,False)
        self.assertEqual(deck.set_key_image.call_args.args[1],first)
        hardware.display("deck",0,static);count=deck.set_key_image.call_count
        hardware.animate(job["start"]+20)
        self.assertEqual(deck.set_key_image.call_count,count)
        hardware.display("deck",0,normal);deck.connected.return_value=False;hardware.animate()
        self.assertFalse(hardware.animations)

    def test_multiple_pack_folders_and_safe_removal_backup(self):
        source=home()/"source"/"IconPacks"
        for package in ("one.sdIconPack","two.sdIconPack"):
            folder=source/package/"icons"/"Audio";folder.mkdir(parents=True)
            (folder/"Signal.gif").write_bytes(moving())
            (folder.parent.parent/"manifest.json").write_text(json.dumps({"Name":package}))
        self.assertEqual(icons.import_folder(source)["imported"],2)
        self.assertEqual({i["package_folder"] for i in icons.library()}, {"one.sdIconPack","two.sdIconPack"})
        ident=icons.library()[0]["id"]
        with self.assertRaisesRegex(ValueError,"verwendet"):
            icons.remove_package("one.sdIconPack",{"icon":ident})
        result=icons.remove_package("one.sdIconPack",{})
        self.assertTrue(__import__('pathlib').Path(result["backup"]).is_file())
        self.assertEqual(len(icons.library()),1)
        self.assertTrue(icons.cached_path(ident).exists())
        icons.remove_package("two.sdIconPack",{})
        self.assertFalse(icons.cached_path(ident).exists())

    def test_binary_plugin_manifest_only_images_imported(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,"w") as z:
            z.writestr("test.sdPlugin/manifest.json",b"ELGATO\xff")
            z.writestr("test.sdPlugin/images/sub/Signal.gif",moving())
            z.writestr("test.sdPlugin/imgs/actions/fan/Signal.gif",moving())
            z.writestr("test.sdPlugin/plugin.js","throw Error('never execute')")
        self.assertEqual(icons.import_archive(out.getvalue(),"Test.streamDeckPlugin")["imported"],2)
        self.assertEqual({i["subfolder"] for i in icons.library()}, {"images/sub","imgs/actions/fan"})


class AnimationWebTests(WebTests):
    def test_progress_is_readable_while_upload_holds_mutation_lock(self):
        import threading
        from unittest.mock import patch
        import urllib.error
        with self.assertRaises(urllib.error.HTTPError) as denied:
            self.request('/api/icons/progress')
        self.assertEqual(denied.exception.code,401)
        self.login();started=threading.Event();release=threading.Event();errors=[]
        def importing(data,name,progress=None):
            progress(3,10,'icons/Third.png');started.set();release.wait(3)
            progress(10,10,'icons/Last.png')
            return {'imported':10,'skipped':[]}
        def upload():
            try:
                with self.request('/api/icons/upload',{'name':'test.zip','data':base64.b64encode(b'test').decode(),'import_id':'probe'}) as r:
                    self.assertEqual(json.load(r)['imported'],10)
            except Exception as exc:errors.append(exc)
        with patch('ugso_usbhub.web.icons.import_archive',side_effect=importing):
            worker=threading.Thread(target=upload);worker.start()
            try:
                self.assertTrue(started.wait(2))
                with self.request('/api/icons/progress') as r:state=json.load(r)
                self.assertEqual((state['id'],state['current'],state['total']),('probe',3,10))
            finally:
                release.set();worker.join(4)
        self.assertFalse(worker.is_alive());self.assertEqual(errors,[])

    def test_storage_status_reports_data_filesystem_without_settings_changes(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        self.login();before=load_config()
        with patch('ugso_usbhub.web.shutil.disk_usage',return_value=SimpleNamespace(free=2*1024**3,total=8*1024**3)):
            with self.request('/api/status') as r:
                self.assertEqual(json.load(r)['storage'],{'free':2*1024**3,'total':8*1024**3})
        self.assertEqual(before,load_config())

    def test_animated_preview_normal_pressed_and_serve(self):
        self.login()
        ident=icons.add(moving(),"Signal.gif")
        before=load_config()
        for style,pressed in [({"icon":ident},False),({"pressed_icon":ident},True)]:
            with self.request("/api/deck/preview",{"style":style,"size":[72,72],"pressed":pressed}) as r:
                result=json.load(r)
            self.assertEqual(result["mime"],"image/webp")
            with Image.open(io.BytesIO(base64.b64decode(result["image"]))) as image:
                self.assertEqual(image.n_frames,2)
            with self.request("/icons/"+ident+".webp") as r:
                self.assertEqual(r.headers.get_content_type(),"image/webp")
        self.assertEqual(before,load_config())
