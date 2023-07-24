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

with open('%s/fancygotchi/sys/files.csv' % (FANCY_ROOT), newline='') as csvfile:
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

with open('%s/fancygotchi/sys/index.html' % (FANCY_ROOT), 'r') as file:
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
                if pattern in line:
                    line_skip = len(subst) - 1
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
        if path[0] != '/' or len(path) == 1:
            if len(path) == 1:
                path = ''
            back_path = '%s/%s' % (dest_fold, path)
            path = '%s/%s' % (ROOT_PATH, path)
        else:
            back_path = '%s%s' % (dest_fold, path)
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
            #logging.info('[FANCYGOTCHI] %s ~~bak~~> %s' % (path_target, path_backup))
            shutil.copyfile(path_target, path_backup)
    if len(path) == 2:
        #logging.info('[FANCYGOTCHI] %s --mod--> %s' % (path_source, path_target))
        shutil.copyfile(path_source, path_target)

# function to verify if a new version is available
def check_update(vers, online):
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
        URL = '%s/fancygotchi/update/fancygotchi-main/fancygotchi.py' % (FANCY_ROOT)
        if os.path.exists(URL):
            with open(URL, 'r') as f:
                lines = f.read()
            lines = lines.splitlines()
            count = 0
            for line in lines:
                if '__version__ =' in line:
                    count += 1
                    if count == 3:
                        online_version = line.split('= ')[-1]
                        online_version = online_version[1:-1]
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

    return [upd, online_version]

def update(online):
    logging.info('[FANCYGOTCHI] The updater is starting, is online: %s' % (online))
    path_upd = '%s/fancygotchi/update' % (FANCY_ROOT)
    if online:#<-- Download from the Git & define the update path
        URL = "https://github.com/V0r-T3x/fancygotchi/archive/refs/heads/main.zip"
        response = requests.get(URL)
        filename = '%s/%s' % (path_upd, URL.split('/')[-1])
        os.system('mkdir %s' % (path_upd))
        with open(filename,'wb') as output_file:
            output_file.write(response.content)
        shutil.unpack_archive(filename, path_upd)
    path_upd += '/fancygotchi-main'
    
    logging.info('[FANCYGOTCHI] %s/fancygotchi.py ====> %s/fancygotchi.py' % (path_upd, FANCY_ROOT))
    shutil.copyfile('%s/fancygotchi.py' % (path_upd), '%s/fancygotchi.py' % (FANCY_ROOT))
    
    uninstall(True)
    mod_path = '%s/fancygotchi/mod' % (FANCY_ROOT)
    logging.info('[FANCYGOTCHI] removing mod folder: %s' % (mod_path))
    os.system('rm -R %s' % (mod_path))
    deftheme_path = '%s/fancygotchi/theme/.default' % (FANCY_ROOT)
    logging.info('[FANCYGOTCHI] removing theme folder: %s' % (deftheme_path))
    os.system('rm -R %s' % (deftheme_path))
    sys_path = '%s/fancygotchi/sys' % (FANCY_ROOT)
    logging.info('[FANCYGOTCHI] removing sys folder: %s' % (sys_path))
    os.system('rm -R %s' % (sys_path))
    
    path_upd += '/fancygotchi'
    for root, dirs, files in os.walk(path_upd):
        for name in files:
            if not name in ['README.md', 'readme.md']:
                src_file = os.path.join(root, name)
                dst_path = '%s/%s' % (FANCY_ROOT, root.split('fancygotchi-main/')[-1])
                dst_file = '%s/%s' % (dst_path, name)
                logging.info('[FANCYGOTCHI] %s ~~~~> %s' % (src_file, dst_file))
                
                if not os.path.exists(dst_path):
                    os.makedirs(dst_path)
                shutil.copyfile(src_file, dst_file)
            
                # Check if the destination path exists and create it if it doesn't
                if not os.path.exists(dst_path):
                    os.makedirs(dst_path)

                # Copy the file to the destination path
                shutil.copyfile(src_file, dst_file)
    if online:
        path_upd = '%s/fancygotchi/update' % (FANCY_ROOT)
        logging.info('[FANCYGOTCHI] removing the update temporary folder: %s' % (path_upd))
        os.system('rm -R %s' % (path_upd))

def uninstall(soft=False):
    # deleting the sym link for the img file
    dest = '%s/ui/web/static/img' % (ROOT_PATH)
    logging.info('[FANCYGOTCHI] removing img folder link '+dest)
    os.system('rm %s' % (dest))
    
    for i in range(len(FILES_TO_MOD['path'])):
        path = data_dict['path'][i]
        file = data_dict['file'][i]
        bak = data_dict['backup'][i]
        #special uninstallation commands
        coms = data_dict['ucommands'][i]

        if not coms == None:
            com_list = coms.split('`')

        if path[0] != '/' or len(path) == 1:
            if len(path) == 1:
                path = ''
            path = '%s/%s' % (ROOT_PATH, path)

        if not coms == None:
            for command in com_list:
                logging.info('[FANCYGOTCHI] special command: '+command)
                os.system(command)

        if bak == '1':
            logging.info('[FANCYGOTCHI] move back original file: %s%s' % (path, file))
            shutil.copyfile('%s.%s.original' % (path, file), '%s%s' % (path, file))
            os.system('rm %s' % ('%s.%s.original' % (path, file)))
            #os.remove('%s.%s.original' % (path, file))
        else:
            logging.info('[FANCYGOTCHI] remove added file: %s%s' % (path, file))
            os.system('rm %s' % ('%s%s' % (path, file)))
            #os.remove('%s.%s' % (path, file))
        # disable the fancygotchi inside the config.toml
    if not soft:
        logging.info('[FANCYGOTCHI] disabled in the config.toml')
        replace_line('/etc/pwnagotchi/config.toml', 'fancygotchi.enabled',['main.plugins.fancygotchi.enabled = false'])
    else:
        logging.info('[FANCYGOTCHI] enabled in the config.toml')
        replace_line('/etc/pwnagotchi/config.toml', 'fancygotchi.enabled',['main.plugins.fancygotchi.enabled = true'])



class Fancygotchi(plugins.Plugin):
    __name__ = 'Fancygotchi'
    __author__ = '@V0rT3x https://github.com/V0r-T3x'
    __version__ = '2023.07.0'
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
        theme = pwnagotchi.config['main']['plugins']['fancygotchi']['theme']
            
        # Linking bg image to the web ui
        if pwnagotchi.config['main']['plugins']['fancygotchi']['theme'] != '':
            src = '%s/fancygotchi/themes/%s/img' % (FANCY_ROOT, pwnagotchi.config['main']['plugins']['fancygotchi']['theme'])
        else:
            src = '%s/fancygotchi/themes/.default/img' % (FANCY_ROOT)
        dest = '%s/ui/web/static' % (ROOT_PATH)

        remove = '%s/img' % (dest)
        os.system('rm %s' % (remove))
        os.system('ln -s %s %s' % (src, dest))

        # Loop to verify if the backup is here, and if not it backup original files
        # and replace them all with link from plugin folder
        restart = 0
        for i in range(len(FILES_TO_MOD['path'])):            
            path = data_dict['path'][i]
            file = data_dict['file'][i]
            bak = data_dict['backup'][i]
            #special installation commands
            coms = data_dict['icommands'][i]
            

            if not coms == None:
                com_list = coms.split('`')

            #logging.warning(com_list)

            slash = ''
            
            if path[0] != '/' or len(path) == 1:
                if len(path) == 1:
                    path = ''
                dest_path = '%s/%s' % (ROOT_PATH, path)
                slash = '/'
            else:
                dest_path = path
                slash = ''
            if bak == '1': ori_bak = '%s.%s.original' % (dest_path, file)
            else: ori_bak = '%s.%s' % (dest_path, file)
            src_path = '%s/fancygotchi/mod%s%s' % (FANCY_ROOT, slash, path)

            if not os.path.exists(ori_bak) or file.endswith('css'):
                if file.endswith('css'):
                    if pwnagotchi.config['main']['plugins']['fancygotchi']['theme'] != '':
                        theme = pwnagotchi.config['main']['plugins']['fancygotchi']['theme']
                    else:
                        theme = '.default'
                    src_path = '%s/fancygotchi/themes/%s/' % (FANCY_ROOT, theme)

                if bak == '1':
                    if not os.path.exists('%s.%s.original' % (dest_path, file)):
                        logging
                        restart = 1
                    #create a backup if needed and move moded file
                    replace_file([file], [dest_path, src_path], True, False, True, 'original')  
                else:

                    #if the file exist, skip it
                    if not os.path.exists('%s%s' % (dest_path, file)):
                        restart = 1
                        #if the file didn't exist, move it and run special commands if needed
                        #only move the moded file
                        replace_file([file], [dest_path, src_path], False, False, False)
                if coms != None and restart == 1:
                    for command in com_list:
                        logging.warning('[FANCYGOTCHI] special command: '+command)
                        os.system(command)
        logging.warning(restart)
        if restart == 1:
            logging.warning('need a restart')
            os.system('service pwnagotchi restart')

        logging.info('[FANCYGOTCHI] Theme manager loaded')

    def on_webhook(self, path, request):
        if not self.ready:
            return "Plugin not ready"

        if request.method == "GET":
            if path == "/" or not path:
                pwnagotchi.fancy_change = True
                return render_template_string(INDEX)
            elif path == "get-config":
                # send configuration
                return json.dumps(self.config, default=serializer)
            elif path == "get-options":
                # send options
                return json.dumps(pwnagotchi._theme['theme']['options'], default=serializer)
            elif path == "get-main":
                # send main components
                return json.dumps(pwnagotchi._theme['theme']['main_elements'], default=serializer)
            elif path == "get-plugins":
                # send plugins components
                return json.dumps(pwnagotchi._theme['theme']['plugin_elements'], default=serializer)
            elif path == "get-css":
                # send css
                with open('%s/style.css' % (pwnagotchi.fancy_theme), 'r') as css_file:
                    css_content = css_file.read()
                css_dump = {
                    'css': css_content
                }
                return json.dumps(css_dump, default=serializer)

            elif path == "get-info":
                # Verifying the image size for resolution
                with Image.open('/var/tmp/pwnagotchi/pwnagotchi.png') as img:
                    width, height = img.size
                # Filling the system/theme config
                info = {
                    'is_display': self.config['ui']['display']['enabled'],
                    'display': self.config['ui']['display']['type'],
                    'resolution': [width, height],
                    'theme': self.config['main']['plugins']['fancygotchi']['theme'],
                    'bg_image': pwnagotchi._theme['theme']['options']['bg_image']
                }
                # adding all the main and the plugins position
                return json.dumps(info, default=serializer)
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
                    dest = '%s%s' % (fancybu, str(folder["response"]))
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
