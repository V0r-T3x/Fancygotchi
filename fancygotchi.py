from pwnagotchi.ui.view import View
import pwnagotchi
import pwnagotchi.plugins as plugins
import logging
import traceback
import os
from os import fdopen, remove
import shutil
from shutil import move, copymode
from tempfile import mkstemp
from PIL import Image, ImageDraw, ImageOps

import json
import toml
import pandas as pd
import _thread
from pwnagotchi import restart, plugins
from pwnagotchi.utils import save_config
from flask import abort, render_template_string

#for tests
import pwnagotchi.ui.fonts as fonts

import requests

ROOT_PATH = '/usr/local/lib/python3.7/dist-packages/pwnagotchi'
FANCY_ROOT = os.path.dirname(os.path.realpath(__file__))

FILES_TO_MOD = pd.read_csv('%s/fancygotchi/mod/files.csv' % (FANCY_ROOT))
#for index, value in FILES_TO_MOD.iterrows():
#    logging.warning('%s ---> %s' % (value[0], value[1]))

COMPATIBLE_PLUGINS = [
    'bt-tether',
    'memtemp',
    'clock',
    'display-password',
    'crack_house',
    'pisugar2',
    'pisugar3',
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
        //background-color: rgba(0, 255, 0, 0.5);
        position:absolute;
        //width:100%;
        //height:100%;
        z-index:100;
        border:1px solid lime;
    }
</style>
{% endblock %}

{% block content %}
    <div id="divTop">
        <span><input id="textDevBackup" type="text" placeholder="Backup folder name..."></input></span>
        <span><button id="btnDevBackup" type="button" onclick="dev_backup()">dev_backup fancygotchi</button></span>
        <button id="btnSave" type="button" onclick="saveConfig()">Save theme and restart</button>
        <button id="btnUninstall" type="button" onclick="uninstall()">Uninstall fancygotchi</button>
        Online update<input type=checkbox id="upd_on"></input>
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
            var online = document.getElementById("upd_on").checked;
            if (online == true){
                var ck_upd = "fancygotchi/check_online_update";
                var upd = "fancygotchi/online_update";}
            else {
                var ck_upd = "fancygotchi/check_local_update";
                var upd = "fancygotchi/local_update";}
            alert(ck_upd + " " + upd);
   
            if (confirm("Do you want check for Fancygotchi update?")){
                var json = {"response":"1"};
                sendJSON(ck_upd, json, function(response){
                    if (response) {
                        if (response.status == "200") {
                            is_version = response.responseText.split(',')
                            if (is_version[0] == 'True') {
                                //alert('New fancygotchi update v.' + is_version[1]);
                                if (confirm("Do you want update Fancygotchi to v." + is_version[1] + "?")){
                                    var json = {"response":"1"};
                                    sendJSON(upd, json, function(response){
                                        if (response) {
                                            if (response.status == "200"){
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
            bg_img.style.backgroundImage = "url('/img/" + theme_array[5][1] + "')";
            wrap_img.style.width = (theme_array[2][1] + 100) + 'px';
            wrap_img.style.height = (theme_array[3][1] + 100) + 'px';
            bg_img.style.width = theme_array[2][1] + 'px';
            bg_img.style.height = theme_array[3][1] + 'px';
            filter_color.style.width = theme_array[2][1] + 'px';
            filter_color.style.height = theme_array[3][1] + 'px';
                
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
    for index, value in file_paths.iterrows():
        path = value[0]
        file = value[1]
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
            logging.warning('%s ----> %s' % (path_target, path_backup))
            shutil.copyfile(path_target, path_backup)
    if len(path) == 2:
        logging.warning('%s ----> %s' % (path_source, path_target))
        shutil.copyfile(path_source, path_target)

# function to verify if a new version is available
def check_update(vers, online):
    #logging.warning(("check update, online: %s") % (online))
    #logging.warning(FANCY_ROOT)
    if online:
        URL = "https://raw.githubusercontent.com/V0r-T3x/fancygotchi/main/fancygotchi.py"
        response = requests.get(URL)
        lines = str(response.content)
        lines = lines.split('\\n')
        count = 0
        for line in lines:
            if '__version__ =' in line:
                count += 1
                if count == 2:
                    online_version = line.split('= ')[-1]
                    online_version = online_version[2:-2]
    elif not online:
        URL = '%s/fancygotchi/update/fancygotchi.py' % (FANCY_ROOT)
        with open(URL, 'r') as f:
            lines = f.read()
        lines = lines.splitlines()
        count = 0
        for line in lines:
            if '__version__ =' in line:
                count += 1
                if count == 2:
                    online_version = line.split('= ')[-1]
                    online_version = online_version[1:-1]

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
        
    logging.warning('%s/fancygotchi.py ----> %s/fancygotchi.py' % (path_upd, FANCY_ROOT))
    replace_file(['fancygotchi.py'], [path_upd, FANCY_ROOT], False, False, False)
 
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
            if not name == "README.md" or name == "readme.md":
                src_file = os.path.join(root, name)
                #logging.warning(src_file)
                dst_file = os.path.join(FANCY_ROOT, root.split('fancygotchi-main/')[-1], name)
                #logging.warning(dst_file)
                logging.warning('%s ---->%s' % (src_file, dst_file))
                replace_file([name], [dst_file, src_file], False, False, False)
    if online:
        logging.warning('removing the update temporary folder: %s' % (path_upd_src))
        os.system('rm -R %s' % (path_upd_src))

def uninstall(soft=False):
    # deleting the sym link for the img file
    dest = '%s/ui/web/static/img/' % (ROOT_PATH)
    logging.warning(dest)
    os.system('rm %s' % (dest))
    
    for index, value in FILES_TO_MOD.iterrows():
        path = value[0]
        file = value[1]
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
    __version__ = '2023.03.1'
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
#<        logging.info("[FANCYGOTCHI] Beginning Fancygotchi load")
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
        elif ui == 'oledhat':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare 1.3" OLED screen')
        elif ui == 'waveshare27inch':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare 2.7" E-paper screen')
        elif ui == 'waveshare144lcd':
            compatible = 1
            logging.info('[FANCYGOTCHI] waveshare 1.44" LCD screen')
        elif ui == 'displayhatmini':
            compatible = 1
            logging.info('[FANCYGOTCHI] pimoroni 2" LCD Display Hat Mini screen')

        elif not pwnagotchi.config['ui']['display']['enabled']:
            compatible = 1
            logging.info('[FANCYGOTCHI] Pwnagotchi headless mode')
        else:
            logging.warning('[FANCYGOTCHI] The screen is not compatible with the plugin')

        # If the initial screen isn't compatible the mod will not install
        logging.info('[FANCYGOTCHI] compatible: %s' % (compatible))
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
        for index, value in FILES_TO_MOD.iterrows():
            path = value[0]
            file = value[1]
            #logging.warning(path)
            #logging.warning(file)
            if not path[0] == '/':
                #logging.warning(path[0])
                dest_path = '%s/%s' % (ROOT_PATH, path)
                #src_path = '%s/fancygotchi/mod%s' % (FANCY_ROOT, path)
            else: 
                dest_path = path
            #logging.info('%s.%s.original' % (path, file))
            if not os.path.exists('%s.%s.original' % (path, file)):
                #logging.warning('%s.%s.original' % (path, file))
                replace_file([file], [dest_path, '%s/fancygotchi/mod/%s' % (FANCY_ROOT, path)], True, False, True, 'original')
            
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
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "update error", 500
                    
            elif path == "check_local_update":
                try:
                    is_update = check_update(self.__version__, False)
                    logging.info(is_update[1])
                    upd = '%s,%s' % (is_update[0], is_update[1])
                    return upd
                except Exception as ex:
                    logging.error(ex)
                    return "update check error, check internet connection", 500

            elif path == "local_update":
                try:
                    update(False)
                    return "success"
                except Exception as ex:
                    logging.error(ex)
                    return "update error", 500


        abort(404)
