from PIL import ImageFont
import pwnagotchi
import logging

#th_opt = pwnagotchi._theme['theme']['options']

# should not be changed
FONT_NAME = 'DejaVuSansMono'

# can be changed
STATUS_FONT_NAME = None
SIZE_OFFSET = 0

Bold = None
BoldSmall = None
BoldBig = None
Medium = None
Small = None
Huge = None

def init(config):
    th_fsize = pwnagotchi._theme['theme']['options']['font_sizes']
    #logging.info(th_opt['font_sizes'])
    global STATUS_FONT_NAME, SIZE_OFFSET
    STATUS_FONT_NAME = config['ui']['font']['name']
    SIZE_OFFSET = config['ui']['font']['size_offset']
    setup(th_fsize[0], th_fsize[1], th_fsize[2], th_fsize[3], th_fsize[4], th_fsize[5])
    #setup(th_opt[''][0], th_font_sizes[1], th_font_sizes[2], th_font_sizes[3], th_font_sizes[4], th_font_sizes[5])


def status_font(old_font):
    global STATUS_FONT_NAME, SIZE_OFFSET
    return ImageFont.truetype(STATUS_FONT_NAME, size=old_font.size + SIZE_OFFSET)


def setup(bold, bold_small, medium, huge, bold_big, small):
    global Bold, BoldSmall, Medium, Huge, BoldBig, Small, FONT_NAME

    Small = ImageFont.truetype(FONT_NAME, small)
    Medium = ImageFont.truetype(FONT_NAME, medium)
    BoldSmall = ImageFont.truetype("%s-Bold" % FONT_NAME, bold_small)
    Bold = ImageFont.truetype("%s-Bold" % FONT_NAME, bold)
    BoldBig = ImageFont.truetype("%s-Bold" % FONT_NAME, bold_big)
    Huge = ImageFont.truetype("%s-Bold" % FONT_NAME, huge)
