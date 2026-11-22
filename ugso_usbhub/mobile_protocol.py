"""Independent VSD2 wire definitions from observed field contracts.

No vendor application code or binaries are distributed. The implemented subset
provides device-isolated deck pages; optional shortcut features remain unsupported.
"""
import secrets
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
from nacl.bindings import crypto_box_afternm, crypto_box_open_afternm, crypto_box_beforenm

U32, TEXT, BYTES, BOOL, MESSAGE = 13, 9, 12, 8, 11
# name: (field number, field name, scalar type or referenced message, repeated)
DEFINITIONS = {
    "Size": [(1,"width",U32),(2,"height",U32)],
    "Image": [(1,"format",U32),(2,"type",U32),(3,"size","Size"),(4,"rowBytes",U32),(5,"image",BYTES)],
    "ClientInformation": [(1,"name",TEXT),(2,"userAgent",TEXT),(3,"protocolVersion",U32),(4,"deviceModel",TEXT),(5,"osName",TEXT),(6,"osVersion",TEXT)],
    "HelloFromClient": [(1,"publicKey",BYTES),(2,"clientInformation","ClientInformation")],
    "HelloFromServer": [(1,"workstationID",TEXT),(2,"hostname",TEXT),(3,"version",TEXT),(4,"protocolVersion",U32),(5,"publicKey",BYTES),(6,"clientNeedsAuthentication",BOOL),(7,"osName",TEXT),(8,"osVersion",TEXT),(9,"endpoints","ServiceEndpoints")],
    "ServiceEndpoints": [(1,"addresses",TEXT,True),(2,"port",U32)],
    "Authenticate": [(1,"requestID",U32)],
    "CancelAuthenticate": [(1,"requestID",U32)],
    "Ok": [(1,"requestID",U32)],
    "Error": [(1,"requestID",U32),(2,"code",U32),(3,"reason",TEXT)],
    "KeypadConfig": [(1,"supportedIconImageFormats",U32,True),(2,"iconSize","Size"),(3,"pressedIconSize","Size"),(4,"highDPI",BOOL),(5,"overscale",BOOL),(6,"layoutCrop","Size"),(7,"enableContextAPI",BOOL)],
    "UpdateKeypadConfig": [(1,"iconSize","Size"),(2,"pressedIconSize","Size"),(3,"highDPI",BOOL),(4,"layoutCrop","Size")],
    "VirtualDevice": [(1,"id",TEXT),(2,"name",TEXT)],
    "VirtualDeviceList": [(1,"devices","VirtualDevice",True)],
    "CreateVirtualDevice": [(1,"requestID",U32),(2,"name",TEXT),(3,"keypadConfig","KeypadConfig"),(4,"skipUniquenessOfNameValidation",BOOL)],
    "OpenVirtualDevice": [(1,"requestID",U32),(2,"deviceID",TEXT),(3,"keypadConfig","KeypadConfig")],
    "DeleteVirtualDevice": [],
    "VirtualDeviceOpened": [(1,"requestID",U32),(2,"device","VirtualDevice")],
    "KeyPress": [(1,"index",U32),(2,"pressed",BOOL)],
    "Icon": [(1,"index",U32),(2,"image","Image")],
    "Action": [(1,"index",U32),(2,"title",TEXT),(3,"name",TEXT),(4,"category",TEXT)],
    "Context": [(1,"profileID",TEXT),(2,"totalPages",U32),(3,"currentPage",U32),(4,"actions","Action",True)],
    "NextPage": [], "PreviousPage": [], "PageByIndex": [(1,"index",U32)],
    "ClientCapabilities": [(1,"isUserPro",BOOL)],
    "AssignShortcut": [(1,"profileID",TEXT),(2,"shortcutID",TEXT),(3,"index",U32)],
    "RemoveShortcut": [(1,"requestID",U32),(2,"shortcutID",TEXT)],
    "TriggerShortcut": [(1,"deviceID",TEXT),(2,"shortcutID",TEXT)],
    "ServerMessage": [(1,"error","Error"),(2,"ok","Ok"),(10,"hello","HelloFromServer"),(20,"virtualDeviceList","VirtualDeviceList"),(21,"virtualDeviceOpened","VirtualDeviceOpened"),(30,"context","Context"),(40,"icon","Icon")],
    "ClientMessage": [(1,"hello","HelloFromClient"),(2,"authenticate","Authenticate"),(3,"cancelAuthenticate","CancelAuthenticate"),(10,"createVirtualDevice","CreateVirtualDevice"),(11,"openVirtualDevice","OpenVirtualDevice"),(12,"deleteVirtualDevice","DeleteVirtualDevice"),(20,"keyPress","KeyPress"),(21,"nextPage","NextPage"),(22,"previousPage","PreviousPage"),(23,"pageByIndex","PageByIndex"),(30,"updateKeypadConfig","UpdateKeypadConfig"),(31,"assignShortcut","AssignShortcut"),(32,"removeShortcut","RemoveShortcut"),(33,"triggerShortcut","TriggerShortcut"),(100,"clientCapabilities","ClientCapabilities")],
}


def definitions():
    file = descriptor_pb2.FileDescriptorProto(name="usb_extender_mobile.proto", package="vsd2", syntax="proto3")
    for name, fields in DEFINITIONS.items():
        message = file.message_type.add(name=name)
        envelope = name in ("ServerMessage", "ClientMessage")
        if envelope:
            message.oneof_decl.add(name="payload")
        for number, field_name, kind, *repeated in fields:
            field = message.field.add(name=field_name, number=number, type=MESSAGE if isinstance(kind,str) else kind,
                                      label=3 if repeated and repeated[0] else 1)
            if isinstance(kind, str):
                field.type_name = ".vsd2." + kind
            if envelope:
                field.oneof_index = 0
    pool = descriptor_pool.DescriptorPool()
    pool.Add(file)
    return {name: message_factory.GetMessageClass(pool.FindMessageTypeByName("vsd2."+name)) for name in DEFINITIONS}


MESSAGES = definitions()
ClientMessage = MESSAGES["ClientMessage"]
ServerMessage = MESSAGES["ServerMessage"]


def shared_key(public, secret):
    if len(public) != 32 or len(secret) != 32:
        raise ValueError("Ungültige Mobile-Schlüssellänge")
    return crypto_box_beforenm(public, secret)


def encrypt(data, key):
    nonce = secrets.token_bytes(24)
    return nonce + crypto_box_afternm(data, nonce, key)


def decrypt(data, key):
    if not isinstance(data, bytes) or not 40 <= len(data) <= 65536:
        raise ValueError("Ungültiges Mobile-Paket")
    return crypto_box_open_afternm(data[24:], data[:24], key)
