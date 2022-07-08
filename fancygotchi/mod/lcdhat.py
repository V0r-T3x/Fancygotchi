import logging

import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl
from PIL import ImageOps
import pwnagotchi


class LcdHat(DisplayImpl):
    def __init__(self, config):
        super(LcdHat, self).__init__(config, 'lcdhat')
        self._display = None

    def layout(self):
        if pwnagotchi.config['main']['plugins']['fancygotchi']['enabled']:
            logging.info('custom lcdhat position')
            logging.info(str(pwnagotchi.config['main']['plugins']['fancygotchi']['enabled']))
            #font order: bold, bold_small, medium, huge, bold_big, small
            #fonts.setup(10, 8, 10, 28, 25, 9)
            fonts.setup(14, 12, 14, 32, 29, 13)
            self._layout['width'] = 240
            self._layout['height'] = 240
            self._layout['face'] = (60, 40)
            self._layout['name'] = (0, 78)
            self._layout['channel'] = (0, 18)
            self._layout['aps'] = (35, 18)
            self._layout['uptime'] = (153, 18)
            self._layout['line1'] = [0, 33, 240, 33]
            self._layout['line2'] = [0, 150, 240, 150]
            self._layout['friend_face'] = (10, 223)
            self._layout['friend_name'] = (60, 226)
            self._layout['shakes'] = (0, 152)
            self._layout['mode'] = (100, 36)
            self._layout['status'] = {
                'pos': (10, 98),
                'font': fonts.status_font(fonts.Medium),
                'max': 20
            }
        else:
            fonts.setup(10, 9, 10, 35, 25, 9)
            self._layout['width'] = 240
            self._layout['height'] = 240
            self._layout['face'] = (0, 40)
            self._layout['name'] = (5, 20)
            self._layout['channel'] = (0, 0)
            self._layout['aps'] = (28, 0)
            self._layout['uptime'] = (175, 0)
            self._layout['line1'] = [0, 14, 240, 14]
            self._layout['line2'] = [0, 108, 240, 108]
            self._layout['friend_face'] = (0, 92)
            self._layout['friend_name'] = (40, 94)
            self._layout['shakes'] = (0, 109)
            self._layout['mode'] = (215, 109)
            self._layout['status'] = {
                'pos': (125, 20),
                'font': fonts.status_font(fonts.Medium),
                'max': 20
            }

        return self._layout

    def initialize(self):
        logging.info("initializing lcdhat display")
        #logging.info(self.config['color'])
        from pwnagotchi.ui.hw.libs.waveshare.lcdhat.epd import EPD
        self._display = EPD()
        self._display.init()
        self._display.clear()

    def render(self, canvas):
        filter_color = pwnagotchi.config['main']['plugins']['fancygotchi']['filter_color']
        if pwnagotchi.config['main']['plugins']['fancygotchi']['enabled']:
            if pwnagotchi.config['main']['plugins']['fancygotchi']['darkmode']:
                rgb_im = ImageOps.colorize(canvas.convert("L"), black = filter_color, white = "black")
            else:
                rgb_im = ImageOps.colorize(canvas.convert("L"), black = "black", white = filter_color)
        else:
            rgb_im = ImageOps.colorize(canvas.convert("L"), black = "black", white = "white")

        self._display.display(rgb_im)


    def clear(self):
        self._display.clear()
