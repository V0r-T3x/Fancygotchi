# FANCYGOTCHI  
----

There's a preview of dev.    
Pimoroni Display Hat Mini 320x240  
![preview](https://raw.githubusercontent.com/V0r-T3x/fancygotchi/main/img/pwnagotchi.png)  

-----------------------

I'm in active development, if you want encourage me, become a [Patreon](https://patreon.com/v0rt3x_workshop).  

This mod can be a bit slow with some features enabled on a raspberry pi zero.
(I'll add a note about the best light config to your with a rpi0w soon)  


```
I SHARE IT AS BACKUP AND TO SHARE THE PROGRESS  
BACKUP YOUR PWNAGOTCHI BEFORE INSTALL 
```

A complete theme manager for the Pwnagotchi [In development]   
this project started with the [colorized_darkmode](https://github.com/V0r-T3x/pwnagotchi_LCD_colorized_darkmode)  

v.2023.05.0  

✔️ Animated background (yes we can! Did in full color & 1bit)  
✔️ Theme web editor  
        ✔️switching theme on the go (yes we can!)(WIP)  
        ✔️linking icon feature  
        ✔️horizontal/vertical mode with rotation @Tzi sugg.  
✔️ adding background color to the low color mode  
✔️ adding the animated background to the low color mode  
✔️ adding a foreground option  
✔️ adding a function to the state.py to get and set any attribute of the state object (to change the theme OTG):  
✔️ adding a function to change theme:  
✔️ loop to set all new theme attributes  
✔️ changing the theme name inside the config.toml to keep the change on restart/reboot  
✔️ adding the partial refresh (other plugins could use it)  
✔️ Force the reboot after install, to avoid a manual restart   
✔️ removing creation or link of foreground image if not in use  
✔️ removing creation or link of background image if not in use  
✔️ removing creation of colorized background if no color set  
☑️ removing color filter on text for the 1bit mode (to do this, use main_text_color for display and webUI)  
✔️ stopping the OTG loop, enabled only on the web UI action  
✔️ one color instead of one color for each component, avoiding a loop for every components  
✔️ adding a variable to auto-install to backup a file or not (for file without original from the pwny)  
✔️ paste a new file in auto-install as the @Dal restart script  
✔️ adding a verification to the uninstaller to know if we need to replace a backup file or not   
✔️ adding a list of color to make components flashing  
✔️ adding Font Awesome as icons (*need the customization of a good font for the pwny*)  
✔️ adding a label_line_spacing to adjust it vertical position  

✔️ Backing up the RSA key, to avoid to regenerate it again if the pwny crash  
✔️ Addition of the restart script from @Dal  

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

### Quick install steps:
----
- setting up your pi and the display correctly activate the web UI too
- downloading files inside the custom plugins folder (or into the default plugins folder) on your pwnagotchi (fancygotchi.py and the fancygotchi folder)
- I keep the fancygotchi disabled when I restart the pwnagotchi
```
ui.display.enabled = true
ui.display.type = "displayhatmini" # use the right display for you 
ui.display.color = "black"
ui.display.rotation = 0 #keep it to 0, don't use it

main.plugins.fancygotchi.enabled = false
main.plugins.fancygotchi.theme = ''
main.plugins.fancygotchi.rotation = 0 #<--- use it
```
- restart the pwnagotchi
- goto inside the web ui plugin page
- wait for the automatic restart.
- the pwnagotchi should restart with it new face.

### Update steps:
----

Online update:
----
1-go inside the plugin page in the web UI  
2-check the box 'Online Update'  
3-click on Check fancygotchi update  
4-this will verify the online update folder to see if this one is a new version.  
5-if the new version is detected, it'll ask if you want install the update.  
6-a pop-up will show up when the install is finish (or if it failed...).  
7-the pwnagotchi should restart itself.  
8-you need to restart the service manually one time to finish the update. (the UI should be the orginal black and white one)  

After that, if all was successful, the theme should be come back and the update is supposed to be apply.  

Local update:
----
1-create a update folder inside the fancygotchi folder.  
2-download the fancygotchi-main-20XX-XX-X.zip.  
3-unzip this zip inside the .../fancygotchi/update/ folder. (this should give this path .../fancygotchi/update/fancygotchi-main/...  
4-go inside the plugin page in the web UI.  
5-click on Check fancygotchi update  
6-this will verify the local update folder to see if this one is a new version.  
7-if the new version is detected, it'll ask if you want install the update.  
8-a pop-up will show up when the install is finish (or if it failed...).  
9-the pwnagotchi should restart itself.  
10-you need to restart the service manually one time to finish the update. (the UI should be the orginal black and white one)  

After that, if all was successful, the theme should be come back and the update is supposed to be apply.  

### To create a theme:  
----  
you can create your own theme easily with fancygothci. You just have to copy the right display folders from the theme folder inside the fancygothci folder.  

The folder three is always the same for each theme. Like the cyber theme folder.   

![theme tree](https://raw.githubusercontent.com/V0r-T3x/fancygotchi/main/img/themes_tree_note.png)   

You have the img folder for all images used inside the theme. A css file to modify the webui. And a folder with the display name. The cyber use the displayhatmini.  

Inside the display folder, you will have two file config-h.toml and config-v.toml.  

They stand for the Horizon and vertical configuration files. Inside it you have all the possible options. Each position, color, if it can icon or not.. etc etc etc  

### Configuration files:
----
The configuration file header is composed with all the gobal options for the theme.  

Global options:  
----  

This start with `[theme.options]`.  

`stealth_mode = false`:  
It's not implemented yet, but will give a way to hide the pwnagotchi UI with a foreground image and potentially custom naive components.  

`fg_image`:
Foreground image name.  

`bg_color`:  
Background color.  

`bg_image`:  
Background image name.  

`bg_anim_image`:  
Animated background gif name.  

`font_sizes`:  
Font sizes in this order  
# [Bold, BoldSmall, Medium, Huge, BoldBig, Small]  

`font = 'DejaVuSansMono'`
Font name.  

`status_font`:  
Status font name (not work properly for now).  

`label_spacing`:  
General label space.  

`size_offset`:   
Status font offset.  

`fps`:  
Refresh rate of the UI.  

`cursor`:  
Name cursor.  

`friend_bars`:  
Friend bar icons.  

`friend_no_bars`:  
Friend bar at 0.  

`color_web` &  `color_display`:  
The color mode for the web UI or the Display.  
'2' = 1bit color mode B&W  
'' = full color mode  

`anim_web` & `anim_display`:  
If an animated background is set it can be use as a fixed image too  
true = animated  
false = fixed on the first frame  

`main_text_color`:  
If the full color or animated full color is enabled  
the main color will have priority on all text color  
*this option help to avoid too much lag on a raspberry pi zero w*  

`color_text`:  
What will be the text color for a low color display, possible options:  
'black'  
'white'  
'auto' = pale color will be 'white' and dark color will be 'black'  

Main theme options:  
----  

This part is for all the options native options of the pwnagotchi.  
This start with `[theme.main_elements]`.  

Each __Text__ components options can have those options:  

`position`:  
Position [x,y].  

`font`:  
Font type.  

`color`:  
The component color.  

`colors`:  
The component color table for an color animation [colorname1, colorname2, ...].  

`icon`:  
If enabled (true), the component value is treated as an image name to add to the image folder parth to use an image instead of a text.  

`f_awesome`:  
If enabled (true) and the icon feature is enabled, the component value is use to select the right font awesome character to use instead of a text.  

`f_awesome_size`:  
The font size for Font Awesome.  

Each __Label__ components options can have those options:  

`position`:  
Position [x,y].  

`label`:  
The label value.  

`label_font`:   
The label font.  

`text_font`:  
The text font.  

`label_spacing`:  
Custom label spacing for the component.  

`label_line_spacing`:  
Custom label vertical position compared to the label text.  

`color`:  
The component color.  

`colors`:  
The component color table for an color animation [colorname1, colorname2, ...].  

`icon`:  
If enabled (true), the component value is treated as an image name to add to the image folder parth to use an image instead of a text.  

`f_awesome`:  
If enabled (true) and the icon feature is enabled, the component value is use to select the right font awesome character to use instead of a text.  

`f_awesome_size`:  
The font size for Font Awesome.  

Plugins options:  
----  
The third section is for all other custom plugins configuration. This start with `[theme.plugin_elements]`.  

### To custom other plugin appearance:  
----  
For exemple with the bluetooth components, you can check inside the plugin file for the "add_element" variable:  

https://github.com/evilsocket/pwnagotchi/blob/master/pwnagotchi/plugins/default/bt-tether.py#L586  

```
ui.add_element('bluetooth', LabeledValue(color=BLACK, label='BT', value='-', position=(ui.width() / 2 - 15, 0),
                           label_font=fonts.Bold, text_font=fonts.Medium))
```

If you check into the config-h.toml you can check how the bluetooth part is constituted.  

All other custom plugins are stocked under [theme.plugin_elements].  

```
[theme.plugin_elements]

[theme.plugin_elements.bluetooth]
position = [276, 170]
label = 'BT'
value = '-'
label_font = 'Bold'
text_font = 'Medium'
label_spacing = 9
label_line_spacing = 0
color = 'lime'
colors = ['yellow','orange','red','purple','blue']
icon = false
f_awesome = false
f_awesome_size = 40
```
### To change the pwnagotchi face with image:  
----  
If you want you can change the pwny face too. Enable the icon feature, and by changing all faces variable inside the /etc/pwnagotchi/config.toml file with the image name stored inside the /themes/mytheme/img/.  

```
[theme.main_elements.face]
position = [14, 28]
font = "Huge"
color = "lime"
colors = ['yellow','orange','red','purple','blue']
icon = true # enable here
```

/etc/pwnagotchi/config.toml  
```
...
ui.faces.look_r = "look_r.png" #"( ⚆_⚆)"
ui.faces.look_l = "look_l.png" #"(☉_☉ )"
ui.faces.look_r_happy = "look_r_happy.png" #"( ◕‿◕)"
ui.faces.look_l_happy = "look_l_happy.png" #"(◕‿◕ )"
...
```

### On-The-Go refresh:  
----  
If something in the configration changed, no need to restart the pwnagotchi. You can go into Fancygotchi plugin page to refresh it. All the UI will be actualized.  

### Sharing custom theme:  
----  
If you create a custom theme and you want to share it. Just need to share the folder theme to another device with Fancygotchi installed.  

You can fork this repo, copy your new theme and push a commit to the main. I'll add them to the main repo.  
