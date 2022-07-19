from pwnagotchi.ui.view import View
import pwnagotchi
import pwnagotchi.plugins as plugins
import logging
import os
from os import fdopen, remove
import shutil
from shutil import move, copymode
from tempfile import mkstemp
from PIL import Image

import json
import toml
import _thread
from pwnagotchi import restart, plugins
from pwnagotchi.utils import save_config
from flask import abort, render_template_string

import requests

ROOT_PATH = '/usr/local/lib/python3.7/dist-packages/pwnagotchi'

FILES_TO_MODIFY = [
    ['/ui/', 'view.py'],
    ['/ui/', 'components.py'],
    ['/ui/hw/', 'base.py'],
    ['/ui/hw/', 'lcdhat.py'],
    ['/ui/hw/', 'oledhat.py'],
    ['/ui/hw/', 'waveshare2.py'],
    ['/ui/hw/', 'waveshare27inch.py'],
    ['/ui/hw/', 'waveshare144lcd.py'],
    ['/ui/hw/libs/waveshare/lcdhat144/', 'epd.py'],
    ['/ui/web/', '__init__.py'],
    ['/ui/web/static/css/', 'style.css'],
    ['/ui/web/templates/','base.html'],
    ['/ui/web/templates/','plugins.html'],
    ['/ui/web/templates/','profile.html'],
    ['/plugins/default/','logtail.py'],
]

COMPATIBLE_PLUGINS = [
    'bt-tether',
    'memtemp',
    'clock',
    'display-password',
    'crack_house',
    'pisugar2',
]

INDEX = """
{% extends "base.html" %}
{% set active_page = "plugins" %}
{% block title %}
    Fancygotchi
{% endblock %}

{% block meta %}
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, user-scalable=0" />
{% endblock %}


{% block styles %}
{{ super() }}
<style>
    #wrap_img{
        position:relative;
        //padding:50px;
        border:1px solid lime;
    }
    #bg_img{
        top:50px;
        position:relative;
        //-webkit-filter: grayscale(1);
       margin-left:50px;
    }
    #content{
        position:relative;
    }
    #filter_color{
        top:50px;
        margin-left:50px;
        background-color: rgba(0, 255, 0, 0.5);
        position:absolute;
        //width:100%;
        //height:100%;
        z-index:100;
    }
</style>
{% endblock %}

{% block content %}
    <div id="divTop">
        <span><input id="textDevBackup" type="text" placeholder="Backup folder name..."></input></span>
        <span><button id="btnDevBackup" type="button" onclick="dev_backup()">dev_backup fancygotchi</button></span>
        <button id="btnSave" type="button" onclick="saveConfig()">Save theme and restart</button>
        <button id="btnUninstall" type="button" onclick="uninstall()">Uninstall fancygotchi</button>
        <button id="btnUpdate" type="button" onclick="check_update()">Check fancygotchi update</button>
        <input type="text" id="searchText" placeholder="Search for options ..." title="Type an option name">
    </div>
    <div>THEME MANAGER</div>
    <div id="debug"></div>
    <div id="wrap_img">
        <div id="filter_color"></div>
        <div id="bg_img"></div>
    </div>
    <div id="content"></div>
{% endblock %}

{% block script %}
        function saveConfig(){
            // get table
            var table = document.getElementById("tableOptions");
            if (table) {
                var json = tableToJson(table);
                sendJSON("fancygotchi/save-config", json, function(response) {
                    if (response) {
                        if (response.status == "200") {
                            alert("Config got updated");
                        } else {
                            alert("Error while updating the config (err-code: " + response.status + ")");
                        }
                    }
                });
            }
        }
        function uninstall(){
            if (confirm("Do you want uninstall Fancygotchi?")){
                var json = {"response":"1"};
                sendJSON("fancygotchi/uninstall", json, function(response) {
                    if (response) {
                        if (response.status == "200") {
                            alert("fancygotchi is uninstalled");
                            window.location.href = '/';
                        } else {
                            alert("Error while uninstalling fancygotchi (err-code: " + response.status + ")");
                        }
                    }
                });
            } else {
                alert("uninstall was canceled");
            }
        }
        function check_update(){
            if (confirm("Do you want check for Fancygotchi update?")){
                var json = {"response":"1"};
                sendJSON("fancygotchi/check_update", json, function(response) {
                    if (response) {
                        if (response.status == "200") {
                            is_version = response.responseText.split(',')
                            if (is_version[0] == 'True') {
                                //alert('New fancygotchi update v.' + is_version[1]);
                                if (confirm("Do you want update Fancygotchi to v." + is_version[1] + "?")){
                                    var json = {"response":"1"};
                                    sendJSON("fancygotchi/update", json, function(response) {
                                        if (response) {
                                            if (response.status == "200") {
                                                alert("fancygotchi is updated");
                                                //window.location.href = '/';
                                            } else {
                                                alert("Error while updating fancygotchi (err-code: " + response.status + ")");
                                            }
                                        }
                                    });
                                } else {
                                    alert("update was canceled");
                                }
                            }
                            else {
                                alert('Fancygotchi is up-to-date v.' + is_version[1]);
                            //window.location.href = '/';
                            }
                        } else {
                            alert("Error while checking fancygotchi update (check internet connection) (err-code: " + response.status + ")");
                        }
                    }
                });
            } else {
                alert("checking update was canceled");
            }

        }
        function update(){
            if (confirm("Do you want update Fancygotchi?")){
                var json = {"response":"1"};
                sendJSON("fancygotchi/update", json, function(response) {
                    if (response) {
                        if (response.status == "200") {
                            alert("fancygotchi is updated");
                            window.location.href = '/';
                        } else {
                            alert("Error while updating fancygotchi (err-code: " + response.status + ")");
                        }
                    }
                });
            } else {
                alert("update was canceled");
            }

        }

        // Function to backup all dev files into the specified folder
        function dev_backup() {
            var folder = document.getElementById("textDevBackup").value;
            if (folder == "") {
                folder = "last_backup";
            }
            alert(folder);
            if (confirm("Do you want backup Fancygotchi dev files?")){
                var json = {"response": folder};
                sendJSON("fancygotchi/devbackup", json, function(response) {
                    if (response) {
                        if (response.status == "200") {
                            alert("dev fancygotchi is backed up");
                            //window.location.href = '/';
                        } else {
                            alert("Error while dev backed up the fancygotchi (err-code: " + response.status + ")");
                        }
                    }
                });
            } else {
                alert("dev backup was canceled");
            }
        }


        var searchInput = document.getElementById("searchText");
        searchInput.onkeyup = function() {
            var filter, table, tr, td, i, txtValue;
            filter = searchInput.value.toUpperCase();
            table = document.getElementById("tableOptions");
            if (table) {
                tr = table.getElementsByTagName("tr");

                for (i = 0; i < tr.length; i++) {
                    td = tr[i].getElementsByTagName("td")[1];
                    if (td) {
                        txtValue = td.textContent || td.innerText;
                        if (txtValue.toUpperCase().indexOf(filter) > -1) {
                            tr[i].style.display = "";
                        }else{
                            tr[i].style.display = "none";
                        }
                    }
                }
            }
        }

        function sendJSON(url, data, callback) {
          var xobj = new XMLHttpRequest();
          var csrf = "{{ csrf_token() }}";
          xobj.open('POST', url);
          xobj.setRequestHeader("Content-Type", "application/json");
          xobj.setRequestHeader('x-csrf-token', csrf);
          xobj.onreadystatechange = function () {
                if (xobj.readyState == 4) {
                  callback(xobj);
                }
          };
          xobj.send(JSON.stringify(data));
        }

        function loadJSON(url, callback) {
          var xobj = new XMLHttpRequest();
          xobj.overrideMimeType("application/json");
          xobj.open('GET', url, true);
          xobj.onreadystatechange = function () {
                if (xobj.readyState == 4 && xobj.status == "200") {
                  callback(JSON.parse(xobj.responseText));
                }
          };
          xobj.send(null);
        }

        // https://stackoverflow.com/questions/19098797/fastest-way-to-flatten-un-flatten-nested-json-objects
        function unFlattenJson(data) {
            "use strict";
            if (Object(data) !== data || Array.isArray(data))
                return data;
            var result = {}, cur, prop, idx, last, temp, inarray;
            for(var p in data) {
                cur = result, prop = "", last = 0, inarray = false;
                do {
                    idx = p.indexOf(".", last);
                    temp = p.substring(last, idx !== -1 ? idx : undefined);
                    inarray = temp.startsWith('#') && !isNaN(parseInt(temp.substring(1)))
                    cur = cur[prop] || (cur[prop] = (inarray ? [] : {}));
                    if (inarray){
                        prop = temp.substring(1);
                    }else{
                        prop = temp;
                    }
                    last = idx + 1;
                } while(idx >= 0);
                cur[prop] = data[p];
            }
            return result[""];
        }

        function flattenJson(data) {
            var result = {};
            function recurse (cur, prop) {
                if (Object(cur) !== cur) {
                    result[prop] = cur;
                } else if (Array.isArray(cur)) {
                     for(var i=0, l=cur.length; i<l; i++)
                         recurse(cur[i], prop ? prop+".#"+i : ""+i);
                    if (l == 0)
                        result[prop] = [];
                } else {
                    var isEmpty = true;
                    for (var p in cur) {
                        isEmpty = false;
                        recurse(cur[p], prop ? prop+"."+p : p);
                    }
                    if (isEmpty)
                        result[prop] = {};
                }
            }
            recurse(data, "");
            return result;
        }

        function delRow(btn) {
            var tr = btn.parentNode.parentNode.parentNode;
            tr.parentNode.removeChild(tr);
        }

        function jsonToTable(json) {
            var table = document.createElement("table");
            table.id = "tableOptions";

            // create header
            var tr = table.insertRow();
            var thDel = document.createElement("th");
            thDel.innerHTML = "";
            var thOpt = document.createElement("th");
            thOpt.innerHTML = "Option";
            var thVal = document.createElement("th");
            thVal.innerHTML = "Value";
            tr.appendChild(thDel);
            tr.appendChild(thOpt);
            tr.appendChild(thVal);

            var td, divDelBtn, btnDel;
            // iterate over keys
            Object.keys(json).forEach(function(key) {
                tr = table.insertRow();
                // option
                td = document.createElement("td");
                td.setAttribute("data-label", "Option");
                td.innerHTML = key;
                tr.appendChild(td);
                // value
                td = document.createElement("td");
                td.setAttribute("data-label", "Value");
                if(typeof(json[key])==='boolean'){
                    input = document.createElement("select");
                    input.setAttribute("id", "boolSelect");
                    tvalue = document.createElement("option");
                    tvalue.setAttribute("value", "true");
                    ttext = document.createTextNode("True")
                    tvalue.appendChild(ttext);
                    fvalue = document.createElement("option");
                    fvalue.setAttribute("value", "false");
                    ftext = document.createTextNode("False");
                    fvalue.appendChild(ftext);
                    input.appendChild(tvalue);
                    input.appendChild(fvalue);
                    input.value = json[key];
                    document.body.appendChild(input);
                    td.appendChild(input);
                    tr.appendChild(td);
                } else {
                    input = document.createElement("input");
                    if(Array.isArray(json[key])) {
                        input.type = 'text';
                        input.value = '[]';
                    }else{
                        input.type = typeof(json[key]);
                        input.value = json[key];
                    }
                    td.appendChild(input);
                    tr.appendChild(td);
                }
            });
            return table;
        }

        function jsonToArray(json) {
            var theme_array = [];
            var x = 0;
            Object.keys(json).forEach(function(key) {
                //alert(json[key]);
                theme_array[x] = [key, json[key]];
                //alert(theme_array[x][0]);
                x+=1;
            });
            return theme_array;
        }

        function tableToJson(table) {
            var rows = table.getElementsByTagName("tr");
            var i, td, key, value;
            var json = {};

            for (i = 0; i < rows.length; i++) {
                td = rows[i].getElementsByTagName("td");
                if (td.length == 2) {
                    // td[0] = del button
                    key = td[0].textContent || td[0].innerText;
                    var input = td[1].getElementsByTagName("input");
                    var select = td[1].getElementsByTagName("select");
                    if (input && input != undefined && input.length > 0 ) {
                        if (input[0].type == "text") {
                            if (input[0].value.startsWith("[") && input[0].value.endsWith("]")) {
                                json[key] = JSON.parse(input[0].value);
                            }else{
                                json[key] = input[0].value;
                            }
                        }else if (input[0].type == "number") {
                            json[key] = Number(input[0].value);
                        }
                    } else if(select && select != undefined && select.length > 0) {
                        var myValue = select[0].options[select[0].selectedIndex].value;
                        json[key] = myValue === 'true';
                    }
                }
            }
            return unFlattenJson(json);
        }

        // Call to generate the page
        loadJSON("fancygotchi/get-theme", function(response) {
            var flat_json = flattenJson(response);
            var table = jsonToTable(flat_json);
            var theme_array = jsonToArray(flat_json);
            var divContent = document.getElementById("content");
            var bg_img = document.getElementById('bg_img');
            var wrap_img = document.getElementById('wrap_img');
            var is_up = document.getElementById('btnUpdate');
            bg_img.style.backgroundImage = "url('/img/" + theme_array[8][1] + "')";
            wrap_img.style.width = (theme_array[2][1] + 100) + 'px';
            wrap_img.style.height = (theme_array[3][1] + 100) + 'px';
            bg_img.style.width = theme_array[2][1] + 'px';
            bg_img.style.height = theme_array[3][1] + 'px';
            filter_color.style.width = theme_array[2][1] + 'px';
            filter_color.style.height = theme_array[3][1] + 'px';
            if (theme_array[4][1] == true) {
                bg_img.style.filter = 'invert(1)'
            }
            else {
                bg_img.style.filter = 'invert(0)'
            }
                
            //alert(theme_array[3][1] + 'px');
            //bg_img.style.background = theme_array[3][1];

            divContent.innerHTML = "";
            divContent.appendChild(table);

            
        });
{% endblock %}
"""

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
                    logging.info(line_skip)
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
    for file in file_paths:
        replace_file([file[1], ], [dest_fold, '%s%s' % (ROOT_PATH, file[0])], False, False, False)

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
            shutil.copyfile(path_target, path_backup)
    if len(path) == 2:
        shutil.copyfile(path_source, path_target)

# function to verify if a new version is available
def check_update(vers):
    URL = "https://raw.githubusercontent.com/V0r-T3x/fancygotchi/main/fancygotchi.py"
    response = requests.get(URL)
    lines = str(response.content)
    lines = lines.split('\\n')
    #logging.info(str(response.content))
    for line in lines:
        if '__version__ =' in line:
            online_version = line.split('= ')[-1]
            online_version = online_version[2:-2]
            logging.info(online_version)
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
    logging.info('%s - %s' % (str(upd), online_version))
    return [upd, online_version]


def update():
    #download from github
    custom_plugins = pwnagotchi.config['main']['custom_plugins']
    URL = "https://github.com/V0r-T3x/fancygotchi/archive/refs/heads/main.zip"
    response = requests.get(URL)
    if not custom_plugins[-1] == '/': custom_plugins += '/'
    path_tmp = '%sfancygotchi/tmp/' % (custom_plugins)
    filename = '%s%s' % (path_tmp, URL.split('/')[-1])
    os.system('mkdir %s' % (path_tmp))
    with open(filename,'wb') as output_file:
        output_file.write(response.content)
    shutil.unpack_archive(filename, path_tmp)
    path_unzip = '%sfancygotchi-main/' % (path_tmp)
    replace_file(['fancygotchi.py'], [path_unzip, custom_plugins], False, False, False)
    for root, dirs, files in os.walk('%sfancygotchi/' % (path_unzip)):
        for name in files:
            if not name == "README.md":
                path_update = root
                path_target = '%s%s/%s' % (custom_plugins, root.split('fancygotchi-main/')[-1])
                logging.info('%s ---->%s' % (path_update, path_target))
                replace_file([name], [path_target, path_update], False, False, False)
    os.system('rm -R %s' % (path_tmp))
    dir_path = os.path.dirname(os.path.realpath(__file__))
    for file in FILES_TO_MODIFY:
        logging.info('replace: %s' % (file[1]))
        replace_file([file[1]], ['%s%s' % (ROOT_PATH, file[0]), '%s/fancygotchi/mod/' % (dir_path)], False, False, False, )

class Fancygotchi(plugins.Plugin):
    __name__ = 'Fancygotchi'
    __author__ = '@V0rT3x https://github.com/V0r-T3x'
    __version__ = '2022.07.3'
    __license__ = 'GPL3'
    __description__ = 'A theme manager for the Pwnagotchi'

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
        """
        check_update(self.__version__)
        update()
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
        custom_plugins_path = pwnagotchi.config['main']['custom_plugins']
        ui = pwnagotchi.config['ui']['display']['type']

        # Linking bg image to the web ui
        dir_path = os.path.dirname(os.path.realpath(__file__))
        src = '%s/fancygotchi/img/' % (dir_path)
        dest = '%s/ui/web/static' % (ROOT_PATH)
        #logging.info('[FANCYGOTCHI] ln -s %s %s' % (src, dest))
        if not os.path.exists('%s/img/' % (dest)):
            #logging.info('[FANCYGOTCHI] link for img don\'t exist')
            os.system('ln -s %s %s' % (src, dest))
            #logging.info('[FANCYGOTCHI] link for img created')
        
        # Loop to verify if the backup is here, and if not it backup original files
        # and replace them all with link from plugin folder
        for file in FILES_TO_MODIFY:
            #logging.info('[FANCYGOTCHI] %s%s' % (file[0], file[1]))
            # Loop to verify backup
            #logging.info('[FANCYGOTCHI] %s%s.%s.original' % (ROOT_PATH, file[0], file[1]))

            if not os.path.exists('%s%s.%s.original' % (ROOT_PATH, file[0], file[1])):
                replace_file([file[1]], ['%s%s' % (ROOT_PATH, file[0]), '%s/fancygotchi/mod/' % (dir_path)], True, False, True, 'original')

        # Verification to the enabled display
        if ui == 'lcdhat':
            logging.info('[FANCYGOTCHI] waveshare 1.33" LCD screen')
        elif ui == 'waveshare_v2':
            logging.info('[FANCYGOTCHI] waveshare v.2 E-paper screen')
        elif ui == 'oledhat':
            logging.info('[FANCYGOTCHI] waveshare 1.3" OLED screen')
        elif ui == 'waveshare27inch':
            logging.info('[FANCYGOTCHI] waveshare 2.7" E-paper screen')
        elif ui == 'waveshare144lcd':
            logging.info('[FANCYGOTCHI] waveshare 1.44" LCD screen')
        elif not pwnagotchi.config['ui']['display']['enabled']:
            logging.info('[FANCYGOTCHI] Pwnagotchi headless mode')
        else:
            logging.info('[FANCYGOTCHI] The screen is not compatible with the plugin')
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
        """
        Serves the current theme configuration
        """
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
                    'darkmode': self.config['main']['plugins']['fancygotchi']['darkmode'],
                    'filter_color': self.config['main']['plugins']['fancygotchi']['filter_color'],
                    'hi-res': self.config['main']['plugins']['fancygotchi']['hi-res'],
                    'bg': self.config['main']['plugins']['fancygotchi']['bg'],
                    'bg_image': self.config['main']['plugins']['fancygotchi']['bg_image'],
                    'themes_path': self.config['main']['plugins']['fancygotchi']['themes_path'],
                    'theme': self.config['main']['plugins']['fancygotchi']['theme'],
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
                    # deleting the sym link for the img file
                    dest = '%s/ui/web/static' % (ROOT_PATH)
                    os.system('rm %s' % (dest))

                    #deleting all modified files and place original files in place
                    for file in FILES_TO_MODIFY:
                        shutil.copyfile('%s%s.%s.original' % (ROOT_PATH, file[0], file[1]), '%s%s%s' % (ROOT_PATH, file[0], file[1]))
                        os.system('rm %s' % ('%s%s.%s.original' % (ROOT_PATH, file[0], file[1])))
                    
                    # disable the fancygotchi inside the config.toml 
                    replace_line('/etc/pwnagotchi/config.toml', 'fancygotchi.enabled',['main.plugins.fancygotchi.enabled = false'])
                    # starting new thread to restart pwnagotchi
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
                    #logging.info('%s/fancygotchi/mod/%s/' % (custom_plugins_path, folder["response"]))
                    dest = '%s/fancygotchi/mod/%s/' % (custom_plugins_path, str(folder["response"]))
                    if not os.path.exists(dest):
                        os.system('mkdir %s' % (dest))
                    dev_backup(FILES_TO_MODIFY, dest);
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "dev backup error", 500
            elif path == "check_update":
                try:
                    is_update = check_update(self.__version__)
                    logging.info(is_update[1])
                    upd = '%s,%s' % (is_update[0], is_update[1])
                    return upd
                except Exception as ex:
                    logging.error(ex)
                    return "update check error, check internet connection", 500

            elif path == "update":
                try:
                    update()
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "update error", 500

        abort(404)
