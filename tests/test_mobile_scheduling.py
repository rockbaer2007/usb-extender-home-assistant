"""Bounded image work leaves input and heartbeat handling a turn."""
import io
import threading
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
from tests.test_hub import TemporaryHome
from ugso_usbhub.mobile import Session, IMAGE_BATCH_SIZE
from ugso_usbhub.mobile_protocol import ClientMessage


def png(color):
    out=io.BytesIO()
    Image.new('RGB',(144,144),color).save(out,format='PNG')
    return out.getvalue()


class SchedulingTests(TemporaryHome):
    def session(self):
        self.events=[]
        owner=SimpleNamespace(config={},lock=threading.RLock(),
                              emit=lambda *args:self.events.append(args),
                              refresh_required=threading.Event())
        ws=SimpleNamespace(ping=lambda data:threading.Event())
        session=Session(owner,ws)
        session.authorized=True;session.device='tablet';session.size=(144,144)
        session.layout=(8,8)
        return session

    def test_slow_64_key_send_returns_to_input_and_heartbeat(self):
        clock=[0.0]
        with patch('ugso_usbhub.mobile.time.monotonic',side_effect=lambda:clock[0]):
            session=self.session()
            session.images={key:png('red') for key in range(64)}
            sent=[]
            def slow_send(message):
                sent.append(message.icon.index)
                clock[0]+=1.5
            session.send=slow_send
            session.flush_images()
            self.assertEqual(sent,[0])
            self.assertEqual(len(session.images),63)
            session.process(ClientMessage(keyPress={'index':0,'pressed':True}))
            self.assertEqual(self.events,[('tablet','key:0','press',1)])
            clock[0]=5.0;session.heartbeat()
            self.assertEqual(session.pings_sent,1)
            # Previously one call sent all 64 frames (96 simulated seconds),
            # preventing the same handler from reading the next input packet.

    def test_bounded_batches_coalesce_newer_images_and_become_idle(self):
        session=self.session();red=png('red');blue=png('blue')
        session.images={key:red for key in range(64)}
        sent=[]
        def send(message):
            sent.append(message.icon.index)
            if message.icon.index==0:session.images[10]=blue
        session.send=send
        session.flush_images()
        self.assertLessEqual(len(sent),IMAGE_BATCH_SIZE)
        self.assertEqual(session.images[10],blue)
        while session.images:session.flush_images()
        self.assertEqual(sent,list(range(64)))
        self.assertEqual(session.images_sent,64)
        session.flush_images()
        self.assertEqual(session.images_sent,64)
        session.images={key:(blue if key==10 else red) for key in range(64)}
        while session.images:session.flush_images()
        self.assertEqual(session.images_sent,64,'Identical images are not resent')
