"""Opt-in DragonRise 0079:0006 stick axes; buttons retain existing Linux IDs."""
import copy

PROFILE='dragonrise-0079-0006'
AXES={'left_x':(0,'Linker Stick X'),'left_y':(1,'Linker Stick Y'),
      'right_x':(3,'Rechter Stick X'),'right_y':(5,'Rechter Stick Y')}
BUTTON_NAMES={'BTN_BASE':'L1','BTN_BASE2':'R1','BTN_TOP2':'L2','BTN_PINKIE':'R2',
              'BTN_BASE5':'Linker Stick-Klick','BTN_BASE6':'Rechter Stick-Klick'}


def channels(settings):
    if not settings.get('enabled') or not settings.get('gamepad_axes_enabled') or settings.get('gamepad_profile')!=PROFILE:return {}
    return {name:(label,settings['gamepad_axes'][name]['topic']) for name,(_,label) in AXES.items()
            if settings.get('gamepad_axes',{}).get(name,{}).get('enabled',True)}


class Gamepad:
    def __init__(self,emit,ranges,options):
        self.emit=emit;self.ranges=ranges;self.options=None;self.configure(options)

    def configure(self,options):
        selected={'enabled':bool(options.get('gamepad_axes_enabled')),
            'rate':options.get('gamepad_rate',10),'axes':copy.deepcopy(options.get('gamepad_axes',{}))}
        if selected!=self.options:
            self.options=selected;self.pending={};self.sent={};self.last={}

    def feed(self,kind,code,value,now):
        if kind==0 and code==3:self.pending.clear();return
        if not self.options['enabled']:return
        name=next((name for name,(axis,_) in AXES.items() if axis==code),None) if kind==3 else None
        if name and name in self.ranges and self.options['axes'].get(name,{}).get('enabled',True):
            low,high,flat=self.ranges[name]
            if high<=low:return
            center=(low+high+1)//2
            normalized=50 if abs(value-center)<=max(0,flat) else max(0,min(100,round(100*(value-low)/(high-low))))
            self.pending[name]=normalized
        if kind==0 and code==0:self.tick(now)

    def tick(self,now):
        for name,value in list(self.pending.items()):
            if now-self.last.get(name,-100)<1/self.options['rate']:continue
            self.pending.pop(name,None)
            if self.sent.get(name)!=value:
                self.emit('_gamepad_axis',name,value);self.sent[name]=value;self.last[name]=now
