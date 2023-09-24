import _thread
import logging
import traceback
import random
import toml
import time
import os
import re
from shutil import copy

from threading import Lock

from PIL import ImageDraw, Image, ImageSequence, ImageFont
from PIL import ImageOps

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

def load_theme(config):
    pwny_path = pwnagotchi.__file__
    setattr(pwnagotchi, 'root_path', os.path.dirname(pwny_path))
    display_path = '%s/ui/hw' % (pwnagotchi.root_path)
    display_list = {}  # Dictionary to store the extracted data
    #logging.warning(display_path)
    
    # Step 1: Scan each .py file from the specified path without scanning subfolders
    for file in os.listdir(display_path):
        if file.endswith(".py"):
            file_path = os.path.join(display_path, file)
            label = None
            width = None
            height = None
            #logging.warning(file_path)
            # Step 2-4: Read and process each line in the .py file
            with open(file_path, 'r') as f:
                for line in f:
                    if 'super' in line and "'" in line:
                        #logging.warning('the super line')
                        label_match = re.search(r"'(.*?)'", line)
                        if label_match:
                            label = label_match.group(1)
                            #logging.warning(label)
                            
                    if 'width' in line and '=' in line:
                        #logging.warning('the width line')
                        width_match = re.search(r'\s*=\s*(\d+)', line)
                        if width_match:
                            width = int(width_match.group(1))
                            #logging.warning(width)
                            
                    if 'height' in line and '=' in line:
                        #logging.warning('the height line')
                        height_match = re.search(r'\s*=\s*(\d+)', line)
                        if height_match:
                            height = int(height_match.group(1))
                            #logging.warning(height)
                            
                    if label and width is not None and height is not None:
                        display_list[label] = (width, height)
                        break  # Stop processing the file if all data is found    logging.warning(display_list)
#    #logging.warning(display_list)
    
    #logging.warning(pwnagotchi.root_path)
    custom_path = config['main']['custom_plugins']
    if not custom_path == '':
        if custom_path[-1] == '/':
            custom_path = custom_path[:-1]
    if os.path.exists('%s/fancygotchi.py' % (custom_path)):
        fancy_path = custom_path
    else:
        fancy_path = '%s/plugins/default' % (pwnagotchi.root_path)
    setattr(pwnagotchi, 'fancy_path', fancy_path)
    if not config['main']['plugins']['fancygotchi']['theme'] == '':
        th_select = str(config['main']['plugins']['fancygotchi']['theme'])
    else:
        th_select = '.default'

    if config['ui']['display']['enabled']:
        display_type = config['ui']['display']['type']
    else:
        display_type = 'waveshare_2'  
    resolution = '%sx%s' % (str(display_list[display_type][0]), str(display_list[config['ui']['display']['type']][1]))


    setattr(pwnagotchi, 'res', resolution)
    th_path = '%s/fancygotchi/themes/%s/' % (fancy_path, th_select)
    #th_path_disp = '%s%s/' % (th_path, config['ui']['display']['type'])
    th_path_disp = '%s%sx%s/' % (th_path, str(display_list[display_type][0]), str(display_list[config['ui']['display']['type']][1]))
    #logging.warning(display_list[display_type][0])
    #logging.warning(display_list[display_type][1])
    #logging.warning('%s%sx%s/' % (th_path, str(display_list[display_type][0]), str(display_list[display_type][1])))
    #logging.info('%sconfig-h.toml' % (th_path_disp))
    rot = config['main']['plugins']['fancygotchi']['rotation']
    if rot == 0 or rot == 180 :
        #logging.info('%sconfig-h.toml' % (th_path_disp))
        config_ori = '%sconfig-h.toml' % (th_path_disp)
    elif rot == 90 or rot == 270:
        #logging.info('%sconfig-v.toml' % (th_path_disp))
        config_ori = '%sconfig-v.toml' % (th_path_disp)

        #logging.warning(config_ori)
    with open(config_ori, 'r') as f:
        #logging.warning('loop in theme config.toml')
        setattr(pwnagotchi, '_theme', toml.load(f))
        setattr(pwnagotchi, 'fancy_theme', th_path)
        setattr(pwnagotchi, 'fancy_theme_disp', th_path_disp)
        setattr(pwnagotchi, 'fancy_change', True)
        setattr(pwnagotchi, 'fancy_name', config['main']['name'])
        #setattr(pwnagotchi, 'fancy_orient', config['main']['plugins']['fancygotchi']['orientation'])
        #pwnagotchi._theme = toml.load(f)
        #logging.info(pwnagotchi._theme)


class View(object):
    def __init__(self, config, impl, state=None):
        global ROOT
        th = pwnagotchi._theme['theme']['main_elements']
        # setup faces from the configuration in case the user customized them
        #faces.load_from_config(config['ui']['faces'])
        faces.load_from_config(th['face']['faces'])

        th_opt = pwnagotchi._theme['theme']['options']
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
        self._layout = impl.layout()
        self._width = self._layout['width']
        self._height = self._layout['height']
        logging.warning("got here")

        size = [self._width, self._height]
        if th_opt['bg_anim_image'] != '':
            gif = Image.open('%simg/%s' % (pwnagotchi.fancy_theme, th_opt['bg_anim_image']))
            self._frames = []
            for frame in ImageSequence.Iterator(gif):
                self._frames.append(frame.convert("RGBA"))
        if th_opt['bg_image'] != '':
            self._bg = Image.open('%simg/%s' % (pwnagotchi.fancy_theme, th_opt['bg_image']))
            self._bg = self._bg.convert('RGBA')

        # verify if the foreground is animated or not (gif or png)
        # 
        if th_opt['fg_image'] != '':
            self._fg = Image.open('%simg/%s' % (pwnagotchi.fancy_theme, th_opt['fg_image']))
            self._fg = self._fg.convert('RGBA')

        self._boot = 1
        self._i = 0
        self._i2 = 0
        self._agent = None
        self._render_cbs = []
        self._config = config
        self._canvas = None
        self._canvas_a = None
        self._canvas_2 = None
        self._canvas_2a = None
        self._canvas_3 = None
        self._web = None
        self._disp = None
        self._frozen = False
        self._lock = Lock()
        self._voice = Voice(lang=config['main']['lang'])
        self._implementation = impl
        
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

            'face': Text(value=faces.SLEEP, position=th_face['position'], color=th_face['color'], font=getattr(fonts, th_face['font']), face=True),

            'friend_face': Text(value=None, position=th_fface['position'], font=getattr(fonts, th_fface['font']), color=th_fface['color']),
            'friend_name': Text(value=None, position=th_fname['position'], font=getattr(fonts, th_fname['font']),
                                color=th_fname['color']),

            'name': Text(value='%s>' % 'pwnagotchi', position=th_name['position'], color=th_name['color'], font=getattr(fonts, th_name['font'])),
            #'name': Text(value='/home/pi/plugins/fancygotchi/img/icons/name.png', position=self._layout['name'], color='lime', font=fonts.Bold),


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

        self._state.set_color('name', 'red')

    def set_agent(self, agent):
        self._agent = agent

    def has_element(self, key):
        self._state.has_element(key)

    def add_element(self, key, elem):
        self._state.add_element(key, elem)
        pwnagotchi.fancy_change = True

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
        delay = 1.0 / self._config['ui']['fps']
        #delay = 1.0 / th_opt['fps']
        while True:
            try:
                name = self._state.get('name')
                #self.set('name', name.rstrip('█').strip() if '█' in name else (name + ' █'))
                #self.set('name', name.rstrip('❤').strip() if '❤' in name else (name + ' ❤'))
                if hasattr(pwnagotchi, 'fancy_cursor'):
                    if th_opt['cursor'] in name:
                        name = pwnagotchi.fancy_name + '>' + pwnagotchi.fancy_cursor
                        th_opt['cursor'] = pwnagotchi.fancy_cursor
                self.set('name', name.rstrip(th_opt['cursor']).strip() if th_opt['cursor'] in name else (name + th_opt['cursor']))


                for val in self._state.items():
                    if len(self._state.get_attr(val[0], 'colors')) != 0:
                        
                        i = self._state.get_attr(val[0], 'icolor')

                        color_list = self._state.get_attr(val[0], 'colors')
                        self._state.set_attr(val[0], 'color', color_list[i])
                        i += 1
                        if i > len(color_list)-1:
                            self._state.set_attr(val[0], 'icolor', 0)
                        else:
                            self._state.set_attr(val[0], 'icolor', i)

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
        th_opt = pwnagotchi._theme['theme']['options']
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

            # adding the 
            name = th_opt['friend_bars'] * num_bars
            name += th_opt['friend_no_bars'] * (4 - num_bars)
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

    def fancy_change(self, partial=False, fancy_dict=[]):
        #-------------------------------------------------------------------------
        # OTG theme changer
        # checked in theory-linking status font OTG
        # checked-linking offset OTG
        #
        # checked-linking the css to the OTG
        # checked- adjusting all the default theme config files
        # checked- making a symlink of the img folder from the theme instead of the fancygotchi plugin folder
        # verifying the selected theme in the pwny config.toml
        #-------------------------------------------------------------------------
        global Bold, BoldSmall, Medium, Huge, BoldBig, Small, FONT_NAME
        rot = self._config['main']['plugins']['fancygotchi']['rotation']
        th_opt = pwnagotchi._theme['theme']['options']
        actual_th = self._config['main']['plugins']['fancygotchi']['theme']

        if not partial:

            # loading pwnagotchi config.toml
            with open('/etc/pwnagotchi/config.toml', 'r') as f:
                f_toml = toml.load(f)
                self._config['main']['plugins']['fancygotchi']['rotation'] = f_toml['main']['plugins']['fancygotchi']['rotation']
            rot = self._config['main']['plugins']['fancygotchi']['rotation']

            self._config['main']['plugins']['fancygotchi']['theme'] = f_toml['main']['plugins']['fancygotchi']['theme']
            actual_th = self._config['main']['plugins']['fancygotchi']['theme']
            if not pwnagotchi.config['main']['plugins']['fancygotchi']['theme'] == '':
                th_select = actual_th
            else:
                th_select = '.default'
            th_path = '%s/fancygotchi/themes/%s/' % (pwnagotchi.fancy_root, th_select)
            th_path_disp = '%s%s/' % (th_path, pwnagotchi.res)
            setattr(pwnagotchi, 'fancy_theme', th_path)
            setattr(pwnagotchi, 'fancy_theme_disp', th_path_disp)

            if actual_th != f_toml['main']['plugins']['fancygotchi']['theme']:
                logging.info('[FANCYGOTCHI] Theme changed... Loading new theme')

            if rot == 0 or rot == 180:
                #logging.info('[FANCYGOTCHI] theme file: %sconfig-h.toml' % (pwnagotchi.fancy_theme_disp))
                config_ori = '%sconfig-h.toml' % (pwnagotchi.fancy_theme_disp)
            if rot == 90 or rot == 270:
                #logging.info('[FANCYGOTCHI] theme file: %sconfig-v.toml' % (pwnagotchi.fancy_theme_disp))
                config_ori = '%sconfig-v.toml' % (pwnagotchi.fancy_theme_disp)
            
            # loading theme config
            with open(config_ori, 'r') as f:
                f_toml = toml.load(f)
                while pwnagotchi._theme != f_toml:
                    setattr(pwnagotchi, '_theme', f_toml)

            # copying the style.css of the selected theme
            src_css = '%sstyle.css' % (th_path)
            dst_css = '%s/web/static/css/style.css' % (os.path.dirname(os.path.realpath(__file__)))
            #logging.info('[FANCYGOTCHI] linking theme css: '+src_css +' ~~mod~~> '+ dst_css)
            copy(src_css, dst_css)

            # changing the symlink for the img folder of the slected theme
            src_img = '%simg' % (th_path)
            dst_img = '%s/web/static' % (os.path.dirname(os.path.realpath(__file__)))
            #logging.info('[FANCYGOTCHI] linking theme image folder: '+src_img +' ~~mod~~> '+ dst_img)
            # removing old link
            os.system('rm %s/img' % (dst_img))
            # creating new link
            os.system('ln -s %s %s' % (src_img, dst_img))
            
        else:
            logging.info('[FANCYGOTCHI] partial theme refresh: %s' % (fancy_dict))

        th_opt = pwnagotchi._theme["theme"]["options"]
        if th_opt['bg_anim_image'] != '':
            self._i = 0
            gif = Image.open('%simg/%s' % (pwnagotchi.fancy_theme, th_opt['bg_anim_image']))
            self._frames = []
            for frame in ImageSequence.Iterator(gif):
                self._frames.append(frame.convert("RGBA"))

        size = [self._width, self._height]

        if th_opt['bg_image'] != '':
            bg_img = Image.open('%simg/%s' % (pwnagotchi.fancy_theme, th_opt['bg_image']))
            self._bg = bg_img
            self._bg = self._bg.convert('RGBA')
        else:
             self._bg = Image.new('RGBA', size, (0, 0, 0, 0))
        if th_opt['fg_image'] != '':
            self._fg = Image.open('%simg/%s' % (pwnagotchi.fancy_theme, th_opt['fg_image']))
            self._fg = self._fg.convert('RGBA')
        #setattr(pwnagotchi, 'fps', th_opt['fps'])
        setattr(pwnagotchi, 'fancy_cursor', th_opt['cursor'])
        th_opt['cursor'] = th_opt['cursor']
        setattr(pwnagotchi, 'fancy_font', th_opt['cursor'])
        fonts.STATUS_FONT_NAME = th_opt['status_font']
        fonts.SIZE_OFFSET = th_opt['size_offset']
        fonts.FONT_NAME = th_opt['font']

        ft = th_opt['font_sizes']
        fonts.setup(ft[0], ft[1], ft[2], ft[3], ft[4], ft[5])
        
        main_elements = pwnagotchi._theme["theme"]["main_elements"]
        plugin_elements = pwnagotchi._theme["theme"]["plugin_elements"]
        components = main_elements.copy()
        components.update(plugin_elements)
        for element, values in components.items():
            for key, value in values.items():
                if element == 'status':
                    s = True
                else:
                    s = False
                if key == 'position':
                    self._state.set_attr(element,'xy', value)
                elif key == 'label':
                    self._state.set_attr(element, key, value)
                elif key == 'label_spacing':
                    self._state.set_attr(element, key, value)
                elif key == 'label_line_spacing':
                    self._state.set_attr(element, key, value)
                elif key == 'font':
                    if value == 'Small': 
                        if not s:
                            self._state.set_font(element, fonts.Small)
                        else:
                            self._state.set_font(element, fonts.status_font(fonts.Small))
                    elif value == 'Medium': 
                        if not s:
                            self._state.set_font(element, fonts.Medium)
                        else:
                            self._state.set_font(element, fonts.status_font(fonts.Medium))
                    elif value == 'BoldSmall':
                        if not s:
                            self._state.set_font(element, fonts.BoldSmall)
                        else:
                            self._state.set_font(element, fonts.status_font(fonts.BoldSmall))
                    elif value == 'Bold':
                        if not s:
                            self._state.set_font(element, fonts.Bold)
                        else:
                            self._state.set_font(element, fonts.status_font(fonts.Bold))
                    elif value == 'BoldBig':
                        if not s:
                            self._state.set_font(element, fonts.BoldBig)
                        else:
                            self._state.set_font(element, fonts.status_font(fonts.BoldBig))
                    elif value == 'Huge':
                        if not s:
                            self._state.set_font(element, fonts.Huge)
                        else:
                            self._state.set_font(element, fonts.status_font(fonts.Huge))
                elif key == 'text_font':
                    if value == 'Small': self._state.set_textfont(element, fonts.Small)
                    elif value == 'Medium': self._state.set_textfont(element, fonts.Medium)
                    elif value == 'BoldSmall': self._state.set_textfont(element, fonts.BoldSmall)
                    elif value == 'Bold': self._state.set_textfont(element, fonts.Bold)
                    elif value == 'BoldBig': self._state.set_textfont(element, fonts.BoldBig)
                    elif value == 'Huge': self._state.set_textfont(element, fonts.Huge)
                elif key == 'label_font':
                    if value == 'Small': self._state.set_labelfont(element, fonts.Small)
                    elif value == 'Medium': self._state.set_labelfont(element, fonts.Medium)
                    elif value == 'BoldSmall': self._state.set_labelfont(element, fonts.BoldSmall)
                    elif value == 'Bold': self._state.set_labelfont(element, fonts.Bold)
                    elif value == 'BoldBig': self._state.set_labelfont(element, fonts.BoldBig)
                    elif value == 'Huge': self._state.set_labelfont(element, fonts.Huge)
                elif key == 'color':
                    self._state.set_attr(element, key, value)
                    self._state.set_attr(element, '%ss' % key, [])
                elif key == 'colors':
                    self._state.set_attr(element, key, [])
                    if len(value) != 0:
                        #logging.warning('more than one color')
                        color_list = [self._state.get_attr(element, 'color')]
                        color_list.extend(value)
                        #logging.warning(color_list)
                        self._state.set_attr(element, key, color_list)
                    else:
                        self._state.set_attr(element, key, [])
                elif key == 'icon':
                    self._state.set_attr(element, key, value)
                    for ckey, cvalue in components[element].items():
                        if not element == 'face':
                            if value:
                                for val in self._state.items():
                                    if val[0] == element:
                                        if isinstance(val[1], pwnagotchi.ui.components.LabeledValue):
                                            #logging.warning(element+' is a labeled value')
                                            type = self._state.get_attr(element, 'label')
                                            t = 'label'
                                        elif isinstance(val[1], pwnagotchi.ui.components.Text):
                                            #if not 'face' in components[element].items():
                                            #logging.warning(element+' is a text')
                                            type = self._state.get_attr(element, 'value')
                                            t = 'value'
                                if not components[element]['f_awesome']:
                                    #if not 'face' in components[element].items():
                                    icon_path = '%simg/%s' % (pwnagotchi.fancy_theme, type)
                                    ##self._state.image = Image.open(icon_path)
                                    zoom = 1
                                    for ckey, cvalue in components[element].items():
                                        if ckey == 'zoom':
                                            zoom = cvalue
                                            if not th_opt['main_text_color'] == '':
                                                mask = True
                                            else:
                                                mask = False
                                    self._state.set_attr(element, 'image',  adjust_image(icon_path, zoom, mask))#Image.open(icon_path))
                                    if th_opt['main_text_color'] != '':
                                        self.image.convert('1')
                                else:
                                    #logging.warning(t)
                                    fa = ImageFont.truetype('font-awesome-solid.otf', components[element]['f_awesome_size'])
                                    code_point = int(components[element][t], 16)
                                    icon = chr(code_point)
                                    w,h = fa.getsize(icon)
                                    icon_img = Image.new('1', (int(w), int(h)), 0xff)
                                    dt = ImageDraw.Draw(icon_img)
                                    dt.text((0,0), icon, font=fa, fill=0x00)
                                    icon_img = icon_img.convert('RGBA')
                                    self._state.set_attr(element, 'image', icon_img)
                elif key == 'f_awesome':
                    self._state.set_attr(element, key, value)
                elif key == 'f_awesome_size':
                    self._state.set_attr(element, key, value)
                elif key == 'faces':
                    for ckey, cvalue in components[element].items():
                        if ckey == 'icon':
                            isiconic = cvalue
                    if isiconic:
                        for ckey, cvalue in components[element].items():
                            if ckey == 'faces':
                                th_faces = cvalue
                            if ckey == 'image_type':
                                th_img_t = cvalue
                        faces.load_from_config(value)
                        mapping = {}
                        for face_name, face_value in th_faces.items():
                            icon_path = '%simg/%s.%s' % (pwnagotchi.fancy_theme, face_name, th_img_t)
                            icon_broken = '%simg/%s.%s' % (pwnagotchi.fancy_theme, 'broken', th_img_t)
                            zoom = 1
                            for ckey, cvalue in components[element].items():
                                mask = False
                                if ckey == 'zoom':
                                    zoom = cvalue
                                    if not th_opt['main_text_color'] == '':
                                        mask = True
                                    else:
                                        mask = False
                            if os.path.isfile(icon_path):
                                face_image = adjust_image(icon_path, zoom, mask)#Image.open(icon_path)
                            else:
                                #logging.warning('[FANCYGOTCHI] missing the %s image' % (face_name))
                                face_image = adjust_image(icon_broken, zoom, mask)#Image.open(icon_path)
                            #self.mapping = {face_value: face_image}
                            mapping[face_value] = face_image
                        self._state.set_attr(element, 'mapping', mapping)

        time.sleep(1)

    def update(self, force=False, new_data={}):
        th_opt = pwnagotchi._theme['theme']['options']
        rot = self._config['main']['plugins']['fancygotchi']['rotation']

        for key, val in new_data.items():
            #logging.info('key: %s; val: %s' % (str(key), str(val)))
            self.set(key, val)

        with self._lock:
            if self._frozen:
                return

            state = self._state
            changes = state.changes(ignore=self._ignore_changes)
            if force or len(changes):
                if rot == 0 or rot == 180:
                    size = [self._width, self._height]
                    if th_opt['main_text_color'] == '':
                        self._canvas = Image.new('RGB', size, 'white')
                    else:
                        self._canvas = Image.new('1', size, 'white')
                elif rot == 90 or rot == 270:
                    size = [self._height, self._width] 
                    if th_opt['main_text_color'] == '':
                        self._canvas = Image.new('RGB', size, 'white')
                    else:
                        self._canvas = Image.new('1', size, 'white')

                #drawer = ImageDraw.Draw(self._canvas)
                drawer = ImageDraw.Draw(self._canvas)

                plugins.on('ui_update', self)

                #pwnagotchi.fancy_change = True
                if pwnagotchi.fancy_change == True:
                    self.fancy_change()
                    if self._boot == 0:
                        pwnagotchi.fancy_change = False
                    else:
                        self._boot = 0

                    
                copy_state = list(state.items())#way to avoid [WARNING] non fatal error while updating view: dictionary changed size during iteration
                for key, lv in copy_state:
                    lv.draw(self._canvas, drawer)

                #-------------------------------------------------------------------------
                # checked- Adding a foreground image option to hide the screen
                #
                # adding option for icons, icon (monochrome) or sprite
                #-------------------------------------------------------------------------

                if th_opt['main_text_color'] != '':
                    #imgtext = ImageOps.colorize(imgtext.convert('L'), black = color, white = 'white')
                    color = th_opt['main_text_color']
                    if color == 'white' : color = (254, 254, 254, 255)
                    if color != 'black':
                        self._canvas = ImageOps.colorize(self._canvas.convert('L'), black = color, white = 'white')
                    self._canvas = self._canvas.convert('RGB')


                self._canvas = self._canvas.convert('RGB')
                datas = self._canvas.getdata()
                newData_web = []
                newData_disp = []
                self._web = None
                self._disp = None
                iweb = None
                idisp = None
                # if not stealth mode enabled...*********************************************************
                if not th_opt['stealth_mode']:
                    # option colorized background
                    if th_opt['bg_color'] != '':
                        iweb = Image.new('RGBA', size, th_opt['bg_color'])
                        if th_opt['color_web']  == '2':
                            iweb = iweb.convert('RGBA')
                        elif th_opt['color_web'] != '2':
                            iweb = iweb.convert('RGBA')

                        idisp = Image.new('RGBA', size, th_opt['bg_color'])
                        if th_opt['color_display']  == '2':
                            idisp = idisp.convert('RGBA')
                        elif th_opt['color_display'] != '2':
                            idisp = idisp.convert('RGBA')
                            
                    
                    # option for animated background
                    if th_opt['bg_anim_image'] !='':
                        #logging.warning(str(self._i) +'/'+str(len(self._frames)))
                        if th_opt['anim_web']:
                            if isinstance(iweb, Image.Image):
                                temp_iweb = iweb.copy()
                                temp_iweb.paste(self._frames[self._i].convert('RGBA'))
                                iweb = temp_iweb
                            else: 
                                iweb = self._frames[self._i].convert('RGBA')
                        else:
                            if isinstance(iweb, Image.Image):
                                temp_iweb = iweb.copy()
                                temp_iweb.paste(self._frames[0].convert('RGBA'))
                                iweb = temp_iweb
                            else: 
                                iweb = self._frames[0].convert('RGBA')
                        if th_opt['anim_display']:
                            if isinstance(idisp, Image.Image):
                                temp_idisp = idisp.copy()
                                temp_idisp.paste(self._frames[self._i].convert('RGBA'))
                                idisp = temp_idisp
                            else: 
                                idisp = self._frames[self._i].convert('RGBA')
                        else:
                            if isinstance(idisp, Image.Image):
                                temp_idisp = idisp.copy()
                                temp_idisp.paste(self._frames[0].convert('RGBA'))
                                idisp = temp_idisp
                            else: 
                                idisp = self._frames[0].convert('RGBA')
                        if self._i >= len(self._frames)-1:
                            self._i = 0
                    
                    # option for background image
                    if th_opt['bg_image'] !='':
                        if isinstance(iweb, Image.Image):
                            temp_iweb = iweb.copy()
                            temp_iweb.paste(self._bg, (0,0), self._bg)
                            iweb = temp_iweb
                        else: 
                            iweb = self._bg.copy()
                        if isinstance(idisp, Image.Image): 
                            temp_idisp = idisp.copy()
                            temp_idisp.paste(self._bg, (0,0), self._bg)
                            idisp = temp_idisp
                        else: 
                            idisp = self._bg.copy()
                    

                    #------------------------------------------------------------------------------------------
                    for item in datas:

                        if item[0] == 255 and item[1] == 255 and item[2] == 255:
                            # white to transparent
                            newData_web.append((255, 255, 255, 0))
                            newData_disp.append((255, 255, 255, 0))

                        else:
                            if th_opt['color_web']  == '2':
                                if th_opt['color_text'] == 'white':
                                    newData_web.append((255, 255, 255, 255))
                                elif th_opt['color_text'] == 'black':
                                    newData_web.append((0, 0, 0, 255))
                                elif th_opt['color_text'] == 'auto':
                                    color_sum = item[0] + item[1] + item[2]
                                    if color_sum < 500:
                                        # color is dark
                                        newData_web.append((0, 0, 0, 255))
                                    else:
                                        # color is pale
                                        newData_web.append((255, 255, 255, 255))
                            else:
                                newData_web.append(item) #version for color mode
                            if th_opt['color_display']  == '2':
                                if th_opt['color_text'] == 'white':
                                    newData_disp.append((255, 255, 255, 255))
                                elif th_opt['color_text'] == 'black':
                                    newData_disp.append((0, 0, 0, 255))
                                elif th_opt['color_text'] == 'auto':
                                    color_sum = item[0] + item[1] + item[2]
                                    if color_sum < 500:
                                        # color is dark
                                        newData_disp.append((0, 0, 0, 255))
                                    else:
                                        # color is pale
                                        newData_disp.append((255, 255, 255, 255))
                            else:
                                newData_disp.append(item) #version for color mode

                    #------------------------------------------------------------------------------------------

                    # maybe adding an option to make certain components
                    # under the foreground layer and other above it for
                    # a stelth mode
                    #
                    # adding the canvas layer
                    
                    if isinstance(iweb, Image.Image):
                        temp_data_iweb = Image.new('RGBA', size, (255, 255, 255, 0))
                        temp_data_iweb.putdata(newData_web)
                        iweb.paste(temp_data_iweb, (0,0), temp_data_iweb)

                    else:
                        temp_data_iweb = Image.new('RGBA', size, (255, 255, 255, 0))
                        temp_data_iweb.putdata(newData_web)
                        iweb = temp_data_iweb
                        
                    if isinstance(idisp, Image.Image):
                        temp_data_idisp = Image.new('RGBA', size, (255, 255, 255, 0))
                        temp_data_idisp.putdata(newData_disp)
                        idisp.paste(temp_data_idisp, (0,0), temp_data_idisp)

                    else:
                        temp_data_idisp = Image.new('RGBA', size, (255, 255, 255, 0))
                        temp_data_idisp.putdata(newData_disp)
                        idisp = temp_data_idisp
                    
                # end of the not stealth mode **************************************************************

                    #if stealth mode, don't activate it on the web UI
                    if th_opt['fg_image'] != '':
                        if isinstance(iweb, Image.Image):
                            temp_iweb = iweb.copy()
                            temp_iweb.paste(self._fg, (0,0), self._fg)
                            iweb = temp_iweb
                        else:
                            iweb = self._fg
                        if isinstance(idisp, Image.Image):
                            temp_idisp = idisp.copy()
                            temp_idisp.paste(self._fg, (0,0), self._fg)
                            idisp = temp_idisp
                        else:
                            idisp = self._fg
                else:
                    logging.info('[FANCYGOTCHI] stealth Mode')
                
                if th_opt['color_web']  == '2':
                    self._web = iweb.convert('1')
                else:
                    self._web = iweb.convert('RGB')
                if th_opt['color_display']  == '2':
                    self._disp = idisp.convert('1')
                else:
                    self._disp = idisp.convert('RGB')
                
                if rot == 0 or rot == 180:
                    img = self._disp
                if rot == 90 or rot == 270:
                    img = self._disp.rotate(90, expand=True)

                if rot == 180 or rot == 270:
                    img = img.rotate(180)
                for cb in self._render_cbs:
                    cb(img)

                web.update_frame(self._web)

                if hasattr(self, '_frames') and (th_opt['anim_web'] or th_opt['anim_display']):
                    self._i += 1

                self._state.reset()
