import os
import pwnagotchi
import logging
from threading import Lock

from PIL import Image, ImageOps

frame_path = '/var/tmp/pwnagotchi/pwnagotchi.png'
frame_format = 'PNG'
frame_ctype = 'image/png'
frame_lock = Lock()


def update_frame(img):
    global frame_lock, frame_path, frame_format
    if not os.path.exists(os.path.dirname(frame_path)):
        os.makedirs(os.path.dirname(frame_path))
#    logging.info(pwnagotchi.config['main']['plugins']['fancygotchi']['darkmode'])
    if pwnagotchi.config['main']['plugins']['fancygotchi']['enabled']:
        filter_color = pwnagotchi.config['main']['plugins']['fancygotchi']['filter_color']
        if pwnagotchi.config['main']['plugins']['fancygotchi']['darkmode']:
            tmp_img = img.convert('L')
            img = ImageOps.invert(tmp_img)
            color_img = ImageOps.colorize(img.convert("L"), black ="black", white = filter_color)
            img = color_img
    with frame_lock:
        img.save(frame_path, format=frame_format)
