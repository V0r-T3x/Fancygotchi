import _thread
import logging
import traceback
import random
import toml
import time
from threading import Lock

from PIL import ImageDraw, Image

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.faces as faces
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.ui.web as web
import pwnagotchi.utils as utils
from pwnagotchi.ui.components import *
from pwnagotchi.ui.state import State
from pwnagotchi.voice import Voice

WHITE = 0xff
BLACK = 0x00
ROOT = None

class View(object):
    def __init__(self, config, impl, state=None):
        global ROOT

        # setup faces from the configuration in case the user customized them
        faces.load_from_config(config['ui']['faces'])
        
        #logging.info(self._theme)
        th = pwnagotchi._theme['theme']['main_elements']
        th_ch = th['channel']
        th_aps = th['aps']
        th_up = th['uptime']
        th_face = th['face']
        th_name = th['name']
        th_status = th['status']
        th_line1 = th['line1']
        th_line2 = th['line2']
        th_fface = th['friend_face']
        th_fname = th['friend_name']
        th_sh = th['shakes']
        th_mode = th['mode']

        self._agent = None
        self._render_cbs = []
        self._config = config
        self._canvas = None
        self._canvas_l = None
        self._frozen = False
        self._lock = Lock()
        self._voice = Voice(lang=config['main']['lang'])
        self._implementation = impl
        self._layout = impl.layout()
        self._width = self._layout['width']
        self._height = self._layout['height']
        self._state = State(state={
            'channel': LabeledValue(color=th_ch['color'], label=th_ch['label'], value=th_ch['value'], position=th_ch['position'],
                                    label_font=getattr(fonts, th_ch['label_font']),
                                    text_font=getattr(fonts, th_ch['text_font'])),

            'aps': LabeledValue(color=th_aps['color'], label=th_aps['label'], value=th_aps['value'], position=th_aps['position'],
                                label_font=getattr(fonts, th_aps['label_font']),
                                text_font=getattr(fonts, th_aps['text_font'])),

            'uptime': LabeledValue(color=th_up['color'], label=th_up['label'], value=th_up['value'], position=th_up['position'],
                                   label_font=getattr(fonts, th_up['label_font']),
                                   text_font=getattr(fonts, th_up['text_font'])),

            'line1': Line(th_line1['position'], color='lime'),
            'line2': Line(th_line2['position'], color='lime'),

            'face': Text(value=faces.SLEEP, position=th_face['position'], color=th_face['color'], font=getattr(fonts, th_face['font'])),

            'friend_face': Text(value=None, position=th_fface['position'], font=getattr(fonts, th_fface['font']), color=th_fface['color']),
            'friend_name': Text(value=None, position=th_fname['position'], font=getattr(fonts, th_fname['font']),
                                color=th_fname['color']),

            'name': Text(value='%s>' % 'pwnagotchi', position=th_name['position'], color=th_name['color'], font=getattr(fonts, th_name['font'])),
            #'name': Text(value='/home/pi/plugins/fancygotchi/img/icons/name.png', position=self._layout['name'], color='lime', font=fonts.Bold, icon=True),


            'status': Text(value=self._voice.default(),
                           position=th_status['position'],
                           color=th_status['color'],
                           font=fonts.status_font(getattr(fonts, th_status['font'])),
                           wrap=th_status['wrap'],
                           # the current maximum number of characters per line, assuming each character is 6 pixels wide
                           max_length=th_status['max']),

            'shakes': LabeledValue(label=th_sh['label'], value=th_sh['value'], color=th_sh['color'],
                                   position=th_sh['position'], label_font=getattr(fonts, th_sh['label_font']),
                                   text_font=getattr(fonts, th_sh['text_font'])),

            'mode': Text(value='AUTO', position=th_mode['position'],
                         font=getattr(fonts, th_mode['font']), color=th_mode['color']),
        })

        if state:
            for key, value in state.items():
                self._state.set(key, value)

        plugins.on('ui_setup', self)

        if config['ui']['fps'] > 0.0:
            _thread.start_new_thread(self._refresh_handler, ())
            self._ignore_changes = ()
        else:
            logging.warning("ui.fps is 0, the display will only update for major changes")
            self._ignore_changes = ('uptime', 'name')

        ROOT = self
        #logging.info(ROOT)

    def set_agent(self, agent):
        self._agent = agent

    def has_element(self, key):
        self._state.has_element(key)

    def add_element(self, key, elem):
        self._state.add_element(key, elem)

    def remove_element(self, key):
        self._state.remove_element(key)

    def width(self):
        return self._width

    def height(self):
        return self._height

    def on_state_change(self, key, cb):
        self._state.add_listener(key, cb)

    def on_render(self, cb):
        if cb not in self._render_cbs:
            self._render_cbs.append(cb)

    def _refresh_handler(self):
        th_opt = pwnagotchi._theme['theme']['options']
        #delay = 1.0 / self._config['ui']['fps']
        delay = 1.0 / th_opt['fps']
        while True:
            try:
                name = self._state.get('name')
                #self.set('name', name.rstrip('█').strip() if '█' in name else (name + ' █'))
                #self.set('name', name.rstrip('❤').strip() if '❤' in name else (name + ' ❤'))
                self.set('name', name.rstrip(th_opt['cursor']).strip() if th_opt['cursor'] in name else (name + ' ' + th_opt['cursor']))
                self.update()
            except Exception as e:
                logging.warning("non fatal error while updating view: %s" % e)
                logging.warning(traceback.format_exc())
            time.sleep(delay)

    def set(self, key, value):
        self._state.set(key, value)

    def get(self, key):
        return self._state.get(key)

    def on_starting(self):
        self.set('status', self._voice.on_starting() + ("\n(v%s)" % pwnagotchi.__version__))
        self.set('face', faces.AWAKE)
        self.update()

    def on_ai_ready(self):
        self.set('mode', ' AI ')
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_ai_ready())
        self.update()

    def on_manual_mode(self, last_session):
        self.set('mode', 'MANU')
        self.set('face', faces.SAD if (last_session.epochs > 3 and last_session.handshakes == 0) else faces.HAPPY)
        self.set('status', self._voice.on_last_session_data(last_session))
        self.set('epoch', "%04d" % last_session.epochs)
        self.set('uptime', last_session.duration)
        self.set('channel', '-')
        self.set('aps', "%d" % last_session.associated)
        self.set('shakes', '%d (%s)' % (last_session.handshakes, \
                                        utils.total_unique_handshakes(self._config['bettercap']['handshakes'])))
        self.set_closest_peer(last_session.last_peer, last_session.peers)
        self.update()

    def is_normal(self):
        return self._state.get('face') not in (
            faces.INTENSE,
            faces.COOL,
            faces.BORED,
            faces.HAPPY,
            faces.EXCITED,
            faces.MOTIVATED,
            faces.DEMOTIVATED,
            faces.SMART,
            faces.SAD,
            faces.LONELY)

    def on_keys_generation(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_keys_generation())
        self.update()

    def on_normal(self):
        self.set('face', faces.AWAKE)
        self.set('status', self._voice.on_normal())
        self.update()

    def set_closest_peer(self, peer, num_total):
        if peer is None:
            self.set('friend_face', None)
            self.set('friend_name', None)
        else:
            # ref. https://www.metageek.com/training/resources/understanding-rssi-2.html
            if peer.rssi >= -67:
                num_bars = 4
            elif peer.rssi >= -70:
                num_bars = 3
            elif peer.rssi >= -80:
                num_bars = 2
            else:
                num_bars = 1

            name = '▌' * num_bars
            name += '│' * (4 - num_bars)
            name += ' %s %d (%d)' % (peer.name(), peer.pwnd_run(), peer.pwnd_total())

            if num_total > 1:
                if num_total > 9000:
                    name += ' of over 9000'
                else:
                    name += ' of %d' % num_total

            self.set('friend_face', peer.face())
            self.set('friend_name', name)
        self.update()

    def on_new_peer(self, peer):
        face = ''
        # first time they met, neutral mood
        if peer.first_encounter():
            face = random.choice((faces.AWAKE, faces.COOL))
        # a good friend, positive expression
        elif peer.is_good_friend(self._config):
            face = random.choice((faces.MOTIVATED, faces.FRIEND, faces.HAPPY))
        # normal friend, neutral-positive
        else:
            face = random.choice((faces.EXCITED, faces.HAPPY, faces.SMART))

        self.set('face', face)
        self.set('status', self._voice.on_new_peer(peer))
        self.update()
        time.sleep(3)

    def on_lost_peer(self, peer):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lost_peer(peer))
        self.update()

    def on_free_channel(self, channel):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_free_channel(channel))
        self.update()

    def on_reading_logs(self, lines_so_far=0):
        self.set('face', faces.SMART)
        self.set('status', self._voice.on_reading_logs(lines_so_far))
        self.update()

    def wait(self, secs, sleeping=True):
        was_normal = self.is_normal()
        part = secs / 10.0

        for step in range(0, 10):
            # if we weren't in a normal state before going
            # to sleep, keep that face and status on for
            # a while, otherwise the sleep animation will
            # always override any minor state change before it
            if was_normal or step > 5:
                if sleeping:
                    if secs > 1:
                        self.set('face', faces.SLEEP)
                        self.set('status', self._voice.on_napping(int(secs)))
                    else:
                        self.set('face', faces.SLEEP2)
                        self.set('status', self._voice.on_awakening())
                else:
                    self.set('status', self._voice.on_waiting(int(secs)))
                    good_mood = self._agent.in_good_mood()
                    if step % 2 == 0:
                        self.set('face', faces.LOOK_R_HAPPY if good_mood else faces.LOOK_R)
                    else:
                        self.set('face', faces.LOOK_L_HAPPY if good_mood else faces.LOOK_L)

            time.sleep(part)
            secs -= part

        self.on_normal()

    def on_shutdown(self):
        self.set('face', faces.SLEEP)
        self.set('status', self._voice.on_shutdown())
        self.update(force=True)
        self._frozen = True

    def on_bored(self):
        self.set('face', faces.BORED)
        self.set('status', self._voice.on_bored())
        self.update()

    def on_sad(self):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_sad())
        self.update()

    def on_angry(self):
        self.set('face', faces.ANGRY)
        self.set('status', self._voice.on_angry())
        self.update()

    def on_motivated(self, reward):
        self.set('face', faces.MOTIVATED)
        self.set('status', self._voice.on_motivated(reward))
        self.update()

    def on_demotivated(self, reward):
        self.set('face', faces.DEMOTIVATED)
        self.set('status', self._voice.on_demotivated(reward))
        self.update()

    def on_excited(self):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_excited())
        self.update()

    def on_assoc(self, ap):
        self.set('face', faces.INTENSE)
        self.set('status', self._voice.on_assoc(ap))
        self.update()

    def on_deauth(self, sta):
        self.set('face', faces.COOL)
        self.set('status', self._voice.on_deauth(sta))
        self.update()

    def on_miss(self, who):
        self.set('face', faces.SAD)
        self.set('status', self._voice.on_miss(who))
        self.update()

    def on_grateful(self):
        self.set('face', faces.GRATEFUL)
        self.set('status', self._voice.on_grateful())
        self.update()

    def on_lonely(self):
        self.set('face', faces.LONELY)
        self.set('status', self._voice.on_lonely())
        self.update()

    def on_handshakes(self, new_shakes):
        self.set('face', faces.HAPPY)
        self.set('status', self._voice.on_handshakes(new_shakes))
        self.update()

    def on_unread_messages(self, count, total):
        self.set('face', faces.EXCITED)
        self.set('status', self._voice.on_unread_messages(count, total))
        self.update()
        time.sleep(5.0)

    def on_uploading(self, to):
        self.set('face', random.choice((faces.UPLOAD, faces.UPLOAD1, faces.UPLOAD2)))
        self.set('status', self._voice.on_uploading(to))
        self.update(force=True)

    def on_rebooting(self):
        self.set('face', faces.BROKEN)
        self.set('status', self._voice.on_rebooting())
        self.update()

    def on_custom(self, text):
        self.set('face', faces.DEBUG)
        self.set('status', self._voice.custom(text))
        self.update()

    def update(self, force=False, new_data={}):
        th_opt = pwnagotchi._theme['theme']['options']
        for key, val in new_data.items():
            #logging.info('key: %s; val: %s' % (str(key), str(val)))
            self.set(key, val)

        with self._lock:
            if self._frozen:
                return

            state = self._state
            changes = state.changes(ignore=self._ignore_changes)
            if force or len(changes):
                self._canvas = Image.new('RGB', (self._width, self._height), 'white')
                
                drawer = ImageDraw.Draw(self._canvas)

                plugins.on('ui_update', self)
                
                copy_state = list(state.items())#way to avoid [WARNING] non fatal error while updating view: dictionary changed size during iteration
                for key, lv in copy_state:
                    lv.draw(self._canvas, drawer)

                #-------------------------------------------------------------------------
                bg = Image.open('%s/fancygotchi/img/%s' % (pwnagotchi.fancy_root, th_opt['bg_image']))

                datas = self._canvas.getdata()
                newData = []
                newData_l = []
                if th_opt['color_web']  == 'full' or th_opt['color_display'] == 'full':
                    bga = bg.convert('RGBA')
                    #logging.warning('A full color image is created')
                    for item in datas:
                        #logging.info(item)
                        if item[0] == 255 and item[1] == 255 and item[2] == 255:
                            newData.append((255, 255, 255, 0))
                        else:
                            newData.append(item) #version for color mode
                    #RGBA image for the full color 
                    rgba_im = Image.new('RGBA', (self._width, self._height), (255, 255, 255, 0))
                    rgba_im.putdata(newData)
                    bga.paste(rgba_im, (0,0), rgba_im)
                    self._canvas = bga.convert('RGB')

                if th_opt['color_web'] != 'full' or th_opt['color_display'] != 'full':
                    # convert white to transparent & switch text if not into full color
                    for item in datas:
                        #logging.info(item)
                        if item[0] == 255 and item[1] == 255 and item[2] == 255:
                            # white to transparent
                            newData_l.append((255, 255, 255, 0))
                        else:
                            if th_opt['color_text'] == 'black':
                                #logging.warning('text is black')
                                newData_l.append((0, 0, 0, 255))
                            if th_opt['color_text'] == 'white':
                                #logging.warning('text is white')
                                newData_l.append((255, 255, 255, 255))
                            if th_opt['color_text'] == 'auto':
                                #logging.warning('pale text is white and dark text is black')
                                color_sum = item[0] + item[1] + item[2]
                                if color_sum < 500:
                                    # color is dark
                                    newData.append((0, 0, 0, 255))
                                else:
                                    # color is pale
                                    newData_l.append((255, 255, 255, 255))
                    #RGBA image for the low color 
                    
                    if th_opt['color_web'] == '2' or th_opt['color_display'] == '2':
                        bga = bg.convert('RGBA')
                        #logging.warning('A 1bit image is created')
                        rgba_im_2 = Image.new('RGBA', (self._width, self._height), (255, 255, 255, 0))
                        rgba_im_2.putdata(newData_l)
                        bga.paste(rgba_im_2, (0,0), rgba_im_2)
                        self._canvas_2 = bga.convert('1')
                        
                    if th_opt['color_web'] == '3' or th_opt['color_display'] == '3':
                        bga = bg.convert('RGBA')
                        #logging.warning('A grayscale image is created')
                        rgba_im_3 = Image.new('RGBA', (self._width, self._height), (255, 255, 255, 0))
                        rgba_im_3.putdata(newData_l)
                        bga.paste(rgba_im_3, (0,0), rgba_im_3)
                        self._canvas_3 = bga.convert('L')

                if th_opt['color_web'] == 'full':
                    #logging.warning('The web UI is full color')
                    web.update_frame(self._canvas)
                elif th_opt['color_web'] == '2':
                    #logging.warning('The web UI is 1bit')
                    web.update_frame(self._canvas_2)
                elif th_opt['color_web'] == '3':
                    #logging.warning('The web UI is grayscale')
                    web.update_frame(self._canvas_3)

                if th_opt['color_display'] == 'full':
                    #logging.warning('The display is full color')
                    for cb in self._render_cbs:
                        cb(self._canvas)
                elif th_opt['color_display'] == '2':
                    #logging.warning('The display is 1bit')
                    for cb in self._render_cbs:
                        cb(self._canvas_2)
                elif th_opt['color_display'] == '3':
                    #logging.warning('The display is grayscale')
                    for cb in self._render_cbs:
                        cb(self._canvas_3)

                self._state.reset()
