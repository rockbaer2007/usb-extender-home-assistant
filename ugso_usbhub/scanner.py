"""Opt-in USB HID keyboard scanner. Decode data only; never execute QR content."""
from urllib.parse import unquote, urlsplit

MAX_BYTES = 4096
LETTERS = {'KEY_'+c.upper():c for c in 'abcdefghijklmnopqrstuvwxyz'}
US = {**{k:(v,v.upper()) for k,v in LETTERS.items()},
      **{'KEY_'+n:(n,s) for n,s in zip('1234567890','!@#$%^&*()')},
      'KEY_SPACE':(' ',' '),'KEY_MINUS':('-','_'),'KEY_EQUAL':('=','+'),
      'KEY_LEFTBRACE':('[','{'),'KEY_RIGHTBRACE':(']','}'),'KEY_BACKSLASH':('\\','|'),
      'KEY_SEMICOLON':(';',':'),'KEY_APOSTROPHE':("'",'"'),'KEY_GRAVE':('`','~'),
      'KEY_COMMA':(',','<'),'KEY_DOT':('.','>'),'KEY_SLASH':('/','?')}
DE = {**US,'KEY_Y':('z','Z'),'KEY_Z':('y','Y'),
      **{'KEY_'+n:(n,s) for n,s in zip('1234567890','!"§$%&/()=')},
      'KEY_MINUS':('ß','?'),'KEY_EQUAL':('´','`'),'KEY_LEFTBRACE':('ü','Ü'),
      'KEY_RIGHTBRACE':('+','*'),'KEY_BACKSLASH':('#',"'"),'KEY_SEMICOLON':('ö','Ö'),
      'KEY_APOSTROPHE':('ä','Ä'),'KEY_GRAVE':('^','°'),'KEY_COMMA':(',',';'),
      'KEY_DOT':('.',':'),'KEY_SLASH':('-','_'),'KEY_102ND':('<','>')}
ALTGR = {'KEY_Q':'@','KEY_E':'€','KEY_M':'µ','KEY_7':'{','KEY_8':'[',
         'KEY_9':']','KEY_0':'}','KEY_MINUS':'\\','KEY_RIGHTBRACE':'~','KEY_102ND':'|'}
KEYPAD = {'KEY_KP'+n:n for n in '0123456789'}
KEYPAD.update({'KEY_KPDOT':'.','KEY_KPSLASH':'/','KEY_KPASTERISK':'*','KEY_KPMINUS':'-','KEY_KPPLUS':'+'})
MODIFIERS = {'KEY_LEFTSHIFT','KEY_RIGHTSHIFT','KEY_RIGHTALT','KEY_LEFTALT','KEY_LEFTCTRL','KEY_RIGHTCTRL','KEY_LEFTMETA','KEY_RIGHTMETA'}


def topic(settings):
    return settings.get('scanner_topic','') if settings.get('enabled') and settings.get('scanner_enabled') else ''


def tag_value(text, settings):
    if not isinstance(text,str) or not text or len(text.encode('utf-8'))>MAX_BYTES or any(ord(c)<32 or ord(c)==127 for c in text):
        raise ValueError('Scanner: leerer, zu langer oder nicht druckbarer Code')
    if settings.get('scanner_ha_urls',True) and text.startswith('https://www.home-assistant.io/tag/'):
        parsed=urlsplit(text)
        if parsed.netloc=='www.home-assistant.io' and not parsed.query and not parsed.fragment:
            ident=unquote(parsed.path[len('/tag/'):],errors='strict')
            if ident and all(ord(c)>=32 and ord(c)!=127 for c in ident):return ident
    return text


class Scanner:
    def __init__(self,emit,options):
        self.emit=emit;self.options=None;self.configure(options)

    def configure(self,options):
        selected=(options.get('scanner_layout','de'),options.get('scanner_terminator','enter'),
                  options.get('scanner_timeout_ms',500),options.get('scanner_enabled',False),
                  options.get('scanner_topic',''),options.get('scanner_ha_urls',True))
        if selected!=self.options:
            self.options=selected;self.modifiers=set();self.caps=False;self.reset()

    def reset(self):
        self.text='';self.bad=False;self.last=None

    def invalidate(self):
        self.text='';self.bad=True;self.modifiers.clear()

    def complete(self):
        value=self.text if not self.bad else ''
        self.reset()
        if value:self.emit('_scanner_scan','scan',value)

    def tick(self,now):
        if self.last is not None and now-self.last>=self.options[2]/1000:
            if self.options[1]=='timeout':self.complete()
            else:
                # Do not reinterpret a delayed tail as an independent valid scan.
                if self.text or self.bad:self.invalidate()
                self.last=None

    def feed(self,control,value,now):
        if not self.options[3]:return
        # Handle scan boundaries before a new character, even between poll ticks.
        self.tick(now)
        if control in MODIFIERS:
            if value==0:self.modifiers.discard(control)
            elif value==1:self.modifiers.add(control)
            return
        if value!=1:return
        self.last=now
        if control=='KEY_CAPSLOCK':self.caps=not self.caps;return
        if control=='KEY_NUMLOCK':return
        if (self.options[1]=='enter' and control in ('KEY_ENTER','KEY_KPENTER')) or (self.options[1]=='tab' and control=='KEY_TAB'):
            self.complete();return
        if control=='KEY_ESC':self.invalidate();return
        if control=='KEY_BACKSPACE':self.text=self.text[:-1];return
        if self.bad:return
        blocked=self.modifiers-{'KEY_LEFTSHIFT','KEY_RIGHTSHIFT','KEY_RIGHTALT'}
        if blocked:self.invalidate();return
        shifted=bool(self.modifiers & {'KEY_LEFTSHIFT','KEY_RIGHTSHIFT'})
        if 'KEY_RIGHTALT' in self.modifiers:
            char=ALTGR.get(control) if self.options[0]=='de' else None
        elif control in KEYPAD:char=KEYPAD[control]
        else:
            pair=(DE if self.options[0]=='de' else US).get(control)
            letter=pair and pair[0].isalpha() and pair[1]==pair[0].upper()
            char=pair[int(shifted ^ (self.caps and bool(letter)))] if pair else None
        if char is None or len((self.text+char).encode('utf-8'))>MAX_BYTES:self.invalidate();return
        self.text+=char
