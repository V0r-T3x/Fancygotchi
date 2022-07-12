import logging

import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.hw.base import DisplayImpl
from PIL import ImageOps
import pwnagotchi

class Waveshare144lcd(DisplayImpl):
    def __init__(self, config):
        super(Waveshare144lcd, self).__init__(config, 'waveshare144lcd')
        self._display = None

    def layout(self):
        if pwnagotchi.config['main']['plugins']['fancygotchi']['enabled']:
            fonts.setup(10, 8, 10, 18, 25, 9)
            self._layout['width'] = 128
            self._layout['height'] = 128
            self._layout['face'] = (0, 43)
            self._layout['name'] = (0, 14)
            self._layout['channel'] = (0, 0)
            self._layout['aps'] = (0, 71)
            self._layout['uptime'] = (0, 25)
            self._layout['line1'] = [0, 12, 127, 12]
            self._layout['line2'] = [0, 116, 127, 116]
            self._layout['friend_face'] = (12, 88)
            self._layout['friend_name'] = (1, 103)
            self._layout['shakes'] = (26, 117)
            self._layout['mode'] = (0, 117)
            self._layout['status'] = {
                'pos': (65, 26),
                'font': fonts.status_font(fonts.Small),
                'max': 12
            }
        else:
            fonts.setup(10, 8, 10, 18, 25, 9)
            self._layout['width'] = 128
            self._layout['height'] = 128
            self._layout['face'] = (0, 43)
            self._layout['name'] = (0, 14)
            self._layout['channel'] = (0, 0)
            self._layout['aps'] = (0, 71)
            self._layout['uptime'] = (0, 25)
            self._layout['line1'] = [0, 12, 127, 12]
            self._layout['line2'] = [0, 116, 127, 116]
            self._layout['friend_face'] = (12, 88)
            self._layout['friend_name'] = (1, 103)
            self._layout['shakes'] = (26, 117)
            self._layout['mode'] = (0, 117)
            self._layout['status'] = {
                'pos': (65, 26),
                'font': fonts.status_font(fonts.Small),
                'max': 12
            }
        return self._layout

    def initialize(self):
        logging.info("initializing waveshare 1.44 inch lcd display")
        from pwnagotchi.ui.hw.libs.waveshare.lcdhat144.epd import EPD
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
        pass
        #self._display.clear()
