"""Shared, unprivileged CLI/MQTT backup. Archives never contain exports recursively."""
from datetime import datetime, timezone
import os
import tarfile
import uuid
from .storage import home


def create_backup():
    folder=home()/'exports';folder.mkdir(exist_ok=True)
    target=folder/('usb-extender-backup-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.tar.gz')
    temporary=target.with_suffix('.part')
    try:
        with os.fdopen(os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:
            with tarfile.open(fileobj=stream,mode='w:gz') as archive:
                for path in sorted(home().iterdir()):
                    if path.name!='exports':archive.add(path,arcname='ugso-usbhub/'+path.name)
        # Verify the entire compressed stream, not just its header.
        import gzip
        with gzip.open(temporary,'rb') as stream:
            while stream.read(1024*1024):pass
        os.replace(temporary,target)
        return target
    finally:
        temporary.unlink(missing_ok=True)
