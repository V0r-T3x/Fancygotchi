import pwnagotchi


import pwnagotchi.plugins as plugins

import logging
import traceback
import os
from os import fdopen, remove
import shutil
from shutil import move, copymode
from tempfile import mkstemp
from PIL import Image

import json
import toml
import csv
import _thread
from pwnagotchi import restart
from pwnagotchi.utils import save_config
from flask import abort, render_template_string


import requests

ROOT_PATH = '/usr/local/lib/python3.7/dist-packages/pwnagotchi'
FANCY_ROOT = os.path.dirname(os.path.realpath(__file__))
setattr(pwnagotchi, 'fancy_root', FANCY_ROOT)

with open('%s/fancygotchi/mod/files.csv' % (FANCY_ROOT), newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    data_dict = {}
    for row in reader:
        for key, value in row.items():
            if key in data_dict:
                data_dict[key].append(value)
            else:
                data_dict[key] = [value]
    FILES_TO_MOD = data_dict

for i in range(len(FILES_TO_MOD['path'])):
    path = data_dict['path'][i]
    file = data_dict['file'][i]

COMPATIBLE_PLUGINS = [
    'bt-tether',
    'memtemp',
    'clock',
    'display-password',
    'crack_house',
    'pisugar2',
    'pisugar3',
]

with open('%s/fancygotchi/mod/index.html' % (FANCY_ROOT), 'r') as file:
    html_contents = file.read()
INDEX = html_contents

def serializer(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

# replace one or many line with a specific keywork in the line
def replace_line(file_path, pattern, subst):
    line_skip = 0
    fh, abs_path = mkstemp()
    with fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                #logging.info('%s -- %s' % (line, pattern))
                #logging.info(len(subst))
                if pattern in line:
                    line_skip = len(subst) - 1
                    #logging.info(line_skip)
                    for su in subst:
                        new_file.write('%s\n' % (su))
                elif line_skip == 0:
                    new_file.write(line)
                else:
                    line_skip -=1
    copymode(file_path, abs_path)
    remove(file_path)
    move(abs_path, file_path)

# function to backup all actual modified files to make a new install update
def dev_backup(file_paths, dest_fold):
    for i in range(len(file_paths['path'])):
        path = data_dict['path'][i]
        file = data_dict['file'][i]
        if path[0] != '/':
            back_path = '%s%s' % (dest_fold, path)
            path = '%s/%s' % (ROOT_PATH, path)
        else:
            back_path = '%s%s' % (dest_fold, path)
        #logging.warning('%s%s' % (path, file))
        folders = os.path.split(back_path)[0]
        if not os.path.exists(folders):
            os.makedirs(folders)
        replace_file([file, ], [back_path, path], False, False, False)

# function to replace a file
# name = [target name, source name]
# path = [target path, source path]
def replace_file(name, path, backup, force, hidden, extension = "bak"):
    # definition of the backup name
    path_backup = path[0]
    if hidden:
        path_backup += '.'
    path_backup += '%s.%s' % (name[0], extension)
    # definition of the target and source paths
    if len(name) ==1:
        path_source = '%s%s' % (path[1], name[0])
    elif ((len(name) == 2) and (len(path) == 2)):
        path_source = '%s%s' % (path[1], name[1])
    path_target = '%s%s' % (path[0], name[0])
    if backup:
        if ((force) or (not force and not os.path.exists(path_backup))):
            logging.warning('%s ~~bak~~> %s' % (path_target, path_backup))
            shutil.copyfile(path_target, path_backup)
    if len(path) == 2:
        logging.warning('%s --mod--> %s' % (path_source, path_target))
        shutil.copyfile(path_source, path_target)

# function to verify if a new version is available
def check_update(vers, online):
    #logging.warning(("check update, online: %s") % (online))
    #logging.warning(FANCY_ROOT)
    nofile = False
    online_version = ''
    if online:
        URL = "https://raw.githubusercontent.com/V0r-T3x/fancygotchi/main/fancygotchi.py"
        response = requests.get(URL)
        lines = str(response.content)
        lines = lines.split('\\n')
        count = 0
        for line in lines:
            if '__version__ =' in line:
                count += 1
                if count == 3:
                    online_version = line.split('= ')[-1]
                    online_version = online_version[2:-2]
    elif not online:
        URL = '%s/fancygotchi/update/fancygotchi.py' % (FANCY_ROOT)
        if os.path.exists(URL):
            with open(URL, 'r') as f:
                lines = f.read()
            lines = lines.splitlines()
            count = 0
            for line in lines:
                #logging.warning(line)
                if '__version__ =' in line:
                    #logging.warning(line)
                    count += 1
                    if count == 3:
                        online_version = line.split('= ')[-1]
                        #logging.warning(online_version)
                        online_version = online_version[1:-1]
                        #logging.warning(online_version)
        else:
            nofile = True

    if not nofile:
        online_v = online_version.split('.')
        local_v = vers.split('.')
        if online_v[0] > local_v[0]:
            upd = True
        elif online_v[0] == local_v[0]:
            if online_v[1] > local_v[1]:
                upd = True
            elif online_v[1] == local_v[1]:
                if online_v[2] > local_v[2]:
                    upd = True
                else: upd = False
            else: upd = False
        else: upd = False
    else:
        upd = 2
        
    #logging.info('%s - %s' % (str(upd), online_version))
    return [upd, online_version]

def update(online):
    logging.warning('The updater is starting, online: %s' % (online))
    if online:#<-- Download from the Git & define the update path
        URL = "https://github.com/V0r-T3x/fancygotchi/archive/refs/heads/main.zip"
        response = requests.get(URL)
        path_upd_src = '%s/fancygotchi/tmp' % (FANCY_ROOT)
        filename = '%s/%s' % (path_upd_src, URL.split('/')[-1])
        os.system('mkdir %s' % (path_upd_src))
        with open(filename,'wb') as output_file:
            output_file.write(response.content)
        shutil.unpack_archive(filename, path_upd_src)
        path_upd = '%s/fancygotchi-main' % (path_upd_src)
    if not online:#<-- Define the update local path
        path_upd = '%s/fancygotchi/update' % (FANCY_ROOT)
        
    logging.warning('%s/fancygotchi.py ====> %s/fancygotchi.py' % (path_upd, FANCY_ROOT))
    #replace_file(['/fancygotchi.py'], [path_upd, FANCY_ROOT], False, False, False)
    shutil.copyfile('%s/fancygotchi.py' % (path_upd), '%s/fancygotchi.py' % (FANCY_ROOT))
 
    uninstall(True)

    mod_path = '%s/fancygotchi/mod' % (FANCY_ROOT)
    logging.warning('removing mod folder: %s' % (mod_path))
    os.system('rm -R %s' % (mod_path))
    deftheme_path = '%s/fancygotchi/theme/.default' % (FANCY_ROOT)
    logging.warning('removing mod folder: %s' % (deftheme_path))
    os.system('rm -R %s' % (deftheme_path))

    path_upd = '%s/fancygotchi' % (path_upd)
    logging.warning(path_upd)
    for root, dirs, files in os.walk(path_upd):
        #logging.warning('%s %s %s' % (root, dirs, files))
        for name in files:
            #logging.warning(name)
            if not name in ['README.md', 'readme.md']:
                src_file = os.path.join(root, name)
                logging.warning(src_file)
                dst_path = '%s/%s' % (FANCY_ROOT, root.split('fancygotchi-main/')[-1])
                dst_file = '%s/%s' % (dst_path, name)
                logging.warning(dst_file)
                logging.warning('%s ~~~~>%s' % (src_file, dst_file))
                logging.warning(dst_path)
                if not os.path.exists(dst_path):
                    os.makedirs(dst_path)
                shutil.copyfile(src_file, dst_file)

            
            # Check if the destination path exists and create it if it doesn't
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)

            # Copy the file to the destination path
            shutil.copyfile(src_file, dst_file)
    if online:
        logging.warning('removing the update temporary folder: %s' % (path_upd_src))
        os.system('rm -R %s' % (path_upd_src))

def uninstall(soft=False):
    # deleting the sym link for the img file
    dest = '%s/ui/web/static/img/' % (ROOT_PATH)
    logging.warning(dest)
    os.system('rm %s' % (dest))
    
    for i in range(len(FILES_TO_MOD['path'])):
        path = data_dict['path'][i]
        file = data_dict['file'][i]
        if path[0] != '/':
            path = '%s/%s' % (ROOT_PATH, path)
        #logging.warning(path)
        #logging.warning('%s.%s.original' % (path, file))
        logging.warning('%s%s' % (path, file))
        shutil.copyfile('%s.%s.original' % (path, file), '%s%s' % (path, file))
        os.system('rm %s' % ('%s.%s.original' % (path, file)))
        # disable the fancygotchi inside the config.toml
    if not soft:
        logging.warning('config.toml disable')
        replace_line('/etc/pwnagotchi/config.toml', 'fancygotchi.enabled',['main.plugins.fancygotchi.enabled = false'])
    else:
        logging.warning('config.toml enable')
        replace_line('/etc/pwnagotchi/config.toml', 'fancygotchi.enabled',['main.plugins.fancygotchi.enabled = true'])



class Fancygotchi(plugins.Plugin):
    __name__ = 'Fancygotchi'
    __author__ = '@V0rT3x https://github.com/V0r-T3x'
    __version__ = '2023.03.2'
    __license__ = 'GPL3'
    __description__ = 'A theme manager for the Pwnagotchi [cannot be disabled, need to be uninstalled from inside the plugin]'

    def __init__(self):
        self.ready = False
        self.mode = 'MANU'

    def on_config_changed(self, config):
        self.config = config
        self.ready = True

    def on_ready(self, agent):
        self.mode = 'MANU' if agent.mode == 'manual' else 'AUTO'

    def on_internet_available(self, agent):
        self.mode = 'MANU' if agent.mode == 'manual' else 'AUTO'

    def on_loaded(self):
        logging.info("[FANCYGOTCHI] Beginning Fancygotchi load")

        custom_plugins_path = pwnagotchi.config['main']['custom_plugins']
        if not custom_plugins_path[-1] == '/': custom_plugins_path += '/'
        ui = pwnagotchi.config['ui']['display']['type']
#<        logging.info("[FANCYGOTCHI] %s" % (ui))
        theme = pwnagotchi.config['main']['plugins']['fancygotchi']['theme']
        
        display = [pwnagotchi.config['ui']['display']['enabled'], pwnagotchi.config['ui']['display']['type']]
        #logging.info('[FANCYGOTCHI] %s' % display)

        """
        check_update(self.__version__)
        update(True)
        replace_file(['target.txt', 'test.txt'], ['/home/pi/', '/home/pi/'], True, False, False)
        check_update(self.__version__)
        
        dev_backup(FILES_TO_MODIFY, "/home/pi/plugins/fancygotchi/mod/2022-07-10/")
        
        subst = [
            'main.ui = false', 
            '    hell', 
            '    hell', 
            'HELL YEAH', 
            'HELL YEAH!!!'
        ]
        replace('/home/pi/test.txt', 'main.ui', subst)
        """

        # Verification to the enabled display
        compatible = 0
        if ui == 'lcdhat':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare 1.33" LCD screen')
        elif ui == 'waveshare_v2':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare v.2 E-paper screen')
        #elif ui == 'oledhat':
        #    compatible = 1
        #    logging.info('[FANCYGOTCHI] waveshare 1.3" OLED screen')
        #elif ui == 'waveshare27inch':
        #    compatible = 1
        #    logging.info('[FANCYGOTCHI] waveshare 2.7" E-paper screen')
        elif ui == 'waveshare144lcd':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare 1.44" LCD screen')
        elif ui == 'displayhatmini':
            compatible = 1
            logging.info('[FANCYGOTCHI] pimoroni 2" LCD Display Hat Mini screen')
        elif ui == 'waveshare35lcd':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare 3,5" LCD screen')

        elif not pwnagotchi.config['ui']['display']['enabled']:
            compatible = 1
            logging.info('[FANCYGOTCHI] Pwnagotchi headless mode')
        else:
            logging.warning('[FANCYGOTCHI] The screen is not compatible with the plugin')

        # If the initial screen isn't compatible the mod will not install
        #logging.info('[FANCYGOTCHI] compatible: %s' % (compatible))
        if compatible:
            # Linking bg image to the web ui
            src = '%s/fancygotchi/img/' % (FANCY_ROOT)
            dest = '%s/ui/web/static' % (ROOT_PATH)
            #logging.info('[FANCYGOTCHI] ln -s %s %s' % (src, dest))
            if not os.path.exists('%s/img/' % (dest)):
                #logging.info('[FANCYGOTCHI] link for img don\'t exist')
                os.system('ln -s %s %s' % (src, dest))
                #logging.info('[FANCYGOTCHI] link for img created')
            # Loop to verify if the backup is here, and if not it backup original files
            # and replace them all with link from plugin folder
        for i in range(len(FILES_TO_MOD['path'])):
            path = data_dict['path'][i]
            file = data_dict['file'][i]
            #logging.warning(path)
            #logging.warning(file)
            slash = ''
            if not path[0] == '/':
                #logging.warning(path[0])
                dest_path = '%s/%s' % (ROOT_PATH, path)
                slash = '/'
                #src_path = '%s/fancygotchi/mod%s' % (FANCY_ROOT, path)
            else: 
                dest_path = path
                slash = ''
            ori_bak = '%s.%s.original' % (dest_path, file)
            #logging.warning(ori_bak)
            src_path = '%s/fancygotchi/mod%s%s' % (FANCY_ROOT, slash, path)
            #logging.warning(src_path)
            #logging.warning(dest_path)
            if not os.path.exists(ori_bak):
                #logging.warning(ori_bak)
                #logging.warning(src_path)
                #logging.warning(dest_path)
                replace_file([file], [dest_path, src_path], True, False, True, 'original')
            
            #logging.info('%s%s' % (path, file))

        logging.info('[FANCYGOTCHI] Theme manager loaded')

        # Verification to enabled and compatible plugins
        for plugin in pwnagotchi.config['main']['plugins']:
            if pwnagotchi.config['main']['plugins'][plugin]['enabled']:
                for c_plugin in COMPATIBLE_PLUGINS:
                    #logging.info('[FANCYGOTCHI] %s = %s' % (plugin, c_plugin))
                    if plugin == c_plugin:
                        # scanning custom plugins folder
                        for x in os.listdir(pwnagotchi.config['main']['custom_plugins']):
                            if x.endswith(".py") and x == '%s.py' % (plugin):
                                
                                logging.info('[FANCYGOTCHI] %s/%s' % (pwnagotchi.config['main']['custom_plugins'], x))
                        #scanning main plugins folder
                        for x in os.listdir('%s/plugins/default/' % (ROOT_PATH)):
                            if x.endswith(".py") and x == '%s.py' % (plugin):  
                                logging.info('[FANCYGOTCHI] %s/plugins/default/%s' % (ROOT_PATH, x))
                                #logging.info('[FANCYGOTCHI] %s' % (pwnagotchi.config['ui']['display']['face']))                              
                        #logging.info(plugin)

    def on_webhook(self, path, request):
        custom_plugins_path = pwnagotchi.config['main']['custom_plugins']
        if not self.ready:
            return "Plugin not ready"

        if request.method == "GET":
            if path == "/" or not path:
                return render_template_string(INDEX)
            elif path == "get-config":
                # send configuration
                logging.info(type(self.config))
                return json.dumps(self.config, default=serializer)
            elif path == "get-theme":
                # Verifying the image size for resolution
                with Image.open('/var/tmp/pwnagotchi/pwnagotchi.png') as img:
                    width, height = img.size
                # Filling the system/theme config
                theme = {
                    'is_display': self.config['ui']['display']['enabled'],
                    'display': self.config['ui']['display']['type'],
                    'resolution': [width, height],
                    'theme': self.config['main']['plugins']['fancygotchi']['theme'],
                    'bg_image': pwnagotchi._theme['theme']['options']['bg_image']
                }
                # adding all the main and the plugins position
                return json.dumps(theme, default=serializer)
            else:
                abort(404)

        elif request.method == "POST":
            if path == "save-config":
                try:
                    logging.info(request.get_json())
            #        save_config(request.get_json(), '/etc/pwnagotchi/config.toml') # test
            #        _thread.start_new_thread(restart, (self.mode,))
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "config error", 500

            elif path == "uninstall":
                try:
                    uninstall()
                    _thread.start_new_thread(restart, (self.mode,))
                    logging.info(str(request.get_json()))
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "uninstall error", 500

            elif path == "devbackup":
                try:
                    jreq = request.get_json()
                    folder = json.loads(json.dumps(jreq))
                    fancybu = '%s/fancybackup/' % (FANCY_ROOT)
                    dest = '%s%s/' % (fancybu, str(folder["response"]))
                    if not os.path.exists(fancybu):
                        os.system('mkdir %s' % (dest))
                    if not os.path.exists(dest):
                        os.system('mkdir %s' % (dest))
                    dev_backup(FILES_TO_MOD, dest);
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    logging.error(traceback.format_exc())
                    return "dev backup error", 500

            elif path == "check_online_update":
                try:
                    is_update = check_update(self.__version__, True)
                    logging.info(is_update[1])
                    upd = '%s,%s' % (is_update[0], is_update[1])
                    return upd
                except Exception as ex:
                    logging.error(ex)
                    return "update check error, check internet connection", 500

            elif path == "online_update":
                try:
                    update(True)
                    _thread.start_new_thread(restart, (self.mode,))
                    logging.info(str(request.get_json()))
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "update error", 500
                    
            elif path == "check_local_update":
                try:
                    is_update = check_update(self.__version__, False)
                    logging.info(is_update)
                    #if upd == 2:
                    upd = '%s,%s' % (is_update[0], is_update[1])
                    logging.info(upd)
                    return upd
                except Exception as ex:
                    logging.error(ex)
                    return "update check error, check internet connection", 500

            elif path == "local_update":
                try:
                    update(False)
                    _thread.start_new_thread(restart, (self.mode,))
                    logging.info(str(request.get_json()))
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "update error", 500
        abort(404)