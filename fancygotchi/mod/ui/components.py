import logging
import pwnagotchi
from PIL import Image, ImageDraw, ImageOps
from textwrap import TextWrapper

def text_to_rgb(text, tfont, color, width, height):
    if color == 'white' : color = (254, 254, 254, 255)
    #logging.warning(color)
    #logging.info('text length: %s; text font: %s; text: %s' % (len(text), tfont, text))
    #logging.info(str(tfont.getbbox(text)))
    w,h = tfont.getsize(text)
    nb_lines = text.count('\n') + 1
    #logging.info(nb_lines)
    h = (h + 1) * nb_lines
    if nb_lines > 1:
        lines = text.split('\n')
        max_char = 0
        tot_char = 0
        for line in lines:
            tot_char = tot_char + len(line)
            char_line = len(line)
            if char_line > max_char: max_char = char_line
        #logging.info('total: %d; max per line: %d' % (tot_char, max_char))
        #logging.info(int(w / (tot_char / max_char)))
        w = int(w / (tot_char / max_char))
        

    #logging.info(str(tfont.getsize()))
    #logging.info('width: %d; height; %d;' % (w, h))
    imgtext = Image.new('1', (int(w), int(h)), 0xff)
    dt = ImageDraw.Draw(imgtext)
    dt.text((0,0), text, font=tfont, fill=0x00)
    nonwhite_positions = [(x,y) for x in range(imgtext.size[0]) for y in range(imgtext.size[1]) if imgtext.getdata()[x+y*imgtext.size[0]] != (255,255,255)]
    #logging.info(str(nonwhite_positions))
    #if not nonwhite_positions == []:
    #    rect = (min([x for x,y in nonwhite_positions]), min([y for x,y in nonwhite_positions]), max([x for x,y in nonwhite_positions]), max([y for x,y in nonwhite_positions]))
    #    imgtext = imgtext.crop(rect)
    if color == 0: color = 'black'
    imgtext = ImageOps.colorize(imgtext.convert('L'), black = color, white = 'white')
    imgtext = imgtext.convert('RGB')
    #datas = imgtext.getdata()
    #newData = []
    #for item in datas:
    #    if item[0] == 255 and item[1] == 255 and item[2] == 255:
    #        newData.append((255, 255, 255, 0))
    #    else:
    #        newData.append(item)
    #imgtext.putdata(newData)
    return imgtext

class Widget(object):
    def __init__(self, xy, color=0):
        self.xy = xy
        self.color = color

    def draw(self, canvas, drawer):
        raise Exception("not implemented")


class Bitmap(Widget):
    def __init__(self, path, xy, color=0):
        super().__init__(xy, color)
        self.image = Image.open(path)

    def draw(self, canvas, drawer):
        canvas.paste(self.image, self.xy)


class Line(Widget):
    def __init__(self, xy, color=0, width=1):
        super().__init__(xy, color)
        self.width = width

    def draw(self, canvas, drawer):
        drawer.line(self.xy, fill=self.color, width=self.width)


class Rect(Widget):
    def draw(self, canvas, drawer):
        drawer.rectangle(self.xy, outline=self.color)


class FilledRect(Widget):
    def draw(self, canvas, drawer):
        drawer.rectangle(self.xy, fill=self.color)


#class Text(Widget):
#    def __init__(self, value="", position=(0, 0), font=None, color=0, wrap=False, max_length=0):
#        super().__init__(position, color)
#        self.value = value
#        self.font = font
#        self.wrap = wrap
#        self.max_length = max_length
#        self.wrapper = TextWrapper(width=self.max_length, replace_whitespace=False) if wrap else None
#
#    def draw(self, canvas, drawer):
#        if self.value is not None:
#            if self.wrap:
#                text = '\n'.join(self.wrapper.wrap(self.value))
#            else:
#                text = self.value
#            drawer.text(self.xy, text, font=self.font, fill=self.color)


class Text(Widget):
    def __init__(self, value="", position=(0, 0), font=None, color=0, wrap=False, max_length=0, icon=False):
        super().__init__(position, color)
        self.value = value
        self.font = font
        self.wrap = wrap
        self.max_length = max_length
        self.wrapper = TextWrapper(width=self.max_length, replace_whitespace=False) if wrap else None
        self.icon = icon
        if icon:
            self.image = Image.open(value)

    def draw(self, canvas, drawer):
        if self.value is not None:
            if not self.icon:
                if self.wrap:
                    text = '\n'.join(self.wrapper.wrap(self.value))
                else:
                    text = self.value
                width, height = canvas.size
                imgtext = text_to_rgb(text, self.font, self.color, width, height)
                #logging.info("canvas: %s" % canvas.mode)
                #logging.info("self.xy: %s" % self.xy)
                if len(self.xy) >= 3:
                    x = self.xy[0]
                    y = self.xy[1]
                else:
                    x, y = self.xy
                canvas.paste(imgtext, (x, y))
                #drawer.text(self.xy, text, self.font, font=self.font, fill=self.color)
            else:
                canvas.paste(self.image, self.xy, self.image)

class LabeledValue(Widget):
    def __init__(self, label, value="", position=(0, 0), label_font=None, text_font=None, color=0, label_spacing=9):
        th_opt = pwnagotchi._theme['theme']['options']
        label_spacing = th_opt['label_spacing']
        super().__init__(position, color)
        self.label = label
        self.value = value
        self.label_font = label_font
        self.text_font = text_font
        self.label_spacing = label_spacing

    def draw(self, canvas, drawer):
        width, height = canvas.size
        if self.label is None:
            
            imgtext = text_to_rgb(self.value, self.label_font, self.color, width, height)
            canvas.paste(imgtext, self.xy)

            #drawer.text(self.xy, self.value, font=self.label_font, fill=self.color)
        else:
            pos_label = [int(self.xy[0]), int(self.xy[1])]
            pos_value = (pos_label[0] + self.label_spacing + 5 * len(self.label), pos_label[1])
            #logging.info('%s   --   %s' % (str(pos_label), str(pos_value)))

            imgtext = text_to_rgb(self.label, self.label_font, self.color, width, height)
            canvas.paste(imgtext, pos_label)

            imgtext = text_to_rgb(self.value, self.label_font, self.color, width, height)
            canvas.paste(imgtext, pos_value)

            #drawer.text(pos, self.label, font=self.label_font, fill=self.color)
            #drawer.text((pos[0] + self.label_spacing + 5 * len(self.label), pos[1]), self.value, font=self.text_font, fill=self.color)

#class LabeledValue(Widget):
#    def __init__(self, label, value="", position=(0, 0), label_font=None, text_font=None, color=0, label_spacing=9, icon=False):
#        super().__init__(position, color)
#        self.label = label
#        self.value = value
#        self.label_font = label_font
#        self.text_font = text_font
#        self.label_spacing = label_spacing
#        self.icon = icon
#
#    def draw(self, canvas, drawer):
#        if self.label is None:
#            drawer.text(self.xy, self.value, font=self.label_font, fill=self.color)
#        elif self.icon:
#            
#        else:
#            pos = self.xy
#            drawer.text(pos, self.label, font=self.label_font, fill=self.color)
#            drawer.text((pos[0] + self.label_spacing + 5 * len(self.label), pos[1]), self.value, font=self.text_font, fill=self.color)
