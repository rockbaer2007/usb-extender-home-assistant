"""Socket-activated root helper: fixed web-unit actions, no shell or user paths."""
import json
import socket
import subprocess
import logging

SOCKET='/run/ugso-usbhub-control/control.sock'
UNIT='ugso-usbhub-web.service'
OPERATIONS={'start':['start'],'stop':['stop'],'enable':['enable','--now'],'disable':['disable','--now']}


def perform(action):
    if action not in {*OPERATIONS,'status'}:raise ValueError('Unbekannter Webbefehl')
    if action in OPERATIONS:
        subprocess.run(['systemctl',*OPERATIONS[action],UNIT],check=True,timeout=20,capture_output=True)
    def flag(verb):
        result=subprocess.run(['systemctl',verb,'--quiet',UNIT],timeout=5,capture_output=True)
        if result.returncode not in (0,1,3):raise OSError('Webdienststatus nicht ermittelbar')
        return result.returncode==0
    return {'running':flag('is-active'),'autorun':flag('is-enabled')}


def request(action):
    if action not in {*OPERATIONS,'status'}:raise ValueError('Unbekannter Webbefehl')
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as client:
        client.settimeout(30);client.connect(SOCKET)
        client.sendall((action+'\n').encode('ascii'));client.shutdown(socket.SHUT_WR)
        data=b''
        while len(data)<=4096:
            part=client.recv(4097-len(data))
            if not part:break
            data+=part
        if len(data)>4096:raise ValueError('Ungültige Steuerantwort')
    result=json.loads(data)
    if result.get('error'):raise OSError(result['error'])
    if any(type(result.get(key)) is not bool for key in ('running','autorun')):raise ValueError('Ungültiger Webstatus')
    return result


def main():
    # StandardInput=socket supplies one connection per service instance.
    with socket.socket(fileno=0) as connection:
        connection.settimeout(5)
        data=b''
        try:
            while len(data)<=32 and not data.endswith(b'\n'):
                part=connection.recv(33-len(data))
                if not part:break
                data+=part
            if len(data)>32 or not data.endswith(b'\n'):raise ValueError('Ungültiger Steuerauftrag')
            result=perform(data.decode('ascii').strip())
        except Exception:
            logging.exception('Websteuerauftrag fehlgeschlagen')
            result={'error':'Websteuerung fehlgeschlagen; Dienstprotokoll prüfen'}
        connection.sendall(json.dumps(result).encode('utf-8'))


if __name__=='__main__':main()
