# fancygotchi

There's a preview of dev.    
Pimoroni Display Hat Mini 320x240  
![preview](https://raw.githubusercontent.com/V0r-T3x/fancygotchi/main/img/pwnagotchi.png)  

!!!DON'T TRY THE PLUGIN RIGHT NOW!!!
-----------------------

I'm in active development, if you want encourage me, become a [Patreon](https://patreon.com/v0rt3x_workshop).  
I will need to but a lot of compatible screen to make the plugin compatible with my theme manager plugin and it take a lot of my free time.  

```
I SHARE IT AS BACKUP AND TO SHOW THE PROGRESS
THIS CAN STUCK YOUR PWNAGOTCHI
```

A complete theme manager for the Pwnagotchi [In development]  
this project started with the [colorized_darkmode](https://github.com/V0r-T3x/pwnagotchi_LCD_colorized_darkmode)  

v.2023.02.0  
-review of the auto-installer, uninstaller and updater  
-basic display components options are linked into a single file (one file to control them all!!)  

v.2023.02.0  
-remove darkmode trace  
-new image genetating process added  
--text in 1bit with multiple colors  
--full resolution background  

-lcdhat  
-waveshare144.lcd  
-displayhatmini  

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



### Quick install steps:
- setting up your pi and the display correctly activate the web UI too
- downloading files inside the custom plugins folder (or into the default plugins folder) on your pwnagotchi (fancygotchi.py and the fancygotchi folder)
- I keep the fancygotchi disabled when I restart the pwnagotchi
```
ui.display.enabled = true
ui.display.type = "displayhatmini"
ui.display.color = "black"
ui.display.rotation = 180

main.plugins.fancygotchi.enabled = false
main.plugins.fancygotchi.theme = ""

```
- restart the pwnagotchi
- goto inside the web ui plugin page
- Enable the Fancygotchi plugin
- restart the pwnagotchi
- the mod should be installed  

### Note for the updater
- After the updater finish, the pwnagotchi will reboot itself and will have his original face, at this time, it need a reboot to really apply the change. After the reboot, it should be have his new face.
