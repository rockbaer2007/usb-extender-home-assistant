"""Headless type-B multitouch gestures; no desktop and no raw-coordinate MQTT."""
import math
import copy

# Linux input-event-codes.h: EV_SYN/ABS/KEY and type-B MT slots.
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
SYN_REPORT, SYN_DROPPED = 0, 3
MT_SLOT, MT_X, MT_Y, MT_ID = 0x2f, 0x35, 0x36, 0x39
BTN_LEFT = 0x110
SLIDE_DIRECTIONS = ('UP', 'DOWN', 'LEFT', 'RIGHT', 'UP_LEFT', 'UP_RIGHT', 'DOWN_LEFT', 'DOWN_RIGHT')


def slide_value(direction, position):
    """Absolute surface position, with matching values for opposite directions."""
    x, y = position
    if direction in ('UP', 'DOWN'): return 100-y
    if direction in ('LEFT', 'RIGHT'): return x
    if direction in ('UP_RIGHT', 'DOWN_LEFT'): return round((x+100-y)/2)
    return round((x+y)/2)


def slide_direction(x,y):
    """Eight 45-degree sectors in normalized coordinates (Y grows down)."""
    sector=math.floor((math.atan2(y,x)+math.pi/8)/(math.pi/4))%8
    return ('RIGHT','DOWN_RIGHT','DOWN','DOWN_LEFT','LEFT','UP_LEFT','UP','UP_RIGHT')[sector]


class Touchpad:
    def __init__(self, emit, x_range, y_range, options=None):
        self.emit=emit;self.ranges=(x_range,y_range)
        if any(high<=low for low,high in self.ranges):raise ValueError('Ungültiger Touchpad-Koordinatenbereich')
        self.slots={};self.slot=0;self.last_emit={};self.physical=False
        self.last_slide=-100.;self.last_position=-100.;self.sent_position=None
        self.options=None;self.configure(options or {})

    def configure(self, options):
        selected={key:options.get(key,default) for key,default in
                  (('touchpad_sensitivity',5),('touchpad_rate',10),('touchpad_xy',False),('touchpad_mode','directions'))}
        selected['touchpad_slide_values'] = copy.deepcopy(options.get('touchpad_slide_values', {}))
        selected['touchpad_faders'] = copy.deepcopy(options.get('touchpad_faders', {}))
        if selected!=self.options:
            self.options=selected
            self.threshold=.20/selected['touchpad_sensitivity']
            self.interval=1/selected['touchpad_rate']
            self.pending_position=None
            self.sent_position=None
            self.pending_slide=None; self.last_value=-100.; self.sent_slide=None
            self.pending_fader=None;self.last_fader=-100.;self.sent_fader=None
            self.slots.clear()
            self.reset()

    def reset(self, preserve_position=False):
        self.started=None;self.center=None;self.span=None;self.count=0
        self.peak=0;self.travel=0;self.motion=[0.0,0.0];self.swipe=[0.0,0.0];self.mode=''
        self.clicked=self.physical
        self.value_direction=None
        self.fader=None
        if not preserve_position:self.pending_fader=None
        if not preserve_position:self.pending_slide=None
        if not preserve_position:self.pending_position=None

    def pulse(self, name, now, minimum=.04):
        control='TOUCHPAD_'+name
        if now-self.last_emit.get(control,-100)<minimum:return
        self.last_emit[control]=now
        self.emit(control,'press',1);self.emit(control,'release',0)

    def feed(self, kind, code, value, now):
        if kind==EV_SYN and code==SYN_DROPPED:
            self.slots.clear();self.reset();return
        if kind==EV_KEY and code==BTN_LEFT:
            self.physical=bool(value)
            if value:self.clicked=True;self.pending_position=None;self.pending_slide=None;self.pending_fader=None
        elif kind==EV_ABS:
            if code==MT_SLOT:
                if 0<=value<32:self.slot=value
                return
            slot=self.slots.setdefault(self.slot,{'active':False})
            if code==MT_ID:slot['active']=value>=0
            elif code in (MT_X,MT_Y):slot['x' if code==MT_X else 'y']=value
        elif kind==EV_SYN and code==SYN_REPORT:self.frame(now)

    def frame(self, now):
        points=[]
        for s in self.slots.values():
            if s['active'] and 'x' in s and 'y' in s:
                points.append(tuple((s[a]-lo)/(hi-lo) for a,(lo,hi) in zip(('x','y'),self.ranges)))
        count=len(points)
        if not count:
            if self.started is not None and not self.clicked:
                if self.peak>=3 and math.hypot(*self.swipe)>=0.15:
                    x,y=self.swipe;direction=('RIGHT' if x>0 else 'LEFT') if abs(x)>abs(y) else ('DOWN' if y>0 else 'UP')
                    self.pulse('SWIPE_'+direction+'_'+str(self.peak),now)
                elif not self.mode and self.travel<0.025 and now-self.started<=0.3:
                    self.pulse('TAP_'+str(self.peak),now)
            self.reset(preserve_position=True);return
        center=tuple(sum(p[a] for p in points)/count for a in (0,1))
        span=math.dist(points[0],points[1]) if count==2 else None
        if self.started is None:
            self.started=now
            self.pending_fader=None
            if count==1:self.fader=max(1,min(5,math.floor(center[0]*5)+1))
        self.peak=max(self.peak,count)
        if count>1:self.pending_position=None;self.pending_slide=None;self.pending_fader=None
        if self.count!=count:
            self.center=center;self.span=span;self.motion=[0.,0.];self.count=count
            return
        dx,dy=(center[a]-self.center[a] for a in (0,1));self.center=center
        self.motion[0]+=dx;self.motion[1]+=dy
        if count>=3:
            self.swipe[0]+=dx;self.swipe[1]+=dy
        self.travel+=math.hypot(dx,dy)
        if self.clicked:
            self.pending_position=None;self.pending_slide=None;self.pending_fader=None;return
        if count==1 and self.peak==1 and self.mode in ('','hold','slide'):
            distance=abs(self.motion[1]) if self.options['touchpad_mode']=='faders' else math.hypot(*self.motion)
            if distance>=self.threshold:
                self.mode='slide'
            if self.mode=='slide' and self.options['touchpad_xy']:
                self.pending_position=tuple(max(0,min(100,round(c*100))) for c in center)
            if self.mode=='slide' and self.options['touchpad_mode']=='faders':
                selected=self.options['touchpad_faders'].get(str(self.fader),{'enabled':True})
                if selected.get('enabled',True):
                    self.pending_fader=(self.fader,max(0,min(100,round((1-center[1])*100))))
            if self.mode=='slide' and self.options['touchpad_mode']=='directions':
                if math.hypot(*self.motion)>=self.threshold:
                    self.value_direction=slide_direction(*self.motion)
                direction=self.value_direction
                # A small reversal must not publish on the previous direction's topic.
                if (dx or dy) and slide_direction(dx,dy)!=direction:direction=None
                if self.options['touchpad_slide_values'].get(direction,{}).get('enabled'):
                    position=tuple(max(0,min(100,round(c*100))) for c in center)
                    self.pending_slide=(direction,slide_value(direction,position))
                else:self.pending_slide=None
        if count==2 and self.peak==2:
            ratio=span/self.span if self.span and span else 1
            if self.mode!='scroll' and abs(ratio-1)>=0.15:
                self.mode='pinch';self.pulse('PINCH_OUT' if ratio>1 else 'PINCH_IN',now);self.span=span
            elif self.mode!='pinch':
                axis=0 if abs(self.motion[0])>abs(self.motion[1]) else 1
                distance=self.motion[axis]
                if abs(distance)>=0.04:
                    self.mode='scroll'
                    self.pulse('SCROLL_'+(('RIGHT' if distance>0 else 'LEFT') if axis==0 else ('DOWN' if distance>0 else 'UP')),now)
                    self.motion=[0.,0.]
        self.tick(now)

    def tick(self, now):
        if self.pending_fader is not None and now-self.last_fader>=self.interval:
            current=self.pending_fader;self.pending_fader=None
            if current!=self.sent_fader:
                self.emit('_touchpad_fader_value','value',list(current))
                self.sent_fader=current;self.last_fader=now
        if self.pending_slide is not None and now-self.last_value>=self.interval:
            current=self.pending_slide;self.pending_slide=None
            if current!=self.sent_slide:
                self.emit('_touchpad_slide_value',current[0],current[1])
                self.sent_slide=current;self.last_value=now
        if self.count==1 and self.peak==1 and self.mode=='slide' and not self.clicked and self.options['touchpad_mode']=='directions':
            if math.hypot(*self.motion)>=self.threshold and now-self.last_slide>=self.interval:
                x,y=self.motion
                direction=slide_direction(x,y)
                self.pulse('SLIDE_'+direction,now,self.interval)
                self.last_slide=now;self.motion=[0.,0.]
        if self.pending_position is not None and now-self.last_position>=self.interval:
            position=self.pending_position;self.pending_position=None
            if position!=self.sent_position:
                self.emit('_touchpad_position','position',list(position))
                self.sent_position=position;self.last_position=now
        if self.started is not None and self.count and not self.clicked and not self.mode and self.travel<0.025 and now-self.started>=0.7:
            self.mode='hold';self.pulse('HOLD_'+str(self.peak),now)
