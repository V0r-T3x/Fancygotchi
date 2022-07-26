# fancygotchi


!!!DON'T TRY THE PLUGIN RIGHT NOW!!!
-----------------------
```
I SHARE IT AS BACKUP AND TO SHOW THE PROGRESS
THIS CAN STUCK YOUR PWNAGOTCHI
```

A complete theme manager for the Pwnagotchi [In development]  
this project started with the [colorized_darkmode](https://github.com/V0r-T3x/pwnagotchi_LCD_colorized_darkmode)  

v.2022.07.3  
-installer/Uninstaller  
-Check update/Update  
  
-lcdhat  
-waveshare144.lcd  


note for the new image generation process:  
```
# ######################### Test for new image generation process ############################## 
# view.py canvas creation------
        imgtest = Image.new('RGBA', (128, 128), (0, 0, 0, 0)) # transparent layer image to paste all colorized texts
# components.py replacement for all texts
        filter_color = 'green' # color filter for the processed text
        imgtext = Image.new('1', (128, 128), 0xff) # 1 bit color layer to process the text
        dt = ImageDraw.Draw(imgtext)
        dt.text((10,10), "Hello World!!!", font=fonts.Bold, fill=0x00) # the text is created in black on white
        imgtext_colo = ImageOps.colorize(imgtext.convert('L'), black = filter_color, white = 'white') # the black is colorized with the color_filter color
        imgtext_rgba = imgtext_colo.convert('RGBA') # the colorized text layer is converted into RGBA (for alpha channel)
        datas = imgtext_rgba.getdata()
        newData = []
        for item in datas: # the white background color is converted into transparent one
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        imgtext_rgba.putdata(newData)
        imgtext_rgba.save('/home/pi/plugins/test.png', 'PNG')
        
#        dtt = ImageDraw.Draw(imgtext_rgba) # test for a text created into the RGBA instead of a 1 bit image to see the degradation
#        dtt.text((10,100), "Hello World!!!", font=fonts.Bold, fill=(255,0,0,255))

# /hw/files.py & /web/__init__.py 
        canvas_ = Image.open('%s/fancygotchi/img/%s' % (pwnagotchi.config['main']['custom_plugins'], pwnagotchi.config['main']['plugins']['fancygotchi']['bg_image']))
        canvas_.paste(imgtext_rgba, (0,0), imgtext_rgba) # the transparent layer with all the combined colorized texts is pasted to the background image
        canvas_.save('/home/pi/plugins/imgtest.png', 'PNG')
        canvas__ = canvas_.convert('1') # the full color UI image is converted into a 1 bit color to be managed by a mono color e-paper
        canvas__.save('/home/pi/plugins/imgtest-bw.png', 'PNG')
# ##############################################################################################
```
