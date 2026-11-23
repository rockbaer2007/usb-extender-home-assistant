from pathlib import Path
from unittest.mock import patch
from tests.test_hub import TemporaryHome
from ugso_usbhub.hardware import usb_storage
from ugso_usbhub.devices import remember_hardware
from ugso_usbhub.storage import load_config, save_config, validate


class USBDriveTests(TemporaryHome):
    def test_mass_storage_interface_and_composite_keyboard(self):
        root=Path(self.temp.name);device=root/'1-2';device.mkdir()
        (device/'bDeviceClass').write_text('00')
        interface=root/'interface';interface.mkdir()
        (interface/'bInterfaceClass').write_text('03')
        with patch.object(Path,'glob',return_value=[interface]) as glob:
            self.assertFalse(usb_storage(device))
            glob.assert_called_with('1-2:*')
            (interface/'bInterfaceClass').write_text('08')
            self.assertTrue(usb_storage(device))
        (interface/'bInterfaceClass').unlink()
        (device/'bDeviceClass').write_text('08')
        self.assertTrue(usb_storage(device))

    def test_view_and_drive_descriptor_survive_reload_without_changing_routes(self):
        config=load_config()
        config['devices']['drive']={'name':'SanDisk','enabled':False,'targets':['broker2'],'device_view':'system'}
        config['devices']['keyboard']={'enabled':True,'targets':['broker1']}
        config.setdefault('mobile',{})['paired']={'test':'preserved'}
        remember_hardware(config,[{'id':'drive','kind':'inventory','usb_storage':True}])
        for mode in ('system','hidden','normal'):
            config['devices']['drive']['device_view']=mode
            save_config(config);saved=load_config()
            self.assertEqual(saved['devices']['drive']['device_view'],mode)
            self.assertEqual(saved['devices']['drive']['hardware']['usb_class'],'mass-storage')
            self.assertEqual(saved['devices']['drive']['targets'],['broker2'])
            self.assertEqual(saved['devices']['keyboard'],config['devices']['keyboard'])
            self.assertEqual(saved['mobile']['paired'],{'test':'preserved'})

    def test_exclusive_view_rejects_invalid_or_combined_value(self):
        config=load_config();config['devices']['drive']={'device_view':'system,hidden'}
        with self.assertRaises(ValueError):validate(config)
