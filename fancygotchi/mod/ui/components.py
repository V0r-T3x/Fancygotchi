import logging
import pwnagotchi
from PIL import Image, ImageDraw, ImageOps, ImageFont
from textwrap import TextWrapper
import pwnagotchi.ui.fonts as fonts
import pwnagotchi.ui.view as view
import sys
import os
#import fontawesome as fa

def text_to_rgb(text, tfont, color, width, height):
    th_opt = pwnagotchi._theme['theme']['options']
    if color == 'white' : color = (254, 254, 254, 255)
    w,h = tfont.getsize(text)
    nb_lines = text.count('\n') + 1
    h = (h + 1) * nb_lines
    if nb_lines > 1:
        lines = text.split('\n')
        max_char = 0
        tot_char = 0
        for line in lines:
            tot_char = tot_char + len(line)
            char_line = len(line)
            if char_line > max_char: max_char = char_line
        w = int(w / (tot_char / max_char))
    imgtext = Image.new('1', (int(w), int(h)), 0xff)
    dt = ImageDraw.Draw(imgtext)
    dt.text((0,0), text, font=tfont, fill=0x00)
    if color == 0: color = 'black'
    imgtext = ImageOps.colorize(imgtext.convert('L'), black = color, white = 'white')
    imgtext = imgtext.convert('RGB')

    return imgtext

def adjust_image(image_path, zoom, mask=False):
    try:
        # Open the image
        image = Image.open(image_path)
        image = image.convert('RGBA') 
        #image.save('/home/pi/original.png')
        # Get the original width and height
        original_width, original_height = image.size
        # Calculate the new dimensions based on the zoom factor
        new_width = int(original_width * zoom)
        new_height = int(original_height * zoom)
        # Resize the image while maintaining the aspect ratio
        adjusted_image = image.resize((new_width, new_height))#, Image.ANTIALIAS)

        #adjusted_image.save('/home/pi/middle.png')

        if mask:
            image = adjusted_image.convert('RGBA') 
            width, height = image.size
            pixels = image.getdata()
            new_pixels = []
            for pixel in pixels:
                r, g, b, a = pixel
                
                # If pixel is not fully transparent (alpha is not 0), convert it to black
                #if a > 50:
                if a > 150:
                    new_pixel = (0, 0, 0, 255)
                else:
                    new_pixel = (0, 0, 0, 0)
                
                new_pixels.append(new_pixel)

            # Create a new image with the modified pixel data
            new_img = Image.new("RGBA", image.size)
            new_img.putdata(new_pixels)
            #for x in range(width):
            #    for y in range(height):
            #        r, g, b, a = image.getpixel((x, y))
            #        # Convert non-alpha pixels to black
            #        if a < 255:
            #            image.putpixel((x, y), (0, 0, 0, 255))
            #new_img.save('/home/pi/mask.png')
            adjusted_image = new_img


        # Return the resized image
        return adjusted_image

    except Exception as e:
        logging.warning("Error:", str(e))
        return None

class Widget(object):
    def __init__(self, xy, color=0):
        self.xy = xy
        self.color = color
        self.icolor = 0
        self.colors = []

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
    def __init__(self, value="", position=(0, 0), font=None, color=0, wrap=False, max_length=0, icon=False, f_awesome=False, f_awesome_size=0, face=False, zoom=1):
        super().__init__(position, color)
        th_opt = pwnagotchi._theme['theme']['options']
        self.value = value
        self.font = font
        self.wrap = wrap
        self.max_length = max_length
        self.wrapper = TextWrapper(width=self.max_length, replace_whitespace=False) if wrap else None
        self.icon = icon
        self.image = None
        self.f_awesome = f_awesome
        self.f_awesome_size = f_awesome_size
        self.face = face
        self.zoom = zoom
        th = pwnagotchi._theme['theme']['main_elements']
        self.mapping = {}
        th_faces = th['face']['faces']
        th_img_t = th['face']['image_type']

        # If one image is 1bit color mask or 1bit convertion create a second mapping

        if not th_opt['main_text_color'] == '':
            self.mask = True
        else:
            self.mask = False
        if th['face']['icon']:
            for face_name, face_value in th_faces.items():
                icon_path = '%simg/%s.%s' % (pwnagotchi.fancy_theme, face_name, th_img_t)
                icon_broken = '%simg/%s.%s' % (pwnagotchi.fancy_theme, 'broken', th_img_t)
                #logging.warning(icon_path)
                if os.path.isfile(icon_path):
                    face_image = adjust_image(icon_path, self.zoom, self.mask)#Image.open(icon_path)

                else:
                    logging.warning('Missing the %s.%s image' % (face_name, th_img_t))
                    face_image = adjust_image(icon_broken, self.zoom, self.mask)#Image.open(icon_broken)
                #face_image.save('/home/pi/%s.png' % (face_name))
                #logging.warning('/home/pi/%s.png' % (face_name))
                self.mapping[face_value] = face_image

        if self.icon:
            if not self.f_awesome:
                icon_path = '%simg/%s' % (pwnagotchi.fancy_theme, value)
                self.image =  adjust_image(icon_path, self.zoom, self.mask)#Image.open(icon_path)

                if th_opt['main_text_color'] != '':
                    self.image.convert('1')
            else:
                fa = ImageFont.truetype('font-awesome-solid.otf', self.f_awesome_size)
                code_point = int(self.value, 16)
                icon = code_point
                w,h = fa.getsize(icon)
                icon_img = Image.new('1', (int(w), int(h)), 0xff)
                dt = ImageDraw.Draw(icon_img)
                dt.text((0,0), icon, font=fa, fill=0x00)
                icon_img = icon_img.convert('RGBA')
                self.image = icon_img
        
    def get_font(self):
        return self.font

    def draw(self, canvas, drawer):
        th_opt = pwnagotchi._theme['theme']['options']
        if self.value is not None:
            if not self.icon:
                if self.wrap:
                    text = '\n'.join(self.wrapper.wrap(self.value))
                else:
                    text = self.value
                text = str(text)
                width, height = canvas.size
                if th_opt['main_text_color'] == '':
                    imgtext = text_to_rgb(text, self.font, self.color, width, height)

                    #logging.info("canvas: %s" % canvas.mode)
                    #logging.info("self.xy: %s" % self.xy)
                    if len(self.xy) >= 3:
                        x = self.xy[0]
                        y = self.xy[1]
                    else:
                        x, y = self.xy
                    canvas.paste(imgtext, (int(x), int(y)))
                else:
                    drawer.text(self.xy, text, font=self.font, fill=0x00)
                    #drawer.text(self.xy, text, self.font, font=self.font, fill=self.color)
            else:
                if not self.f_awesome:
                    if not self.face:
                        canvas.paste(self.image, self.xy, self.image)
                    else:
                        img = self.mapping[self.value]
                        #img.save('/home/pi/actual.png')
                        canvas.paste(img, self.xy, img)
                        #canvas.paste(self.image, self.xy, self.image)
                else:
                    if self.color == 'white' : self.color = (254, 254, 254, 255)
                    if th_opt['main_text_color'] == '':
                        icon_img = ImageOps.colorize(self.image.convert('L'), black = self.color, white = 'white')
                        icon_img = icon_img.convert('RGBA')
                        canvas.paste(icon_img, self.xy, icon_img)
                    else:
                        canvas.paste(self.image, pos_label, self.image)



class LabeledValue(Widget):
    def __init__(self, label, value="", position=(0, 0), label_font=None, text_font=None, color=0, label_spacing=9, icon=False, label_line_spacing=0, f_awesome=False, f_awesome_size=0, zoom=1):
        th_opt = pwnagotchi._theme['theme']['options']
        label_spacing = th_opt['label_spacing']
        super().__init__(position, color)
        self.label = label
        self.value = value
        self.label_font = label_font
        self.text_font = text_font
        self.label_spacing = label_spacing
        self.label_line_spacing = label_line_spacing
        self.icon = icon
        self.image = None
        self.zoom = zoom
        self.f_awesome = f_awesome
        self.f_awesome_size = f_awesome_size
        if not th_opt['main_text_color'] == '':
            self.mask = True
        else:
            self.mask = False
        if icon:
            if not self.f_awesome:
                icon_path = '%simg/%s' % (pwnagotchi.fancy_theme, label)
                self.image =  adjust_image(icon_path, self.zoom, self.mask)#Image.open(icon_path)
                if th_opt['main_text_color'] != '':
                    self.image.convert('1')
            else:
                fa = ImageFont.truetype('font-awesome-solid.otf', self.f_awesome_size)
                code_point = int(self.label, 16)
                icon = code_point
                w,h = fa.getsize(icon)
                icon_img = Image.new('1', (int(w), int(h)), 0xff)
                dt = ImageDraw.Draw(icon_img)
                dt.text((0,0), icon, font=fa, fill=0x00)
                icon_img = icon_img.convert('RGBA')
                self.image = icon_img

        
            

    def draw(self, canvas, drawer):
        th_opt = pwnagotchi._theme['theme']['options']
        width, height = canvas.size
        pos_label = [int(self.xy[0]), int(self.xy[1]) + self.label_line_spacing]
        pos_value = (pos_label[0] + self.label_spacing + 5 * len(self.label), pos_label[1] - self.label_line_spacing)
        if self.label is None:
            if th_opt['main_text_color'] == '':
                imgtext = text_to_rgb(self.value, self.label_font, self.color, width, height)
                canvas.paste(imgtext, self.xy)
            else:
                drawer.text(self.xy, self.value, font=self.label_font, fill=0x00)
                #drawer.text(self.xy, self.value, font=self.label_font, fill=self.color)
        else:
            if not self.icon:

                #logging.info('%s   --   %s' % (str(pos_label), str(pos_value)))
                if th_opt['main_text_color'] == '':
                    imgtext = text_to_rgb(self.label, self.label_font, self.color, width, height)
                    canvas.paste(imgtext, pos_label)
                    imgtext = text_to_rgb(self.value, self.text_font, self.color, width, height)
                    canvas.paste(imgtext, pos_value)
                else:
                    drawer.text(pos_label, self.label, font=self.label_font, fill=0x00)
                    drawer.text(pos_value, self.value, font=self.text_font, fill=0x00)
            else:
                #logging.warning(self.f_awesome)
                if not self.f_awesome:
                    canvas.paste(self.image, pos_label, self.image)
                else:
                    if self.color == 'white' : self.color = (254, 254, 254, 255)
                    #logging.warning(self.color)
                    if th_opt['main_text_color'] == '':
                        icon_img = ImageOps.colorize(self.image.convert('L'), black = self.color, white = 'white')
                        icon_img = icon_img.convert('RGBA')
                        canvas.paste(icon_img, pos_label, icon_img)
                    else:
                        canvas.paste(self.image, pos_label, self.image)

                if th_opt['main_text_color'] == '':
                    imgtext = text_to_rgb(self.value, self.text_font, self.color, width, height)
                    canvas.paste(imgtext, pos_value)
                else:
                    drawer.text(pos_value, self.value, font=self.text_font, fill=0x00)

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
