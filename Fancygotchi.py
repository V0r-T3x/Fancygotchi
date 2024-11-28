import argparse
import asyncio
import copy
import glob
import importlib.util
import json
import logging
import math
import numpy as np
import os
import random
import re
import requests
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import toml
import traceback
import zipfile

from io import BytesIO
from multiprocessing.connection import Client, Listener
from os import system
from shutil import copy2, copyfile, copytree
from textwrap import TextWrapper
from toml import dump, load
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageSequence
from flask import abort, jsonify, make_response, render_template_string, send_file

import pwnagotchi
import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi import utils
from pwnagotchi.plugins import toggle_plugin
from pwnagotchi.ui import display
from pwnagotchi.ui.hw import display_for
from pwnagotchi.utils import load_config, merge_config, save_config

V0RT3X_REPO = "https://github.com/V0r-T3x"
FANCY_REPO = os.path.join(V0RT3X_REPO, "Fancygotchi")
THEMES_REPO = "https://api.github.com/repos/V0r-T3x/Fancygotchi_themes/contents/fancygotchi_2.0/themes"


LOGO = """░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒░░░░░░▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓████▓▓▓▓▓▓▓▓▓████████▓▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓███████▓▓▓▓▓▓▓▓██████████▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█▓█████▓▓▓▓▓▓▓▓▓▓▓██████████▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██████████▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓█▓▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓███████████▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░█▓▓▓█▓▒▒▒▒▓▓▓▓▓▓▓▓▓█████████████▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░▒▓▓▓█▓▓▓█▓▓██████████████████████████████▓▓▓▓▓▓▓▒░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░███████████████████████████████████████████████████▓░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░████████████████████████████████████████████████████░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░▒████████▓▓▓▓▓▓▓▓██████████████████████████████████▒░░░░▒▒▒▒░░░░░░░░░░
░░░░░░░░░▓▓▒░░░░░░░░░░▓█████▓▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓███████▓░░░░░░▓▓▓▓▓▓▓▓▓░░░░░
░░░░░░░░▒▒▒▓▒░░░░░░░░░░░▒▓██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓██▓▒░░░░░░░░░█▓▓▓▓▓█▓░░░░░░
░░░░░░░░▓░░▒▒▓▒░░░░░░░░░░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓░░░░░░░░░░░▒▒▓▓▓▓▓█▒░░░░░░
░░░░░░░▓▒▒▒▒▒▓▓▒░░░░░░░░░░░▓▒▒▓████▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓█████▓▓▓▓░░░░░░░░░░░▒▒▒▒▒▒▓▓░░░░░░░
░░░░░░░▒▒░░░░▒▒▓░░░░░░░░░░░▓▒▒▒██▓▓████▓▒▒▒▒▒▒▒▒▒▒▓▓████▓███▓▓▓▒░░░░░░░░░░▒▓▓▓▓▓▒▓▒░░░░░░░
░░░░░░░░▓░░░░░▒▓░░░░░░░░░░░░▓▒▒▒███████▓▒▒▒▒▒▒▒▒▒▒▒▓███████▓▓▓▓░░░░░░░░░░░░░▓▓██▓▓░░░░░░░░
░░░░░░░▒▓▒░░░░▓▓▒▒▒░░░░░░░░░▒▓▒▒▒▓███▓▒▒▓▓▓▓▒▒▒▓▓▓▒▒▒▓████▓▓▓▓░░░░░░░░░░░▒▒▓▓▓█░░░░░░░░░░░
░░░░░░░▒▓▓▒▓▒▒▓▓▓█▓▓░░░░░░░░░░▓▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▒▒▒▒▒▒▒▒▒▓▓▓▓░░░░░░░░░░░▓▒▒█▓▓▓░░░░░░░░░░░
░░░░░░░░▒█▒▓▓▓▓▓███▓▒░░░░░░░░▒▓█▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓██▒░░░░░░░░░░░█▓▓█▓█▒▒▒░░░░░░░░░
░░░░░░░░░▓░▓▓▓▒▒▓██▓▓▓▒░░░░▒▓███▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓████▓▒░░░░░░░░▓▓██████▓▒▓░░░░░░░░
░░░░░░░░░▒▓▒▒▒▓▓████▓▓▓▓▒▒▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓███▓▒▒░▒▒▓▒▒▓██████▓▒▓░░░░░░░░
░░░░░░░░░░░░░▒████▓██▓▓▓▓▓▓▓▒▒▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▓▒▒▒▒▒▒▒▒▒▒▓██████▓▒▓▒░░░░░░░░
░░░░░░░░░░░░░░▒████▓▒▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓█████▓▒▒░░░░░░░░░░
░░░░░░░░░▒██░░░▓█████▓▒▒▒▒▒▒▒▒▒▒▒▒▓▓█▓▒▒▒▒▒▒▓█▓▓▒▒▒▒▒▒▓█▓▓▒▒▒▒▒▒▒▒▒▒▒▒▓███▓█▓▒▒░░░░░░░░░░░
░░░░░░░░▒██░░░░▒▒████████▓▓▓▓▓▓██████▓▒▒▒▒▒▓█████▓▒▒▒▒▒████████▓▓▓▓▓█████░▒██▓██▓░░░░░░░░░
░░░░░░░░▓██░░░▒░░▒█████████▓▓████████▓▒▒▒▒▓███████▓▒▒▒▒████████████████▓░░░▒▒░▒██▓░░░░░░░░
░░░░░░░░▒███▒░░░▒████▒░██▓███▓███████▒▒▒▒▓█████████▓▒▒▒▒████████▓██▓██▓░░░░░░░▒███░░░░░░░░
░░░░░░░░░▒███████████▒▒█▓▓██▓▓▓█████▒▒▒▒▒███████████▓▒▒▒▒██████▓▓█████▓▒░░░░░░▓██▓░░░░░░░░
░░░░░░░░░░░▒▓▓██████▓▓███▓███▓▒▒▓▓▒▒▒▒▒▓██████████████▒▒▒▒▒▓▓▒▒▒██████▓▓▓▒▒▒▓▓███▒░░░░░░░░
░░░░░░░░░░░░░▓███████████▓▓████▓▓▒▒▒▓▓███████▓▒▓██▓█████▓▒▒▒▒▒▓████████████████▓░░░░░░░░░░
░░░░░░░░░░░░░░▓███████████▓███████████████▒░░░░░░░▓▓██████████████▓█████████▓▒░░░░░░░░░░░░
░░░░░░░░░░░░░░░▒▓▓██████▓░░▒█████████████▒░░░░░░░░░▓█▓███████████▒░░▓▓█▓▓▓▓▒░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░▒░░░░░░░▒▓██▓██▓███▓▒░░░░░░░░░░░░▓██▓█████▓▒░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒▒▒░░░░░░░░░░░░░░░░░░░░▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"""

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
    body {
        position: relative;
        min-height: 100vh;
    }
    #wrap {
        width: 100%;
        float:left;
        padding: 10px;
        padding-bottom: 50px;
        align-items: center;
        justify-content: center;
        flex-grow: 1;
        display: flex;
        border-bottom: 1px solid black;
        flex-direction: column; /* Display tabs menu and content vertically */}
    #tabs {
        border-bottom: 1px solid black;
        text-align: center;}
    .theme {
        width: 100%;
        margin-bottom: 20px;}
    .theme-columns {
        display: flex;}
    .select,
    .theme-description {
        flex: 1;
        margin-right: 20px;}
    #uploader {
        margin-top: 20px;}
    #tabs{
        width: 100%}
    #config_content {
        text-align: left;}
    label {
        text-align: center;}
    .ui-image {
        width: 100%;
        max-width: 600px; 
        left: 50%;
        transform: translateX(-50%);
        position: relative;
        background-color: black;
    }
    .config-box {
        max-width: 100%;
        width: 600px;
        max-height: 300px;
        resize: both; /* allow resizing in both directions */
        overflow: auto;
        padding: 10px;
        border: 1px solid #ccc;}
    #fancygotchi {
        font-size: 10px;
        text-align: center;
        white-space: pre; /* Preserve the spaces in ASCII art */
        font-family: monospace;
    }
    #sticky-button {
        max-width: 150px;
        position: fixed;
        bottom: 15px; /* Distance from the bottom of the screen */
        left: 50%; /* Center the button horizontally */
        transform: translateX(-50%); /* Adjust the centering */
        cursor: pointer;
        z-index: 1000; /* Ensure it stays above other elements */
    }
    .preserve-line-breaks {
        white-space: pre-wrap;
    }
    .glitch-line {
        display: inline-block;
        position: relative;
        animation: glitch 0.3s ease-in-out forwards; /* Slower animation duration */
    }
    /* Style the button */
    .scroll-to-top-btn {
        max-width: 100px;
        position: fixed;
        bottom: 00px;
        right: 40px;
        z-index: 100; /* Ensure it's on top of other elements */
        cursor: pointer;
        display: none; /* Initially hidden */
        font-size: 24px; /* Make the arrow bigger */
    }
    #theNet{
        display: none;
        position: absolute;
        bottom: 0px;
        font-size: 9px;
        right: 25px;
        padding:10px;
        cursor: context-menu;
        -webkit-touch-callout: none; /* iOS Safari */
            -webkit-user-select: none; /* Safari */
                -khtml-user-select: none; /* Konqueror HTML */
                    -moz-user-select: none; /* Old versions of Firefox */
                        -ms-user-select: none; /* Internet Explorer/Edge */
                            user-select: none; /* Non-prefixed version, currently supported by Chrome, Edge, Opera and Firefox */
    }

    /* Show button when scrolling */
    .scroll-to-top-btn.show {
        display: block;
    }
    #footer {
        backkground-color: black;
        position: fixed;
        bottom: 0;
        width: 400px;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 1000;
        text-align: center;
    }
    #logo {
        #left: 50%;
        #transform: translate(-50%, -50%);
        margin-right: 40px;
        margin-left: 40px;
    }
    .dev {
        #display: none;
    }

    @keyframes glitch {
        0% {
            transform: translateX(0);
        }
        20% {
            transform: translateX(-2px); /* Smaller shift */
        }
        40% {
            transform: translateX(2px); /* Smaller shift */
        }
        60% {
            transform: translateX(-1px); /* Smaller shift */
        }
        80% {
            transform: translateX(1px); /* Smaller shift */
        }
        100% {
            transform: translateX(0);
        }
    }

    /* Main container with 3 sections */
    .container {
    display: flex;
    width: 100%;
    max-width: 1000px; /* adjust as needed */
    margin: 0 auto;
    align-items: center;
    gap: 10px;
    }

    /* Left section centered within its area */
    .left-container {
    display: flex;
    justify-content: center;
    width: 33.33%;
    }
    .left {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    }

    /* Center element truly centered */
    .center-container {
    display: flex;
    justify-content: center;
    width: 33.33%;
    }
    .center img {
    max-width: 100%;
    height: auto;
    }

    /* Right section centered within its area */
    .right-container {
    display: flex;
    justify-content: center;
    width: 33.33%;
    }
    .right img {
    max-width: 100%;
    height: auto;
    }

    /* Responsive stacking for small screens */
    @media (max-width: 600px) {
    .container {
        flex-direction: column;
        align-items: center;
    }
    .left-container, .center-container, .right-container {
        width: auto;
        margin-bottom: 10px;
    }

    /* Style individual arrow buttons */
    .arrow-button {
        font-weight: bold;
        font-size: 24px; /* Makes the arrow icon larger */
    }
    #download_window {
        display: none;
    }
    #loading-spinner{
    
    }
</style>
{% endblock %}
{% block content %}
    <div id="editor">
        
        <div id="main" data-role="navbar">
            <ul>
                <li>
                    <form class="action" method="post" action="/shutdown" onsubmit="return confirm('this will halt the unit, continue?');">
                        <input type="submit" class="button ui-btn ui-corner-all" value="Shutdown"/>
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    </form>
                </li>
                <li>
                    <form class="action" method="post" action="/reboot" onsubmit="return confirm('this will reboot the unit, continue?');">
                        <input type="submit" class="button ui-btn ui-corner-all" value="Reboot"/>
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    </form>
                </li>

                <li>
                    <form class="action" method="post" action="/restart" onsubmit="return confirm('This will restart the service in Manu mode, continue?');">
                        <input type="submit" class="button ui-btn ui-corner-all" value="Restart in Manu mode"/>
                        <input type="hidden" name="mode" value="MANU"/>
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    </form>
                </li>
                <li>
                    <form class="action" method="post" action="/restart" onsubmit="return confirm('This will restart the service in Auto mode, continue?');">
                        <input type="submit" class="button ui-btn ui-corner-all" value="Restart in Auto mode"/>
                        <input type="hidden" name="mode" value="AUTO"/>
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                    </form>
                </li>
            </ul>
        </div>
        <div id="display" data-role="navbar" class="dev">
            <ul>
                <li>
                    <button id="display_hijack" onclick="display_hijack()">Second hardware display</button>
                </li>
                <li>
                    <button id="display_pwny" onclick="display_pwny()">Pwnagotchi hardware display</button>
                </li>
            </ul>
            <ul>
                <li>
                    <button id="display_next" onclick="display_next()">Next second screen mode</button>
                </li>
                <li>
                    <button id="display_previous" onclick="display_previous()">Previous second screen mode</button>
                </li>
                <li>
                    <button id="screen_saver_next" onclick="screen_saver_next()">Next screen saver</button>
                </li>
                <li>
                    <button id="screen_saver_previous" onclick="screen_saver_previous()">Previous screen saver</button>
                </li>
            </ul>
        </div>
        <div class="container">
            <!-- Left Div with 3x3 grid -->
            <div class="left-container">
                <div class="left">
                    <div><button id="toggle" onclick="navigate('toggle')">Toggle</button></div>
                    <div><button id="up" onclick="navigate('up')" class="arrow-button">↑</button></div>
                    <div><button id="stealth" onclick="stealth()">Stealth</button></div>
                    <div><button id="left" onclick="navigate('left')" class="arrow-button">←</button></div>
                    <div><button id="select" onclick="navigate('select')">Select</button></div>
                    <div><button id="right" onclick="navigate('right')" class="arrow-button">→</button></div>
                    <div></div>
                    <div><button id="down" onclick="navigate('down')" class="arrow-button">↓</button></div>
                    <div></div>
                </div>
            </div>

            <!-- Center Image -->
            <div class="center-container">
                <div class="center">
                    <img class="ui-image pixelated" src="/ui" id="ui" style="width: 400px" />
                </div>
            </div>

            <!-- Right Image -->
            <div class="right-container">
                <div class="right">
                    <img class="ui-image pixelated" src="/plugins/Fancygotchi/ui2" id="ui2" style="width: 400px" />
                </div>
            </div>
        </div>

        <div id="wrap" data-role="tabs">
            <div id="tabs" data-role="navbar">
                <ul>
                    <li class="ui-btn-active"><a href="#theme" data-theme="a" data-ajax="false">Theme manager</a></li>
                    <li class=""><a href="#theme_downloader" data-theme="a" data-ajax="false">Theme downloader</a></li>
                    <li class=""><a href="#config" data-theme="a" data-ajax="false">Configuration</a></li>
                    <li class=""><a href="#theme_editor" data-theme="a" data-ajax="false">Theme editor</a></li>
                </ul>
            </div>
            <div id="theme" class="ui-content theme">
                <div id="theme-columns" class="row theme-columns">
                    <div id="select" class="column select">
                        <label for="theme-selector">Select a theme:</label>
                        <select id="theme-selector">
                            <option value="Default"{% if default_theme == '' %}selected{% endif %}>Default</option>
                            {% for theme in themes %}
                            <option value="{{ theme }}"{% if default_theme == theme %}selected{% endif %}>{{ theme }}</option>
                            {% endfor %}
                        </select>
                        <br>
                        <label for="orientation-selector">Select an orientation:</label>
                        <select id="orientation-selector">
                            <option value=0{% if rotation == 0 %} selected{% endif %}>0</option>
                            <option value=90{% if rotation == 90 %} selected{% endif %}>90</option>
                            <option value=180{% if rotation == 180 %} selected{% endif %}>180</option>
                            <option value=270{% if rotation == 270 %} selected{% endif %}>270</option>
                        </select>
                        <button id="select-theme-button" onclick="theme_select()">Select Theme</button>
                        <button id="copy-theme-button" onclick="copyTheme()">Copy Theme</button>
                        <button id="rename-theme-button" onclick="renameTheme()">Rename Theme</button>

                        <button id="select-theme-button" onclick="theme_delete()">Delete Theme</button>
                        <button id="export-theme-button" onclick="theme_export()">Export Theme</button>
                        <div id="uploader" class="ui-content">
                            <form id="uploadForm" enctype="multipart/form-data">
                                <input type="file" name="zipFile" id="zipFile">
                                <input type="submit" value="Upload Theme Zip" onclick="theme_upload(event)">
                            </form>
                            <div id="message"></div>
                        </div>
                        <div id="create-theme">
                            <h3>Create New Theme</h3>
                            <input type="text" id="new-theme-name" placeholder="Enter new theme name">
                            <label><input type="checkbox" id="use-resolution"> Use Resolution System</label>
                            <label><input type="checkbox" id="use-orientation"> Use Orientation System</label>
                            <button id="create-theme-button" onclick="createNewTheme()">Create Theme</button>
                        </div>
                    </div>
                    <div id="theme-description" class="column theme-description">
                        <h3>Theme Description</h3>
                        <div id="theme-description-content"></div>
                        <img id="screenshot" src="/img/screenshot.png" onerror="this.onerror=null; this.src='/screenshots/screenshot.png';"></img>
                        </br><input type="checkbox" name="fancyserver" data-on-text="Fancyserver" data-off-text="Fancyserver" data-role="flipswitch" id="fancyserver-selector" onchange="fancyserver()" {% if fancyserver %}checked{% endif %} data-wrapper-class="custom-size-flipswitch"></input>
                    </div>
                </div>
            </div>
            <div id="theme_downloader" class="ui-content theme">
                <div id="download_list_refresh">
                    <p align="center">
                        <button id="select-theme-downloader-btn" onclick="loadThemeRepo()">Load theme list</button>
                    </p>
                </div>
                <div id="loading-spinner" style="display:none;"><p align="center">Loading...</p></div>
                <div id="download_window" style="display:none;">
                    <div id="theme-downloader-columns" class="row theme-columns">
                        <div id="downloader-select" class="column select">
                            <label for="theme-downloader-selector">Select a theme:</label>
                            <select id="theme-downloader-selector">
                                <!-- Themes will be dynamically populated here -->
                            </select>
                            <br>
                            <button id="select-theme-downloader-button" onclick="theme_download_select()">Select Theme</button>
                        </div>
                        <div id="theme-downloader-description" class="column theme-description">
                            <h3>Theme Description</h3>
                            <div id="theme-downloader-description-content"><p>No description available</p></div>
                            <img id="repo_screenshot" src="/screenshots/screenshot.png" onerror="this.onerror=null; this.src='/screenshots/screenshot.png';"></img>
                        </div>
                    </div>
                </div>
            </div>
            <div id="config" class="ui-content">
                <h2>No configuration for the default theme</h2> <!-- Updated dynamically -->
                <div id="hidden">
                    <button onclick="saveConfig()" id="sticky-button">Save Configuration</button>
                    <h3>Configuration editor</h3>
                    <h4>Config Path</h4> <!-- Updated dynamically -->
                    <div id="config_content"></div> <!-- Config data inserted here dynamically -->
                    <h3>CSS editor</h3>
                    <h4>CSS Path</h4>  <!-- css path inserted here dynamically -->
                    <div contenteditable="true" id="CSS" class="config-box"></div> <!-- css content inserted here dynamically -->
                    <h3>Info editor</h3>
                    <h4>Info Path</h4>  <!-- css path inserted here dynamically -->
                    <div contenteditable="true" id="Info" class="config-box"></div> <!-- Info content inserted here dynamically -->
                </div>
                <button onclick="resetCSS()">Reset Pwnagotchi core CSS</button>
            </div>

            <div id="theme_editor" class="ui-content">
                
                <div id="fancygotchi">
                    <h2>Theme editor</h2>
                    <div id="theme_editor_content">
                        <h2>Coming soon !</h2>
                        <h2>If you like the project feel free to contribute !</h2>
                        <h2><a href='{{fancy_repo}}'>Fancygotchi</a> is made with ❤ by <a href='https://linktr.ee/v0r_t3x'>V0rT3x</a></h2>
                    </div>
                    <div id="logo">
                        <pre>
{% for line in logo.splitlines() %}<span>{{ line }}</span>
{% endfor %}
                        </pre>
                    </div>
                </div>
                <div id="theNet"><a onclick="theNet()">π</a></div>
            </div>
        </div>
        
        <div id="footer">
            <a href='{{fancy_repo}}'>Fancygotchi</a> {{ version }} made with ❤ by <a href='https://linktr.ee/v0r_t3x'>{{ author }}</a>
        </div>
        
    </div>
    <div data-role="popup" id="delete-dialog" data-overlay-theme="b" data-theme="b" data-dismissible="false" style="max-width:400px;">
        <div role="main" class="ui-content">
            <h3 class="ui-title">Confirm Deletion</h3>
            <p>Are you sure you want to delete the selected theme?</p>
            <a href="#" class="ui-btn ui-corner-all ui-shadow ui-btn-inline ui-btn-b" data-rel="back">Cancel</a>
            <a href="#" id="confirm-delete" class="ui-btn ui-corner-all ui-shadow ui-btn-inline ui-btn-b" data-rel="back">Delete</a>
        </div>
    </div>
    <button id="scrollToTopBtn" class="scroll-to-top-btn">&#x25B2;</button>
{% endblock %}
{% block script %}
theme_info("{{name}}");
loadConfig(0, "{{name}}");

var scrollToTopBtn = document.getElementById("scrollToTopBtn");

function theNet() {
    var div = document.querySelector(".dev");
    var logo = document.querySelector("#logo");

    if (!div || !logo) {
        console.error('Element not found: .dev or #logo');
        return;
    }

    var computedColor = window.getComputedStyle(logo).color;
    console.log(computedColor)

    function rgbToColor(rgb) {
        return rgb.replace(/\s+/g, '').toLowerCase();
    }

    var limeColor = rgbToColor("rgb(0, 255, 0)"); 

    if (div.style.display === "none" || div.style.display === "") {
        if (rgbToColor(computedColor) === limeColor) {
            logo.style.color = "red"; 
        } else {
            logo.style.color = "lime"; 
        }

        glitchEffect(true);
        div.style.display = "block";
        logo.style.backgroundColor = "black";
    } else {
        div.style.display = "none";
        logo.style.color = ""; 
        logo.style.backgroundColor = "";
    }
}

window.onload = function() {
    var image = document.getElementById("ui");
    var image2 = document.getElementById("ui2");
    function updateImage() {
        image.src = image.src.split("?")[0] + "?" + new Date().getTime();
        image2.src = image2.src.split("?")[0] + "?" + new Date().getTime();
    }
    setInterval(updateImage, {{webui_fps}});
}

window.onscroll = function() {
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        scrollToTopBtn.classList.add("show");
    } else {
        scrollToTopBtn.classList.remove("show");
    }
};

scrollToTopBtn.addEventListener("click", function() {
    window.scrollTo({top: 0, behavior: 'smooth'});
});

function active_theme(callback) {
    loadJSON("Fancygotchi/active_theme", function(response) {
        callback(response.theme);
    });
}

function resetCSS() {
    var json = {"reset_css": true};
    sendJSON("Fancygotchi/reset_css", json, function(response) {
        console.log("CSS reset successful!");
        alert("CSS reset successful!");
    });
}

function theme_select() {
    var theme = document.getElementById("theme-selector").value;
    var rotation = document.getElementById("orientation-selector").value;
    
    var json = {"theme": theme, "rotation": rotation};
    sendJSON("Fancygotchi/theme_select", json, function(response) {
        loadConfig(1, theme);
    }); 
}

function fancyserver(){
    var fancyserver = document.getElementById("fancyserver-selector").checked;
    console.log(fancyserver);
    var json = {"fancyserver": fancyserver};
    sendJSON("Fancygotchi/fancyserver", json);
}

function loadConfig(a, theme) {
    if (a == 1) {
        alert(theme + ' selected');
    }
    if (theme == "Default") {
        document.querySelector("#config h2").innerText = "No configuration for the default theme";
        document.getElementById("hidden").style.visibility = "hidden";
        document.getElementById("hidden").style.display = "none";
    } else {
        document.getElementById("hidden").style.visibility = "visible";
        document.getElementById("hidden").style.display = "inline-block";
    }
    loadJSON("Fancygotchi/load_config", function(response) {
        updateConfigSection(response);
    });
}

function escapeHtml(text) {
    return text
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function updateConfigSection(data) {
    populateConfig(data.config)
    if (data.name == "Default"  || data.name == "") {
        document.querySelector("#config h2").innerText = "No configuration for the default theme";

    } else {
        document.querySelector("#config h2").innerText = "Configuration of " + data.name;

    }
    document.querySelector("#config h4:nth-of-type(1)").innerText = data.cfg_path;
    document.querySelector("#config h4:nth-of-type(2)").innerText = data.css_path;
    var cssContent = document.getElementById("CSS");
    cssContent.innerHTML = '<div class="preserve-line-breaks">' + escapeHtml(data.css) + '</div>';
    document.querySelector("#config h4:nth-of-type(3)").innerText = data.info_path;
    var infoContent = document.getElementById("Info");
    infoContent.innerHTML = '<div class="preserve-line-breaks">' + escapeHtml(data.info) + '</div>';
}

function populateConfig(config) {
    var configContent = $('#config_content');
    configContent.empty();
    var table = jsonToTable(flattenJson(config));
    configContent.append(table);
}

function jsonToTable(json) {
  var table = document.createElement("table");
  table.id = "tableOptions";

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
  Object.keys(json).forEach(function(key) {
    tr = table.insertRow();
    divDelBtn = document.createElement("div");
    divDelBtn.className = "del_btn_wrapper";
    td = document.createElement("td");
    td.setAttribute("data-label", "");
    if (!key.startsWith("theme.options")) {
      btnDel = document.createElement("Button");
      btnDel.innerHTML = "X";
      btnDel.setAttribute("data-key", key);
      btnDel.onclick = function(){ delRow(this);};
      btnDel.className = "remove";
      divDelBtn.appendChild(btnDel);
      td.appendChild(divDelBtn);
    }
    tr.appendChild(td);
    td = document.createElement("td");
    td.setAttribute("data-label", "Option");
    td.innerHTML = key;
    tr.appendChild(td);
    td = document.createElement("td");
    td.setAttribute("data-label", "Value");
    if(typeof(json[key])==='boolean'){
      var input = document.createElement("select");
      input.setAttribute("id", "boolSelect");
      var tvalue = document.createElement("option");
      tvalue.setAttribute("value", "true");
      var ttext = document.createTextNode("True")
      tvalue.appendChild(ttext);
      var fvalue = document.createElement("option");
      fvalue.setAttribute("value", "false");
      var ftext = document.createTextNode("False");
      fvalue.appendChild(ftext);
      input.appendChild(tvalue);
      input.appendChild(fvalue);
      input.value = json[key];
      td.appendChild(input);
    } else {
      var input = document.createElement("input");
      if(Array.isArray(json[key])) {
        input.type = 'text';
        input.value = '[' + json[key].join(', ') + ']';
      } else {
        input.type = typeof(json[key]);
        input.value = json[key];
      }
      td.appendChild(input);
    }
    tr.appendChild(td);
  });

  var newTr = table.insertRow();
  var newTd = newTr.insertCell();
  newTd.setAttribute("data-label", "");
  var addButton = document.createElement("button");
  addButton.innerHTML = "+";
  addButton.onclick = function() {
    var newRow = table.insertRow();
    var newTd = newRow.insertCell();
    var delButton = document.createElement("button");
    delButton.innerHTML = "X";
    delButton.onclick = function() {
      this.parentNode.parentNode.remove();
    };
    newTd.appendChild(delButton);
    var newKeyCell = newRow.insertCell();
    var newKeyInput = document.createElement("input");
    newKeyInput.type = "text";
    newKeyInput.placeholder = "New Key";
    newKeyCell.appendChild(newKeyInput);

    var newValueCell = newRow.insertCell();
    var newValueInput = document.createElement("input");
    newValueInput.type = "text";
    newValueInput.placeholder = "New Value";
    newValueCell.appendChild(newValueInput);
  };
  newTd.appendChild(addButton);
  newTr.appendChild(newTd);
  newTr.appendChild(document.createElement("td"));

  return table;
}
function delRow(btn) {
    var key = btn.getAttribute("data-key");
    var tr = btn.closest("tr");
    if (tr && key) {
        tr.parentNode.removeChild(tr);
    }
}

function saveConfig() {
    var config = document.getElementById("tableOptions");
    var css = document.getElementById("CSS").textContent;
    var info = document.getElementById("Info").textContent;

    console.log(info)
    console.log(css)

    var data = {
        config: tableToJson(config),
        css: css,
        info: info
    };
    sendJSON("Fancygotchi/save_config", data, function(response) {
        if (response.status == "200") {
            alert("Config got updated");
        } else {
            alert("Error while updating the config (err-code: " + response.status + ")");
        }
    });
    active_theme(function(activeTheme) {
        loadConfig(0, activeTheme)
        theme_info(activeTheme)
    });
}

function tableToJson(table) {
  var rows = table.getElementsByTagName("tr");
  var i, td, key, value;
  var json = {};

  for (i = 0; i < rows.length; i++) {
    td = rows[i].getElementsByTagName("td");
    if (td.length == 3) {
      key = td[1].textContent || td[1].innerText;
      console.log(td[1].textContent || td[1].innerText);
      var input = td[2].getElementsByTagName("input");
      var select = td[2].getElementsByTagName("select");
      console.log(key);

      if (input && input.length > 0) {
        if (input[0].type == "text") {
          const inputValue = input[0].value.trim();
          if (inputValue === "") {
            value = ""; 
          } else if (inputValue.startsWith("[") && inputValue.endsWith("]")) {
            try {
              value = JSON.parse(inputValue); 
            } catch (e) {
              console.error('Invalid JSON array:', inputValue);
              value = inputValue;
            }
          } else if (inputValue === 'true' || inputValue === 'false') {
            value = inputValue === 'true'; 
          } else if (!isNaN(inputValue)) {
            value = parseInt(inputValue, 10); 
          } else {
            value = inputValue;
          }
        } else if (input[0].type == "number") {
          value = Number(input[0].value); 
        }
      } else if (select && select.length > 0) {
        value = select[0].options[select[0].selectedIndex].value === 'true';
      }

      var keyParts = key.split('.');
      var currentObj = json;
      for (var j = 0; j < keyParts.length - 1; j++) {
        if (!currentObj[keyParts[j]]) {
          currentObj[keyParts[j]] = {}; 
        }
        currentObj = currentObj[keyParts[j]];
      }
      currentObj[keyParts[keyParts.length - 1]] = value;
    }
  }

  var newRows = document.querySelectorAll("tr input[type='text'][placeholder='New Key']");
  newRows.forEach(function(newKeyInput) {
    var newValueInput = newKeyInput.closest("tr").querySelector("input[placeholder='New Value']");
    var newKey = newKeyInput.value.trim();
    var newValue = newValueInput.value.trim();

    
  if (newKey) {
    if (newValue === "") {
      newValue = "";
    } else if (newValue.startsWith("[") && newValue.endsWith("]")) {
      try {
        newValue = JSON.parse(newValue);
      } catch (e) {
        console.error('Invalid JSON array:', newValue);
        newValue = newValue;
      }
    } else if (newValue === 'true' || newValue === 'false') {
      newValue = newValue === 'true';
    } else if (!isNaN(newValue)) {
      newValue = parseFloat(newValue);
    } else {
      newValue = newValue;
    }

      var newKeyParts = newKey.split('.');
      var currentNewObj = json;
        console.log(newKeyParts)
      for (var k = 0; k < newKeyParts.length - 1; k++) {
        if (!currentNewObj[newKeyParts[k]]) {
          currentNewObj[newKeyParts[k]] = {};
        }
        currentNewObj = currentNewObj[newKeyParts[k]];
      }
      currentNewObj[newKeyParts[newKeyParts.length - 1]] = newValue;
    }
  });

  return unFlattenJson(json);
}

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

function createNewTheme() {
    var themeName = document.getElementById("new-theme-name").value;
    var useResolution = document.getElementById("use-resolution").checked;
    var useOrientation = document.getElementById("use-orientation").checked;
    if (!themeName) {
        alert("Please enter a theme name");
        return;
    }
    var json = {
        "theme_name": themeName,
        "use_resolution": useResolution,
        "use_orientation": useOrientation
    };
    sendJSON("Fancygotchi/create_theme", json, function(response) {
        if (response.status == 200) {
            alert("Theme created successfully");
            theme_list();
        } else {
            alert("Error creating theme: " + response.responseText);
        }
    });
}

function copyTheme() {
    var theme = document.getElementById("theme-selector").value;
    if (theme != "Default") {
        if (theme) {
            var newName = theme + '-copy';
            sendJSON("Fancygotchi/theme_copy", {"theme": theme, "new_name": newName}, function(response) {
                if (response.status == 200) {
                    alert("Theme copied successfully");
                    theme_list();
                } else {
                    alert("Error copying theme: " + response.responseText);
                }
            });
        } else {
            alert('Please select a theme to copy.');
        }
    } else {
        alert('Default theme cannot be copied.');
    }
}

function renameTheme() {
    var theme = document.getElementById("theme-selector").value;

    active_theme(function(activeTheme) {
        if (theme !== "Default" && theme !== activeTheme) {
            if (theme) {
                var newName = prompt("Enter new name for the theme:", theme);
                if (newName && newName !== theme) {
                    sendJSON("Fancygotchi/theme_rename", {"theme": theme, "new_name": newName}, function(response) {
                        if (response.status == 200) {
                            alert("Theme renamed successfully");
                            theme_list(); 
                        } else {
                            alert("Error renaming theme: " + response.responseText);
                        }
                    });
                }
            } else {
                alert('Please select a theme to rename.');
            }
        } else {
            alert('Default theme or active theme cannot be renamed.');
        }
    });
}

function theme_upload(event) {
    event.preventDefault();

    var formData = new FormData();
    var fileInput = document.getElementById('zipFile');
    var file = fileInput.files[0];

    if (!file) {
        alert('No file selected.');
        return;
    }

    formData.append('zipFile', file);

    sendFormData('Fancygotchi/theme_upload', formData, function(err, response) {
        if (err) {
            console.error(err);
            alert('An error occurred while uploading the theme.');
            return;
        }

        if (response.startsWith('Zip file uploaded')) {
            alert(response);
            theme_list();
        } else if (response.startsWith('Some folders were not copied')) {
            alert(response);
        } else {
            alert('Error: ' + response);
        }
    });
}

function theme_export() {
    var selectedTheme = document.getElementById('theme-selector').value;
    if (selectedTheme != "Default") {
        if (selectedTheme) {
            window.location.href = 'Fancygotchi/theme_export/' + selectedTheme;
        } else {
            alert('Please select a theme to export.');
        }
    } else {
        alert('Default theme cannot be exported.');
    }
}
$(document).on('click', '#confirm-delete', function() {
    var theme = $('#theme-selector').val();
    
    if (theme != "Default") {
        var json = { "theme": theme };
        
        sendJSON("Fancygotchi/theme_delete", json, function(xhr) {
            if (xhr.status == 200) {
                theme_list();
            }
        });
    } else {
        alert('Default theme cannot be deleted.');
    }
});

function theme_list() {

    active_theme(function(activeTheme) {
        loadJSON("Fancygotchi/theme_list", function(response) {
            populateThemeSelector(response, activeTheme);
        });
        $('#theme-selector').val(activeTheme);
        theme_info(activeTheme);
    });
}
function theme_info(activeTheme) {
    var theme = $('#theme-selector').val();
    var json = { "theme": theme };
    sendJSON("Fancygotchi/theme_info", json, function(xhr) {
        if (xhr.status == 200) {
            var themeInfo = JSON.parse(xhr.responseText);
            console.log(themeInfo);
            populateThemeInfo(themeInfo);
        }
    });
}
$('#theme-selector').change(function() {
    theme_info($(this).val());
});
function populateThemeSelector(themes, activeTheme) {
    var selectElement = $('#theme-selector');
    selectElement.empty();
    

    var defaultOption = $('<option>').val('Default').text('Default');
    selectElement.append(defaultOption);
    
    themes.forEach(function(theme) {
        var option = $('<option>').val(theme).text(theme);
        if (theme === activeTheme) {
            option.attr('selected', 'selected');
        }
        selectElement.append(option);
    });
    
    if (!themes.includes('Default') && !activeTheme) {
        defaultOption.attr('selected', 'selected');
    }
    
    selectElement.selectmenu('refresh');
    return activeTheme

}
function populateThemeInfo(themeInfo) {
    var $themeDescriptionContent = $('#theme-description-content');

    active_theme(function(activeTheme) {
        var theme = $('#theme-selector').val() || activeTheme || 'Default';
        console.log(theme);

        $themeDescriptionContent.empty();
        $themeDescriptionContent.append('<h3>' + theme.toUpperCase() + '</h3>');

        var $screenshot = $('#screenshot');
        var screenshotSrc = $('#theme-selector').val() == activeTheme 
            ? '/img/screenshot.png' 
            : '/screenshots/' + theme + '/screenshot.png';

        // Add a cache-busting timestamp parameter
        $screenshot.attr('src', screenshotSrc + '?cache_buster=' + new Date().getTime());
        
        // Log the src attribute to check the updated URL
        console.log($screenshot.attr('src'));

        $screenshot.on('error', function() {
            $(this).attr('src', '/screenshots/screenshot.png?cache_buster=' + new Date().getTime());
        });

        Object.entries(themeInfo).forEach(([key, value]) => {
            var val = '<span class="preserve-line-breaks">' + value + '</span>';
            $themeDescriptionContent.append($('<li>').html(key + ': ' + val));
        });
    });
}



function loadThemeRepo() {
    $('#theme_downloader').find('select, button').prop('disabled', true);
    $('#loading-spinner').show();
    $('#download_window').hide();
    $('#loading-spinner p').text("Loading...");

    loadJSON("Fancygotchi/theme_download_list", function(response) {
        console.log(response.status);
        if (response.status == 200) {
            populateThemeSelector_downloader(response.data);
            $('#loading-spinner').hide();
            $('#download_window').show();
            $('#theme_downloader').find('select, button').prop('disabled', false);
        }
        else {
            var error = response.error || "An error occurred";
            $('#loading-spinner p').text(error);
            $('#theme_downloader').find('select, button').prop('disabled', false);
        }
    });
}

$('#theme-downloader-selector').change(function() {
    var themes = window.themes; 
    var selectedTheme = $('#theme-downloader-selector').val();
    populateThemeInfo_downloader(themes[selectedTheme]);
});

function populateThemeSelector_downloader(themes) {
    window.themes = themes; 
    var selectElement = $('#theme-downloader-selector');
    selectElement.empty();
    const sortedThemes = Object.keys(themes).sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
    sortedThemes.forEach(function(theme) {
        var option = $('<option>').val(theme).text(theme);
        selectElement.append(option);
    });
    selectElement.selectmenu('refresh');
    if (sortedThemes.length > 0) {
        populateThemeInfo_downloader(themes[sortedThemes[0]]);
    }
}

function populateThemeInfo_downloader(themeInfo) {
    var $themeDescriptionContent = $('#theme-downloader-description-content');
    var theme = $('#theme-downloader-selector').val();
    if (theme == '') {
        theme = 'Default';
    }
    $themeDescriptionContent.empty();
    $themeDescriptionContent.append('<h3>' + theme.toUpperCase() + '</h3>');
    var img = new Image();
    var imgPath = '/repo_screenshots/' + theme + '/screenshot.png';
    img.onload = function() {
        document.getElementById('repo_screenshot').src = imgPath;
    };
    img.onerror = function() {
        document.getElementById('repo_screenshot').src = '/repo_screenshots/screenshot.png';
    };
    img.src = imgPath;
    $.each(themeInfo.info, function(key, value) {
        var val = '<span class="preserve-line-breaks">' + value + '</span>';
        var listItem = $('<li>').html(key + ': ' + val);
        $themeDescriptionContent.append(listItem);
    });
}

function theme_download_select() {
    var theme = document.getElementById("theme-downloader-selector").value;
    
    $('#theme_downloader').find('select, button').prop('disabled', true);

    var themes = window.themes; 
    var version = themes[theme]?.info?.version || 'Unknown'; 
    var json = {
        "theme": theme,
        "version": version
    };
    sendJSON("Fancygotchi/version_compare", json, function(response) {
        data = JSON.parse(response.responseText)
        var localVersion = data.local_version || 'Unknown';
        var isNewer = data.is_newer;
        if (isNewer) {
            var message = `A newer ${theme} version (${version}) is available. Your current version is ${localVersion}. Would you like to update?`;
        } 
        if (!isNewer) {
            var message = `You have the ${theme} version ${localVersion} installed. The available version is ${version}. Do you want to overwrite your current version?`;
        }
        if (isNewer == null) {
            var message = `You will download ${theme} version ${version}. Do you want to peoceed?`;
        }
        var confirmOverwrite = confirm(message);
        if (confirmOverwrite) {
            var json = {
                "theme": theme,
            };
            $('#loading-spinner').show();
            $('#loading-spinner p').text("Downloading...");
            sendJSON("Fancygotchi/theme_download_select", json, function(response) {
                if (response.status == 200) {
                    $('#loading-spinner').hide();
                    alert("Theme updated successfully!");
                    theme_list();
                } else {
                    $('#loading-spinner').hide();
                    alert("There was an error updating the theme.");
                }
                $('#theme_downloader').find('select, button').prop('disabled', false);
            });
        }
    });
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

function sendFormData(url, formData, callback) {
    var xhr = new XMLHttpRequest();
    var csrf = "{{ csrf_token() }}";
    xhr.open('POST', url);
    xhr.setRequestHeader('x-csrf-token', csrf);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            console.log("Response received:", xhr.responseText); 
            if (xhr.status === 200) {
                document.getElementById('zipFile').value = '';
                document.getElementById('message').innerHTML = 'Upload successful!';
                callback(null, xhr.responseText);
            } else {
                console.error('Request failed with status:', xhr.status);
                document.getElementById('message').innerHTML = 'Upload error: ' + xhr.responseText;
                callback(new Error('Request failed with status: ' + xhr.status), null);
            }
        }
    };

    xhr.send(formData);
}

function loadJSON(url, callback) {
    var xobj = new XMLHttpRequest();
    xobj.overrideMimeType("application/json");
    xobj.open('GET', url, true);
    xobj.onreadystatechange = function () {
        if (xobj.readyState == 4 && xobj.status == "200") {
            callback(JSON.parse(xobj.responseText));
        }
        if (xobj.readyState == 4 && xobj.status == "500") {
            callback(JSON.parse(xobj.responseText));
        }
        if (xobj.readyState == 4 && xobj.status == "404") {
            callback(JSON.parse(xobj.responseText));
        }
    };
    xobj.send(null);
}

function flattenJson(data) {
    var result = {};

    function recurse(cur, prop) {
        if (Array.isArray(cur)) {
            result[prop] = cur.map(function(item) {
                return typeof item === 'string' ? `"${item}"` : item;
            });
        } else if (Object(cur) !== cur) {
            result[prop] = cur;
        } else {
            for (var p in cur) {
                recurse(cur[p], prop ? prop + "." + p : p);
            }
        }
    }

    recurse(data, "");
    return result;
}

function jsonToArray(json) {
    var theme_array = [];
    var x = 0;
    Object.keys(json).forEach(function(key) {
        theme_array[x] = [key, json[key]];
        x+=1;
    });
    return theme_array;
}
function openDeleteDialog() {
    $('#delete-dialog').popup('open');
}
function theme_delete() {
    var theme = document.getElementById("theme-selector").value;
    active_theme(function(activeTheme) {
        if (theme !== "Default" && theme !== activeTheme) {
            openDeleteDialog();
        } else {
            alert('Cannot delete default theme or the active theme.');
        }
    });
}

function display_hijack() {
    var data = {};
    sendJSON("Fancygotchi/display_hijack", data, function(response) {
        if (response.status == "200") {
            alert("Screen Hijacked");
        } else {
            alert("Error while hijacking the display (err-code: " + response.status + ")");
        }
    });
}
function display_pwny() {
    var data = {};
    sendJSON("Fancygotchi/display_pwny", data, function(response) {
        if (response.status == "200") {
            alert("Screen Pwny");
        } else {
            alert("Error while diplaying pwagotchi (err-code: " + response.status + ")");
        }
    });
}
function display_next() {
    var data = {};
    sendJSON("Fancygotchi/display_next", data, function(response) {
        if (response.status == "200") {
            alert("Next second screen mode");
        } else {
            alert("Error while diplaying next second screen mode (err-code: " + response.status + ")");
        }
    });
}
function display_previous() {
    var data = {};
    sendJSON("Fancygotchi/display_previous", data, function(response) {
        if (response.status == "200") {
            alert("Next second screen mode");
        } else {
            alert("Error while diplaying previous second screen mode (err-code: " + response.status + ")");
        }
    });
}
function screen_saver_next() {
    var data = {};
    sendJSON("Fancygotchi/screen_saver_next", data, function(response) {
        if (response.status == "200") {
            alert("Next screen saver");
        } else {
            alert("Error while diplaying next screen saver (err-code: " + response.status + ")");
        }
    });
}
function screen_saver_previous() {
    var data = {};
    sendJSON("Fancygotchi/screen_saver_previous", data, function(response) {
        if (response.status == "200") {
            alert("Previous screen saver");
        } else {
            alert("Error while diplaying previous screen saver (err-code: " + response.status + ")");
        }
    });
}
function stealth() {
    var data = {};
    sendJSON("Fancygotchi/stealth", data, function(response) {
        if (response.status == "200") {
            alert("Stealth mode");
        } else {
            alert("Error while enabling stealth mode (err-code: " + response.status + ")");
        }
    });
}
function navigate(direction) {
    var data = {
        action: direction
    };

    sendJSON("Fancygotchi/navmenu", data, function(response) {
        if (response.status == "200") {
            console.log("Navigation: " + direction);
        } else {
            console.log("Navigation error: " + direction + " (err-code: " + response.status + ")");
        }
    });
}

function glitchEffect(amplify = false) {
    const lines = document.querySelectorAll('#fancygotchi span');
    const numLines = lines.length;
    
    const numGlitches = amplify ? Math.floor(Math.random() * numLines) + 1 : Math.min(5, Math.floor(Math.random() * 5));
    const indices = new Set();
    
    while (indices.size < numGlitches) {
        indices.add(Math.floor(Math.random() * numLines));
    }
    
    indices.forEach(index => {
        const line = lines[index];
        line.classList.add('glitch-line');
        
        const randomMove = Math.floor(Math.random() * 200) - 50; 
        line.style.transform = `translateX(${randomMove}px)`;  
        
        setTimeout(() => {
            line.classList.remove('glitch-line');
            line.style.transform = ''; 
        }, amplify ? 1000 : 300);
    });
}
document.addEventListener('click', () => {
    glitchEffect(true);
});

setInterval(glitchEffect, 150);
{% endblock %}
"""

CSS = """
.ui-image {
    width: 100%;
}

.pixelated {
    image-rendering: optimizeSpeed; /* Legal fallback */
    image-rendering: -moz-crisp-edges; /* Firefox        */
    image-rendering: -o-crisp-edges; /* Opera          */
    image-rendering: -webkit-optimize-contrast; /* Safari         */
    image-rendering: optimize-contrast; /* CSS3 Proposed  */
    image-rendering: crisp-edges; /* CSS4 Proposed  */
    image-rendering: pixelated; /* CSS4 Proposed  */
    -ms-interpolation-mode: nearest-neighbor; /* IE8+           */
}

.image-wrapper {
    flex: 1;
    position: relative;
}

div.status {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
}

a.read {
    color: #777 !important;
}

p.messagebody {
    padding: 1em;
}

li.navitem {
    width: 16.66% !important;
    clear: none !important;
}

/* Custom indentations are needed because the length of custom labels differs from
   the length of the standard labels */
.custom-size-flipswitch.ui-flipswitch .ui-btn.ui-flipswitch-on {
    text-indent: -5.9em;
}

.custom-size-flipswitch.ui-flipswitch .ui-flipswitch-off {
    text-indent: 0.5em;
}

/* Custom widths are needed because the length of custom labels differs from
   the length of the standard labels */
.custom-size-flipswitch.ui-flipswitch {
    width: 8.875em;
}

.custom-size-flipswitch.ui-flipswitch.ui-flipswitch-active {
    padding-left: 7em;
    width: 1.875em;
}

@media (min-width: 28em) {
    /*Repeated from rule .ui-flipswitch above*/
    .ui-field-contain > label + .custom-size-flipswitch.ui-flipswitch {
        width: 1.875em;
    }
}

#container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-around;
}

.plugins-box {
    margin: 0.5rem;
    padding: 0.2rem;
    border-style: groove;
    border-radius: 0.5rem;
    background-color: lightgrey;
    text-align: center;
}             
"""

BOOT_ANIM = """import time
from PIL import Image, ImageSequence
import os
import logging
from pwnagotchi import utils
import pwnagotchi.ui.hw as hw

from pwnagotchi.ui.hw import display_for
import argparse
#import traceback

def setup_logging(log_file='/var/log/bootanim.log'):
    # Ensure the directory exists
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,  # or DEBUG, WARNING, ERROR, CRITICAL
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def show_boot_animation(display_driver, config):
    try:
        frames_path = '{img_path}'
        width = {width}
        height = {height}
        rotation = {rotation}

        # Check if folder exists
        if not os.path.exists(frames_path):
            return

        # Accept common image formats
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        frames = sorted([f for f in os.listdir(frames_path) if f.lower().endswith(valid_extensions)])
        logging.debug("Found %s frames" % len(frames))
        # Check if there are any images to process
        if not frames:
            return

        frames_count = len(frames)

        if len(frames) == 1:
            if frames[0].lower().endswith('.gif'):
                source_path = os.path.join(frames_path, frames[0])
                with Image.open(source_path) as img:
                    frames_count = sum(1 for _ in ImageSequence.Iterator(img))

        max_loops = {max_loops}
        total_duration = {total_duration}
        start_time = time.time()
        loop_count = 0

        delay =  total_duration / (frames_count * max_loops)

        while (time.time() - start_time < total_duration) or (loop_count < max_loops):
            for frame in frames:
                if (time.time() - start_time >= total_duration) and (loop_count >= max_loops):
                    break
                
                frame_path = os.path.join(frames_path, frame)

                if frame.lower().endswith('.gif'):
                    logging.debug('Processing GIF: %s' % frame_path)
                    with Image.open(frame_path) as img:
                        for gif_frame in ImageSequence.Iterator(img):
                            if rotation == 90:
                                gif_frame = gif_frame.rotate(90, expand=True)
                            elif rotation == 180:
                                gif_frame = gif_frame.rotate(180, expand=True)
                            elif rotation == 270:
                                gif_frame = gif_frame.rotate(270, expand=True)
                            gif_frame = gif_frame.resize((width, height)).convert('{color_mode}')
                            logging.debug('Rendering frame: %s' % gif_frame)
                            display_driver.render(gif_frame)
                else:
                    # Handle any other image formats (jpg, jpeg, bmp, png, etc.)
                    with Image.open(frame_path) as img:
                        if rotation == 90:
                            img = img.rotate(90, expand=True)
                        elif rotation == 180:
                            img = img.rotate(180, expand=True)
                        elif rotation == 270:
                            img = img.rotate(270, expand=True)
                        img = img.resize((width, height)).convert('{color_mode}')
                        logging.debug('Rendering frame: %s' % img)
                        display_driver.render(img)
                        
                time.sleep(delay)  # Adjust this value to control animation speed
            logging.debug('Finished loop %d' % loop_count)
            loop_count += 1
            
    except Exception as ex:
        logging.error(ex)
        #logging.error(traceback.format_exc())
        display_driver.clear()

if __name__ == "__main__":
    setup_logging()
    logging.debug('Starting boot animation...')
    args = argparse.Namespace(
        config='/etc/pwnagotchi/default.toml', 
        user_config='/etc/pwnagotchi/config.toml', 
        do_manual=False, 
        skip_session=False, 
        do_clear=False, 
        debug=False, 
        version=False, 
        print_config=False, 
        wizard=False, 
        check_update=False, 
        donate=False
    )
    logging.debug(args)
    try:
        config = utils.load_config(args)
        logging.debug('Display config: %s' % config['ui']['display'])
        logging.debug('Display type: %s' % config['ui'])
        display_type = config['ui']['display']['type']
        logging.debug('Display type: %s' % display_type)
        display_driver = display_for(config)
        logging.debug(vars(display_driver))
        if display_driver is not None:
            
            display_driver.config['rotation'] = {rotation}
            
            if hasattr(display_driver, 'initialize'):
                try:
                    display_driver.initialize()
                    show_boot_animation(display_driver, config)
                    display_driver.config['enabled'] = True
                    display_driver.is_initialized = True
                except Exception as e:
                    logging.error(e)
            display_driver.config['enabled'] = False

            if hasattr(display_driver, 'displayImpl') and display_driver.config.get('enabled', False):
                display_driver.config['enabled'] = False
                logging.debug('[Fancygotchi] Display has been disabled')
                
                if hasattr(display_driver, 'clear'):
                    logging.debug('[Fancygotchi] Clearing the display')
                    display_driver.clear()
                
                display_driver.is_initialized = False

                if hasattr(display_driver, '_display'):
                    logging.debug('[Fancygotchi] Resetting internal display reference')
                    display_driver._display = None
        else:
            logging.error("Failed to initialize the display driver.")
    except KeyError as e:
        logging.error('KeyError: %s' % e)
        #logging.error(traceback.format_exc())
        display_type = 'Unknown'
"""

FANCYTOOLS = """#!{pyenv}
import time
import argparse
import os
import json
import subprocess
from multiprocessing.connection import Client

def create_log_directory():
    log_dir = '/var/log/fancytools/'
    if not os.path.exists(log_dir):
        result = subprocess.run(['sudo', 'mkdir', '-p', log_dir], check=True, capture_output=True, text=True)
        print("Directory %s created." % log_dir)
    return log_dir

def main():
    parser = argparse.ArgumentParser(description="Fancytools")
    parser.add_argument('-d', '--diagnostic', nargs='*', dest='diagnostic_args',
                        help='A full anonymized system report will be prompted. Additional arguments are accepted.')
    parser.add_argument('-p', '--plugin', dest='plugin', help='Name of the plugin to toggle')
    parser.add_argument('-e', '--enable', action='store_true', dest='enable',
                        help='Enable the specified plugin (default is to disable)')
    parser.add_argument('-r', '--restart', nargs='?', const='normal', dest='restart_mode',
                        help='Restart the system (auto or manu)')
    parser.add_argument('-b', '--reboot', nargs='?', const='normal', dest='reboot_mode',
                        help='Reboot the system (auto or manu)')
    parser.add_argument('-s', '--shutdown', action='store_true', dest='shutdown',
                        help='Shutdown the system')
    

    parser.add_argument('-m', '--menu', choices=['toggle', 'up', 'down', 'left', 'right', 'select'], help='Control the menu')
    parser.add_argument('-pr', '--refresh-plugins', action='store_true', help='Refresh installed plugins list')
    parser.add_argument('-ts', '--theme-select', nargs=2, metavar=('NAME', 'ROTATION'), help='Select theme')
    parser.add_argument('-tr', '--theme-refresh', action='store_true', help='Refresh theme')
    parser.add_argument('-S', '--stealth-mode', action='store_true', help='Toggle stealth mode')
    parser.add_argument('-sw', '--switch-screen-mode', choices=['next', 'previous'], help='Switch screen mode')
    parser.add_argument('-s2', '--second-screen', choices=['enable', 'disable'], help='Enable or disable second screen')
    parser.add_argument('-sc', '--screen-saver', choices=['next', 'previous'], help='Switch screen saver')
    parser.add_argument('-rb', '--run-bash', metavar='SCRIPT', help='Run a bash script')
    parser.add_argument('-rp', '--run-python', metavar='FILE', help='Run a Python script')
    
    args = parser.parse_args()

    log_dir = create_log_directory()
    log_output_file = os.path.join(log_dir, 'anonymized_log.txt')

    if args.diagnostic_args is not None:
        script_path = os.path.abspath(__file__)
        print("The path of the running script is: %s" % script_path)
        path = "/usr/local/bin/diagnostic.sh"
        os.system(path)

    if args.plugin:
        enable_state = 'True' if args.enable else 'False'
        command_data = {
            'action': 'plugin',
            'plugin': args.plugin,
            'enable': enable_state
        }
        send_command(command_data)
        print('Success %s.enable=%s' % (args.plugin, enable_state))

    if args.restart_mode:
        command_data = {
            'action': 'restart-%s' % args.restart_mode
        }
        send_command(command_data)
        print('Success: restart %s' % args.restart_mode)

    if args.reboot_mode:
        command_data = {
            'action': 'reboot-%s' % args.reboot_mode
        }
        send_command(command_data)
        print('Success: reboot %s' % args.reboot_mode)

    if args.shutdown:
        command_data = {
            'action': 'shutdown'
        }
        send_command(command_data)
        print('Success: shutdown')

    if args.menu:
        command_data = {
            'action': 'menu_%s' % args.menu
        }
        send_command(command_data)
        print(f'Success: menu %s' % args.menu)

    if args.refresh_plugins:
        send_command({'action': 'refresh_plugins'})

    if args.theme_select:
        send_command({'action': 'theme_select', 'name': args.theme_select[0], 'rotation': args.theme_select[1]})

    if args.theme_refresh:
        send_command({'action': 'theme_refresh'})

    if args.stealth_mode:
        send_command({'action': 'stealth_mode'})

    if args.switch_screen_mode:
        action = 'switch_screen_mode' if args.switch_screen_mode == 'next' else 'switch_screen_mode_reverse'
        send_command({'action': action})

    if args.second_screen:
        action = 'enable_second_screen' if args.second_screen == 'enable' else 'disable_second_screen'
        send_command({'action': action})

    if args.screen_saver:
        action = 'next_screen_saver' if args.screen_saver == 'next' else 'previous_screen_saver'
        send_command({'action': action})

    if args.run_bash:
        send_command({'action': 'run_bash', 'file': args.run_bash})

    if args.run_python:
        send_command({'action': 'run_python', 'file': args.run_python})

def send_command(command_data):
    address = ('localhost', 3699)
    while True:
        try:
            conn = Client(address)
            conn.send(json.dumps(command_data).encode('utf-8'))
            conn.close()
            print('Success: %s' % command_data["action"])
            break
        except ConnectionRefusedError as cre:
            print("Connection refused error: %s" % cre)
            time.sleep(5)
            continue

if __name__ == "__main__":
    main()
"""

DIAGNOSTIC= """#!/bin/bash

get_log_file_path() {
  local config_file="$1"
  if [ -f "$config_file" ]; then
    log_path=$(grep '^main\.log\.path' "$config_file" | cut -d'=' -f2 | tr -d ' "')
    if [ -n "$log_path" ]; then
      echo "$log_path"
      return
    fi
  fi
  echo ""
}

# Get the script's directory
script_dir=$(dirname "$(readlink -f "$0")")

# Output file in the script's directory
output_file="/var/log/fancytools/system_info.txt"

# Pwnagotchi version
echo "Pwnagotchi version:" > "$output_file"
pip list | grep pwnagotchi >> "$output_file"
echo >> "$output_file"

# Kernel info
echo "Kernel info:" >> "$output_file"
uname -a >> "$output_file"
echo >> "$output_file"

# Boot config
echo "Boot config:" >> "$output_file"

# Check for the presence of cmdline.txt and config.txt in /boot/firmware
cmdline_file="/boot/firmware/cmdline.txt"
config_file="/boot/firmware/config.txt"

if [ -f "$cmdline_file" ]; then
  cat "$cmdline_file" >> "$output_file"
else
  # Fallback to /boot if not found in /boot/firmware
  if [ -f "/boot/cmdline.txt" ]; then
    cat "/boot/cmdline.txt" >> "$output_file"
  else
    echo "cmdline.txt not found." >> "$output_file"
  fi
fi
echo >> "$output_file"
if [ -f "$config_file" ]; then
  cat "$config_file" >> "$output_file"
else
  # Fallback to /boot if not found in /boot/firmware
  if [ -f "/boot/config.txt" ]; then
    cat "/boot/config.txt" >> "$output_file"
  else
    echo "config.txt not found." >> "$output_file"
  fi
fi
echo >> "$output_file"


# Service status
echo "Service status:" >> "$output_file"
service pwnagotchi status >> "$output_file"
echo >> "$output_file"

# Network driver interface load
echo "Network driver interface load:" >> "$output_file"
sudo dmesg | grep brcm >> "$output_file"
echo >> "$output_file"

# List all IP active host names
echo "List all IP active host names:" >> "$output_file"
hostname -I >> "$output_file"
echo >> "$output_file"

echo "List all active ports:" >> "$output_file"
lsof -nP -iTCP -sTCP:LISTEN >> "$output_file"
echo >> "$output_file"

# List available plugins
echo "List available plugins:" >> "$output_file"
cat /etc/pwnagotchi/config.toml | grep plugin | grep enabled >> "$output_file"
echo >> "$output_file"

# List enabled plugins
echo "List enabled plugins:" >> "$output_file"
cat /etc/pwnagotchi/config.toml | grep plugin | grep enabled | grep true >> "$output_file"
echo >> "$output_file"

# Attempt to find the log file path in the preferred config file
log_file=$(get_log_file_path "/etc/pwnagotchi/config.toml")

# If not found, check the default config file
if [ -z "$log_file" ]; then
  log_file=$(get_log_file_path "/etc/pwnagotchi/default.toml")
fi

# Check if log file path was found
if [ -z "$log_file" ]; then
  log_file="/var/log/pwnagotchi.log"
fi

# Config file
config_file="/etc/pwnagotchi/config.toml"

# Output files in the /var/log directory
log_dir="/var/log/fancytools/"
if [ ! -d "$log_dir" ]; then
  echo "Creating log directory: $log_dir"
  sudo mkdir -p "$log_dir" || { echo "Failed to create $log_dir"; exit 1; }
  echo "Directory $log_dir created."
fi

log_output_file="$log_dir/anonymized_log.txt"
config_output_file="$log_dir/anonymized_config.toml"

# Ensure we have write access to log files
if [ ! -w "$log_dir" ]; then
  echo "Cannot write to $log_dir. Please check permissions."
  exit 1
fi

# Anonymize and export the last 100 lines of the log file to a file
if [ -f "$log_file" ]; then
  echo "Anonymized log (last 100 lines):"
  tail -n 100 "$log_file" | sed -E -e 's/([0-9]{1,3}\.){3}[0-9]{1,3}/XX.XX.XX.XX/g' -e 's/([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}/XX:XX:XX:XX:XX:XX/g' -e '/api_key/ s/=.*$/= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"/' -e '/whitelist/ {s/=.*/= \[\]/; :loop n; /\]/! {s/^[[:space:]]*["'"'"'].*["'"'"'],?//; s/^[[:space:]]*\][[:space:]]*$//; b loop}}' -e '/password/ s/=.*$/= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"/' -e 's/@[^()]*()/@XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/' > "$log_output_file"
else
  echo "Log file $log_file not found."
  exit 1
fi

# Anonymize and export the config file to a file
if [ -f "$config_file" ]; then
  echo -e "\nAnonymized config file:"
  sed -E -e 's/([0-9]{1,3}\.){3}[0-9]{1,3}/XX.XX.XX.XX/g' -e 's/([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}/XX:XX:XX:XX:XX:XX/g' -e '/api_key/ s/=.*$/= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"/' -e '/whitelist/ {s/=.*/= \[\]/; :loop n; /\]/! {s/^[[:space:]]*["'"'"'].*["'"'"'],?//; s/^[[:space:]]*\][[:space:]]*$//; b loop}}' -e '/password/ s/=.*$/= "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"/' "$config_file" > "$config_output_file"
else
  echo "Config file $config_file not found."
  exit 1
fi

cat $output_file
cat $log_output_file
cat $config_output_file

echo "Basic system info saved to $output_file"
echo "Anonymized log saved to $log_output_file"
echo "Anonymized config saved to $config_output_file"
"""

FANCYDISPLAY = '/var/tmp/pwnagotchi/FancyDisplay.png'

class FancyDisplay:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FancyDisplay, cls).__new__(cls)
        return cls._instance

    def __init__(self, enabled=False, fps=1, th_path='', mode='screen_saver', sub_mode='show_logo', config={}):
        self.enabled = enabled
        self.image_lock = threading.Lock()
        self.is_image_locked = False
        self.th_path = th_path
        self.displayImpl = None
        self.hijack_frame = None
        self.task = None
        self.loop = None
        self.thread = None
        self.is_running_event = asyncio.Event()
        self.stop_event = threading.Event()
        self.running = False
        self.fps = fps
        self.fb = self.find_fb_device()
        self.current_mode = mode
        self.current_screen_saver = sub_mode
        self.modes = ['screen_saver', 'auxiliary', 'terminal']
        self.screen_saver_modes = ['show_logo', 'moving_shapes', 'random_colors', 'hyper_drive', 'show_animation']
        if config: self.screen_data = config
        else: self.screen_data = {}
        self.set_mode(mode, sub_mode)

    def _start_loop(self):
        logging.warning("[FancyDisplay] Starting the asyncio event loop in a new thread.")
        asyncio.set_event_loop(self.loop)
        self.is_running_event.set()
        try:
            self.loop.run_until_complete(self.screen_controller())
        except asyncio.CancelledError:
            pass
        finally:
            self.loop.close()
            self.is_running_event.clear()

    def start(self, res, rot, col):
        logging.debug("[FancyDisplay] Starting display controller.")
        self._res = res
        self._rot = rot
        self._col = col
        self.displayImpl = self.display_hijack()

        if self.loop is None or self.loop.is_closed():
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._start_loop, daemon=True)
            self.thread.start()

        while not self.is_running_event.is_set():
            time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join()
        self.loop = None
        self.thread = None
        logging.debug("[FancyDisplay] Display controller stopped.")

    async def screen_controller(self):
        self.running = True
        while self.running:
            await self.refacer()
            await asyncio.sleep(0.1)

    def is_running(self):
        if self.is_running_event is not None:
            return self.is_running_event.is_set()
        logging.error("[FancyDisplay] is_running_event is not initialized.")
        return False

    def cleanup(self):
        logging.debug("[FancyDisplay] Cleaning up the FancyDisplay resources.")
        self.task = None
        if self.loop is not None:
            if not self.loop.is_closed():
                logging.debug("[FancyDisplay] Closing event loop.")
                self.loop.close()
        self.loop = None
        self.thread = None
        self.displayImpl = None
        self.hijack_frame = None
        self.screen_data = {}
      
    def _calculate_aspect_ratio(self, width, height, aspect_ratio):
        if width < height:
            new_width = width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = height
            new_width = int(new_height * aspect_ratio)
        return new_width, new_height

    def screen(self):
        return  self.hijack_frame

    async def refacer(self):
        try: 
            fps = 1 / self.fps 
            refresh_interval = 1
            iteration = 0
            while self.running:
                if iteration % refresh_interval == 0:
                    self.hijack_frame = self.get_mode_image()

                if self.hijack_frame is not None:
                    canvas = self.hijack_frame
                    if self._rot == 90:
                        canvas = canvas.rotate(90, expand=True)
                    elif self._rot == 180:
                        canvas = canvas.rotate(180, expand=True)
                    elif self._rot == 270:
                        canvas = canvas.rotate(270, expand=True)

                    if self.enabled:
                        canvas = canvas.resize((self._res[0], self._res[1])).convert(self._col)
                        self.displayImpl.render(canvas)
                else:
                    logging.warning("[FancyDisplay] No image to display.")
                    
                
                await asyncio.sleep(fps)
                iteration += 1

        except asyncio.CancelledError:
            logging.warning("[FancyDisplay] refacer cancelled.")
    def display_hijack(self):
        try:
            args = argparse.Namespace(
                config='/etc/pwnagotchi/default.toml', 
                user_config='/etc/pwnagotchi/config.toml', 
                do_manual=False, 
                skip_session=False, 
                do_clear=False, 
                debug=False, 
                version=False, 
                print_config=False, 
                wizard=False, 
                check_update=False, 
                donate=False
            )
            config = utils.load_config(args)
            display_type = config['ui']['display']['type']
            display = config['ui']['display']['enabled']
            self.displayImpl = None

            displayImpl = getattr(self, 'displayImpl', None)
            if not displayImpl or not displayImpl.config.get('enabled', False):
                self.displayImpl = display_for(config)
                self.displayImpl.config['rotation'] = 0
                logging.debug(self.displayImpl.config)

                if hasattr(self.displayImpl, 'initialize') or not self.enabled:
                    logging.debug('[Fancygotchi] Initializing display')
                    if self.enabled:
                        self.displayImpl.initialize()
                    self.displayImpl.config['enabled'] = True
                    return self.displayImpl
                else:
                    logging.debug('[Fancygotchi] Failed to initialize display: No initialization method found.')
            else:
                logging.debug('[Fancygotchi] Display is already initialized.')

        except KeyError as e:
            logging.error(f'[FancyDisplay] KeyError while display hijacking: {e}')
            logging.error(traceback.format_exc())
            
    def glitch_text_effect(self, text, glitch_chance=0.2, max_spaces=3):
        lines = text.split('\n')
        glitched_lines = []

        for line in lines:
            if random.random() < glitch_chance: 
                num_spaces = random.randint(1, max_spaces) 
                line = ' ' * num_spaces + line 

            glitched_lines.append(line)

        return '\n'.join(glitched_lines)

    def set_mode(self, mode, sub_mode=None, config={}):
        if mode in self.modes:
            logging.debug(f"[FancyDisplay] Switching to mode: {mode}")
            self.current_mode = mode
            if mode == "screen_saver":
                self.set_screen_saver_mode(sub_mode)
                self.screen_cdata = config
            elif mode == "auxiliary":
                self.screen_data = config
            elif mode == "terminal":
                self.screen_data = config 
        else:
            logging.warning(f"[FancyDisplay] Invalid mode: {mode}. Available modes are: {self.modes}")
    
    def switch_mode(self, direction='next'):
        current_index = self.modes.index(self.current_mode)
        sub_mode = None
        if direction == 'next':
            next_index = (current_index + 1) % len(self.modes)
        elif direction == 'previous':
            next_index = (current_index - 1) % len(self.modes)
        else:
            logging.warning(f"[FancyDisplay] Invalid direction: {direction}. Using 'next' as default.")
            next_index = (current_index + 1) % len(self.modes)
        
        next_mode = self.modes[next_index]
        
        logging.debug(f"[FancyDisplay] Switching to the {direction} mode: {next_mode}")
        if next_mode == "screen_saver": 
            sub_mode = self.current_screen_saver
        self.set_mode(next_mode, sub_mode)
        self.set_screen_saver_mode(sub_mode)
        self.current_mode = next_mode
        return next_mode

    def find_fb_device(self):
        for i in range(10): 
            fb_device = f"/dev/fb{i}"
            if os.path.exists(fb_device):
                return fb_device
        return None

    def get_fb_size(self):
        import subprocess
        output = subprocess.check_output(['fbset', '-s']).decode('utf-8')
        for line in output.split('\n'):
            if 'geometry' in line:
                parts = line.split()
                return int(parts[1]), int(parts[2])
        return self._res[0], self._res[1] 

    def read_fb(self, width, height):
        with open(self.fb, "rb") as fb:
                return memoryview(fb.read(width * height * 2))

    def terminal_mode(self):
        if self.fb is None:
            return self.show_logo()

        fb_width, fb_height = self.get_fb_size()
        fb_data = self.read_fb(fb_width, fb_height)
        
        rgb_image = self.convert_to_rgb(fb_data, fb_width, fb_height)
        image = Image.fromarray(rgb_image, mode='RGB')
        
        width, height = self._res
        resized_image = image.resize((width, height), Image.BILINEAR)
        
        return resized_image

    def convert_to_rgb(self, fb_data, width, height):
        rgb_array = np.zeros((height, width, 3), dtype=np.uint8)
        pixels = np.frombuffer(fb_data, dtype=np.uint16)
        
        r = ((pixels >> 11) & 0x1F) << 3
        g = ((pixels >> 5) & 0x3F) << 2
        b = (pixels & 0x1F) << 3
        
        rgb_array[..., 0] = r.reshape(height, width)
        rgb_array[..., 1] = g.reshape(height, width)
        rgb_array[..., 2] = b.reshape(height, width)
        
        return rgb_array

    def set_screen_saver_mode(self, sub_mode):
        if sub_mode is None:
            sub_mode = self.current_screen_saver
        if sub_mode in self.screen_saver_modes:
            logging.debug(f"[FancyDisplay] Switching screen_saver to: {sub_mode}")
            self.current_screen_saver = sub_mode
            if sub_mode == 'show_logo':
                options = {}
            elif sub_mode == 'moving_shapes':
                options = {
                    "shape_type": "text", 
                    "text": "Fancygotchi", 
                    "font_path": "/usr/local/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                    "color": "red", 
                    "speed": 10, 
                    "font_size": 40,
                }
            elif sub_mode == 'random_colors':
                options = {
                    "speed": 1,
                }
            elif sub_mode == 'hyper_drive':
                num_stars = 100 
                options = {
                    'stars': [
                        {
                            'position': [random.randint(-self._res[0]//2, self._res[0]//2), random.randint(-self._res[1]//2, self._res[1]//2)],
                            'velocity': random.uniform(2, 5),  
                            'size': random.uniform(1, 3),
                            'streak_length': random.uniform(5, 20),
                            'color': 'white'
                        } for _ in range(num_stars)
                    ],
                    'speed': 1.0 
                }
            elif sub_mode == 'show_animation':
                options = {
                    'frames_path': os.path.join(self.th_path, 'img', 'boot'),
                    'max_loops': 1,
                    'total_duration': 10,
                }
            self.screen_data.update(options)
        else:
            logging.warning(f"[FancyDisplay] Invalid screen_saver sub-mode: {sub_mode}. Available sub-modes are: {self.screen_saver_modes}")

    
    def switch_screen_saver_submode(self, direction='next'):
        if self.current_mode != 'screen_saver':
            logging.warning(f"[FancyDisplay] Not in screen_saver mode. Current mode is: {self.current_mode}")
            return self.current_mode
        
        current_index = self.screen_saver_modes.index(self.current_screen_saver)
        
        if direction == 'next':
            next_index = (current_index + 1) % len(self.screen_saver_modes) 
        elif direction == 'previous':
            next_index = (current_index - 1) % len(self.screen_saver_modes)  
        else:
            logging.error(f"[FancyDisplay] Invalid direction: {direction}. Must be 'next' or 'previous'.")
            return self.current_mode
        
        next_submode = self.screen_saver_modes[next_index]
        logging.warning(f"[FancyDisplay] Switching to the {direction} screen_saver sub-mode: {next_submode}")
        self.set_screen_saver_mode(next_submode)
        return next_submode

    def get_mode_image(self):
        logging.debug(f"[FancyDisplay] Getting mode image: {self.current_mode}")
        if self.current_mode == 'screen_saver':
            return self.get_screen_saver_image()
        elif self.current_mode == 'auxiliary':
            return self.auxiliary_image()
        elif self.current_mode == 'terminal':
            return self.terminal_mode()
        else:
            logging.warning(f"[FancyDisplay] Unknown mode: {self.current_mode}. Falling back to default.")
            return self.show_logo()

    def get_screen_saver_image(self):
        if self.current_screen_saver == 'show_logo':
            return self.show_logo() 
        elif self.current_screen_saver == 'moving_shapes':
            return self.moving_shapes_screen_saver()
        elif self.current_screen_saver == 'random_colors':
            return self.random_colors_screen_saver()
        elif self.current_screen_saver == 'hyper_drive':
            return self.hyperdrive_screen_saver()
        elif self.current_screen_saver == 'show_animation':
            return self.show_animation_screen_saver()
        else:
            logging.warning(f"[FancyDisplay] Unknown screen_saver sub-mode: {self.current_screen_saver}.")
            self.current_screen_saver = 'show_logo'
            return self.show_logo() 


    def auxiliary_image(self):
        image = self.show_logo()
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
        text = "Auxiliary mode"
        text_color = (255, 0, 0) 
        image_width, image_height = image.size
        text_width, text_height = draw.textsize(text, font)
        position = ((image_width - text_width) // 2, 10)
        draw.text(position, text, font=font, fill=text_color)
        return image

    def show_logo(self):
        try:
            width = self._res[0]
            height = self._res[1]
            canvas = Image.new('RGBA', (width, height), 'black')
            draw = ImageDraw.Draw(canvas)
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 3)
            text = self.glitch_text_effect(LOGO, glitch_chance=0.25, max_spaces=5)
            text_width, text_height = draw.textsize(text, font=font)
            logo_img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
            draw_logo = ImageDraw.Draw(logo_img)
            draw_logo.text((0, 0), text, fill='lime', font=font)
            aspect_ratio = text_width / text_height
            new_width, new_height = self._calculate_aspect_ratio(width, height, aspect_ratio)
            resized_logo = logo_img.resize((new_width, new_height))
            x = (width - new_width) // 2
            y = (height - new_height) // 2
            canvas.paste(resized_logo, (x, y), resized_logo)
            self.hijack_frame = canvas
            return canvas
        except KeyError as e:
            logging.debug(f'[FancyDisplay] KeyError while showing logo: {e}')
            logging.debug(traceback.format_exc())

    def moving_shapes_screen_saver(self):
        try:
            font_path = self.screen_data.get('font_path')
            font_size = self.screen_data.get('font_size')
            shape_type = self.screen_data.get('shape_type')
            text = self.screen_data.get('text')
            color = self.screen_data.get('color')
            speed = self.screen_data.get('speed')

            width, height = self._res
            font = ImageFont.load_default() if self.screen_data.get(font_path) is None else ImageFont.truetype(font_path, font_size)
            
            if shape_type == "text":
                shape_width, shape_height = font.getsize(text)
            else:
                shape_width = shape_height = shape_size 
            
            if not hasattr(self, 'shape_position'):
                self.shape_position = [random.randint(0, width - shape_width), random.randint(0, height - shape_height)]
                self.shape_velocity = [random.choice([-1, 1]) * speed, random.choice([-1, 1]) * speed] 

            x, y = self.shape_position
            vx, vy = self.shape_velocity

            if x + shape_width >= width or x <= 0:
                vx = -vx
            if y + shape_height >= height or y <= 0:
                vy = -vy
            x += vx
            y += vy
            self.shape_position = [x, y]
            self.shape_velocity = [vx, vy]

            canvas = Image.new('RGBA', (width, height), 'black')
            draw = ImageDraw.Draw(canvas)

            if shape_type == "text":
                draw.text((x, y), text, font=font, fill=color)
            else:
                draw.ellipse((x, y, x + shape_width, y + shape_height), fill=color)
            return canvas
        except KeyError as e:
            logging.debug(f'[FancyDisplay] KeyError while moving shapes: {e}')
            logging.debug(traceback.format_exc())

    def random_colors_screen_saver(self):
        speed = self.screen_data.get('speed')
        width, height = self._res
        canvas = Image.new('RGBA', (width, height), (
            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255))
        time.sleep(speed)
        return canvas

    def hyperdrive_screen_saver(self):
        width, height = self._res
        canvas = Image.new('RGBA', (width, height), 'black')
        draw = ImageDraw.Draw(canvas)
        
        center_x, center_y = width // 2, height // 2
        speed = self.screen_data.get('speed', 1.0)
        
        stars = self.screen_data['stars']
        
        for star in stars:
            pos_x, pos_y = star['position']
            velocity = star['velocity'] * speed 
            size = star['size']
            streak_length = star['streak_length']
            
            pos_x *= (1 + velocity / 100)
            pos_y *= (1 + velocity / 100)
            
            streak_end_x = pos_x * (1 + streak_length / 100)
            streak_end_y = pos_y * (1 + streak_length / 100)

            size = min(size * (1 + velocity / 10), 10)
            
            draw.line([(center_x + streak_end_x, center_y + streak_end_y), 
                    (center_x + pos_x, center_y + pos_y)], fill=star['color'], width=int(size))
            
            if abs(pos_x) > width // 2 or abs(pos_y) > height // 2:
                star['position'] = [random.randint(-50, 50), random.randint(-50, 50)]
                star['velocity'] = random.uniform(2, 5)
                star['size'] = random.uniform(1, 3)
                star['streak_length'] = random.uniform(5, 20)
                
                pos_x, pos_y = star['position']
                velocity = star['velocity'] * speed
                pos_x *= (1 + velocity / 100)
                pos_y *= (1 + velocity / 100)
                streak_end_x = pos_x * (1 + star['streak_length'] / 100)
                streak_end_y = pos_y * (1 + star['streak_length'] / 100)
                
                draw.line([(center_x + streak_end_x, center_y + streak_end_y), 
                        (center_x + pos_x, center_y + pos_y)], fill=star['color'], width=int(star['size']))

            star['position'] = [pos_x, pos_y]
        
        return canvas

    def show_animation_screen_saver(self):
        try:
            if self.screen_data is None:
                logging.error("[FancyDisplay] screen_data is None. Unable to show animation screen saver.")
                return self.show_logo() 
                
            frames_path = self.screen_data.get('frames_path', '')
            max_loops = self.screen_data.get('max_loops', 1)
            total_duration = self.screen_data.get('total_duration', 10)
            target_fps = 24
            frame_duration = 0.2

            if not os.path.exists(frames_path):
                image = self.show_logo()
                return image

            valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            frames = sorted([f for f in os.listdir(frames_path) if f.lower().endswith(valid_extensions)])
            
            if not frames:
                logging.error("[FancyDisplay] No valid frames found in the specified directory")
                return None

            if not hasattr(self, 'animation_state'):
                self.animation_state = {
                    'start_time': time.time(),
                    'loop_count': 0,
                    'extracted_frames': []
                }

            current_time = time.time()
            elapsed_time = current_time - self.animation_state['start_time']

            if (self.animation_state['loop_count'] >= max_loops):
                self.animation_state['start_time'] = current_time
                self.animation_state['loop_count'] = 0
                self.animation_state['extracted_frames'] = []

            if not self.animation_state['extracted_frames']:
                for frame in frames:
                    frame_path = os.path.join(frames_path, frame)
                    if frame.lower().endswith('.gif'):
                        with Image.open(frame_path) as img:
                            for gif_frame in ImageSequence.Iterator(img):
                                self.animation_state['extracted_frames'].append(copy.deepcopy(gif_frame))
                    else:
                        self.animation_state['extracted_frames'].append(Image.open(frame_path))
                
                logging.debug(f"[FancyDisplay] Extracted {len(self.animation_state['extracted_frames'])} frames")

            total_frames = len(self.animation_state['extracted_frames'])
            current_frame_index = int((elapsed_time / frame_duration) % total_frames)

            current_frame = self.animation_state['extracted_frames'][current_frame_index]

            image = current_frame.resize((self._res[0], self._res[1])).convert(self._col)

            if current_frame_index == 0 and elapsed_time > 0: 
                self.animation_state['loop_count'] += 1

            if image is None:
                image = self.show_logo()
            return image

        except Exception as ex:
            logging.error(f"[FancyDisplay] Error in show_animation_screen_saver: {ex}")
            logging.error(traceback.format_exc())
            return None

class FancyServer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FancyServer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.server = None
            self.thread = None
            self.loop = None
            self.is_running_event = threading.Event()
            self.running = False
            self.last_command = None
            self.navi_cmd = [
                'menu_up', 
                'menu_down', 
                'menu_left', 
                'menu_right', 
                'menu_toggle', 
                'menu_select', 
            ]

    def _start_loop(self):
        logging.debug("[FancyServer] Starting the asyncio event loop in a new thread.")
        asyncio.set_event_loop(self.loop)
        self.is_running_event.set()
        try:
            self.loop.run_until_complete(self.start_server())
        except asyncio.CancelledError:
            pass
        finally:
            self.loop.close()
            self.is_running_event.clear()

    def start(self):
        if self.loop is None or self.loop.is_closed():
            logging.debug("[FancyServer] Starting FancyServer.")
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._start_loop, daemon=True)
            self.thread.start()

        while not self.is_running_event.is_set():
            time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.server:
            self.server.close()
            self.server = None
        if self.thread:
            self.thread.join()
        self.loop = None
        self.thread = None
        logging.debug("[FancyServer] FancyServer stopped.")

    def restart(self):
        logging.debug("[FancyServer] Restarting FancyServer.")
        self.stop()
        self.start()

    async def handle_client(self, reader, writer):
        try:
            logging.debug("[Fancygotchi] Client connected.")
            data = await reader.read()

            if data:
                json_match = re.search(b'{.*}', data)
                if json_match:
                    json_str = json_match.group(0).decode('utf-8')
                    command = json.loads(json_str)
                    await self.process_command(command)
                else:
                    logging.warning("[FancyServer] No valid JSON found in the data.")
            else:
                logging.warning("[FancyServer] No command received.")
        except Exception as e:
            logging.error(f"[FancyServer] An error occurred while handling client: {e}")
            logging.error(traceback.format_exc())
        finally:
            writer.close()
            await writer.wait_closed()

    async def process_command(self, command):
        try:
            logging.debug(f"[FancyServer] Received command: {command}")
            action = command.get('action')
            if action == 'plugin':
                name = command.get('plugin')
                state = command.get('enable')
                is_change = toggle_plugin(name, enable=(state == 'True'))
                logging.debug(f'[FancyServer] {name} {"changed state" if is_change else "did not change state"}')
            elif action == 'shutdown':
                pwnagotchi.shutdown()
            elif action.startswith('restart-'):
                mode = action.split('-')[1]
                pwnagotchi.restart(mode)
            elif action.startswith('reboot-'):
                mode = action.split('-')[1]
                pwnagotchi.reboot(mode)
            elif action in self.navi_cmd:
                self.last_command = command
            else:
                self.last_command = command
        except Exception as e:
            logging.error(f"[FancyServer] An error occurred while processing command: {e}")
            traceback.print_exc()

    async def start_server(self):
        if self.running:
            logging.debug('[FancyServer] Already started')
            return

        self.running = True
        self.server = await asyncio.start_server(self.handle_client, 'localhost', 3699)
        addr = self.server.sockets[0].getsockname()
        logging.debug(f'[FancyServer] Serving on {addr}')

        async with self.server:
            while self.running:
                await asyncio.sleep(1) 
            logging.debug('[FancyServer] loop finished')

    def get_last_command(self):
        command = self.last_command
        self.last_command = None
        return command

class FancyMenu:

    def __init__(self, fancygotchi, menu_theme, custom_menus={}):
        
        self._fancygotchi = fancygotchi
        self.menus = copy.deepcopy(MENUS)
        self.scroll_state = {}
        self.menu_theme = menu_theme
        self.menu_stack = [self.menus['Main menu']]
        self.active = False
        self.timeout = menu_theme['timeout']

        self.last_activity_time = time.time()
        self.plugin_names = get_all_plugin_names(self._fancygotchi)
        self.populate_plugins_menu(self.plugin_names)
        self.populate_themes_menu()
        if custom_menus != {}:
            self.load_menu_config(custom_menus)

        self.reset_menus(custom_menus)

    def reset_menus(self, custom_menus={}):
        self.menus = copy.deepcopy(MENUS) 
        self.menu_stack = [self.menus['Main menu']]
        self.populate_plugins_menu(self.plugin_names)
        self.populate_themes_menu()
        if custom_menus:
            self.load_menu_config(custom_menus)

    def load_menu_config(self, config):
        menus = {}
        main = {}
        issues = []
        for menu_key, menu_data in config.items():
            if not isinstance(menu_data, dict):
                issues.append(f"[FancyMenu] Menu data for '{menu_key}' is not a dictionary.")
                continue
            menu_title = menu_data.get("options", {}).get("title", menu_key)
            action = {"action": "submenu", "name": menu_title}
            if not menu_contains_button(self.menu_stack[0], menu_title):
                self.menu_stack[0].add_button(menu_title, action)
            menu_title = menu_data.get("options", {}).get("title", menu_key)
            back_menu = menu_data.get("options", {}).get("back", "Main menu") or "Main menu"
            buttons = []
            for btn_key, btn_data in menu_data.items():
                if btn_key.startswith("btn"):
                    if not isinstance(btn_data, dict):
                        issues.append(f"[FancyMenu] Button data for '{btn_key}' in menu '{menu_key}' is not a dictionary.")
                        continue
                    title = btn_data.get("title", f"Button {btn_key[-1]}")
                    buttons.append((title, btn_data))
            menus[menu_title] = Menu(menu_title, buttons, back_reference=back_menu)
            self.menus.update(menus)
        if issues:
            logging.warning("[FancyMenu] Issues encountered during menu configuration: \n" + "\n".join(issues))

    def populate_plugins_menu(self,plugin_names):
        menus = {}
        sorted_plugin_names = sorted(plugin_names)
        menus['Plugins toggle'] = Menu('Plugins toggle', [], back_reference='Plugins')
        for plugin in sorted_plugin_names:
            if plugin.lower() != 'fancygotchi':
                if plugin != 'None' and plugin is not None:
                    menus[plugin] = Menu(plugin, [
                        ("Enable plugin", {"action": "plugin", "plugin": plugin, "enable": True}),
                        ("Disable plugin", {"action": "plugin", "plugin": plugin, "enable": False}),
                    ], back_reference='Plugins toggle')
                    menus['Plugins toggle'].items.append((
                        plugin.capitalize(), {"action": "submenu", "name": plugin}
                    ), )
        self.menus.update(menus)

    def populate_themes_menu(self):
        theme_names = self._fancygotchi.theme_list()
        menus = {}
        sorted_theme_names = sorted(theme_names)
        menus['Theme selector'] = Menu('Theme selector', [], back_reference='Fancygotchi')
        for theme in theme_names:
            menus[theme] = Menu(theme, [
                (f"{theme} 0", {"action": "theme_select", "name": theme, "rotation": 0,}),
                (f"{theme} 90", {"action": "theme_select", "name": theme, "rotation": 90}),
                (f"{theme} 180", {"action": "theme_select", "name": theme, "rotation": 180}),
                (f"{theme} 270", {"action": "theme_select", "name": theme, "rotation": 270}),
            ], back_reference='Theme selector')
            menus['Theme selector'].items.append((
                theme.capitalize(), {"action": "submenu", "name": theme}
            ), )
        self.menus.update(menus)

    def toggle(self):
        self.active = not self.active
        self.last_activity_time = time.time() 
        return self.active

    def navigate(self, direction):
        if self.active:
            current_menu = self.menu_stack[-1]
            if direction in ['up', 'down']:
                current_menu.navigate(direction)
            elif direction == 'left':
                if len(self.menu_stack) > 1:
                    self.menu_stack.pop()
            elif direction == 'right':
                selected_item = current_menu.items[current_menu.current_index]
                if isinstance(selected_item[1], dict) and selected_item[1].get('action') == 'submenu':
                    submenu_name = selected_item[1]['name']
                    if submenu_name in self.menus:
                        self.menu_stack.append(self.menus[submenu_name])
            self.last_activity_time = time.time()  
    def select(self):
        current_menu = self.menu_stack[-1]
        return current_menu.items[current_menu.current_index][1]

    def check_timeout(self):
        if self.timeout != 0:
            current_time = time.time()
            if current_time - self.last_activity_time > self.timeout:
                logging.debug("[FancyMenu] Session timed out.")
                self.active = False
                return True
            return False
        else:
            self.active = True
            return False

    def render(self):
        try:
            if self.active:
                if self.check_timeout():
                    return

                if not hasattr(self, 'loaded_images'):
                    self.loaded_images = {}

                current_menu = self.menu_stack[-1]
                rot = self._fancygotchi._config['main']['plugins']['Fancygotchi']['rotation']
                if rot == 0 or rot == 180:
                    canvas_width, canvas_height = self._fancygotchi._res
                elif rot == 90 or rot == 270:
                    canvas_width = self._fancygotchi._res[1]
                    canvas_height = self._fancygotchi._res[0]

                menu_width = self.menu_theme.get('width', 100)
                menu_height = self.menu_theme.get('height', '100%')

                menu_x, menu_y, menu_x2, menu_y2 = Fancygotchi.pos_convert(
                    self._fancygotchi,
                    self.menu_theme.get('position', [0, 0])[0],
                    self.menu_theme.get('position', [0, 0])[1],
                    menu_width,
                    menu_height,
                    r=0,
                    r0=canvas_width,
                    r1=canvas_height,
                )

                if self.menu_theme.get('bg_color', (0, 0, 0, 0)) == '': bg_color = (0,0,0,0)
                else: bg_color = self.menu_theme.get('bg_color', (0, 0, 0, 0))
                text_speed = self.menu_theme.get('motion_text_speed', 20)
                menu_width = menu_x2 - menu_x
                menu_height = menu_y2 - menu_y
   
                menu_image = Image.new("RGBA", (menu_width, menu_height), bg_color)
                draw = ImageDraw.Draw(menu_image)

                draw.rectangle([0, 0, menu_width, menu_height], fill=bg_color)

                bg_image_path = None
                if self.menu_theme.get('bg_image', None):
                    bg_image_path = os.path.join(self._fancygotchi._th_path, 'img', 'menu', self.menu_theme.get('bg_image'))
                if bg_image_path:
                    if bg_image_path not in self.loaded_images:
                        if os.path.exists(bg_image_path):
                            try:
                                bg_image = Image.open(bg_image_path)
                                self.loaded_images[bg_image_path] = bg_image
                            except Exception as e:
                                logging.warning(f"Failed to load background image: {e}")
                                self.loaded_images[bg_image_path] = None 
                        else:
                            logging.warning(f"Background image not found: {bg_image_path}")
                            self.loaded_images[bg_image_path] = None
                            
                    if self.loaded_images[bg_image_path]:
                        bg_mode = self.menu_theme.get('bg_mode', 'normal')
                        bg_tmp = image_mode(menu_image, self.loaded_images[bg_image_path], bg_mode)

                title_font_size = self.menu_theme.get('title_font_size', 'Medium')
                title_font = getattr(self._fancygotchi, title_font_size)
                title_color = self.menu_theme.get('title_color', 'black')

                if title_font:
                    title_text = current_menu.name
                    title_width, title_height = draw.textsize(title_text, font=title_font)

                    title_x, title_y, _, _ = Fancygotchi.pos_convert(
                        self._fancygotchi,
                        self.menu_theme.get('title_position', ['center', '5'])[0],
                        self.menu_theme.get('title_position', ['center', '5'])[1],
                        title_width,
                        title_height,
                        r=0,
                        r0=menu_width,
                        r1=menu_height,
                    )

                    title_size = draw.textsize(title_text, font=title_font)
                    if title_size[0] > menu_width and self.menu_theme.get('motion_text', True):
                        self.scroll_text(draw, title_text, title_color, title_text, title_font, menu_width, text_speed)
                    else:
                        draw.text((title_x, title_y), title_text, font=title_font, fill=title_color)

                btn_height = self.menu_theme.get('button_height', 15)
                btns_width = self.menu_theme.get('buttons_width', '90%')
                btns_height = self.menu_theme.get('buttons_height', '90%')
                button_spacing = self.menu_theme.get('button_spacing', 5)

                if isinstance(btns_width, str) and '%' in btns_width:
                    base_width = menu_width
                    btns_menu_width = int((base_width / 100) * int(btns_width.replace('%', '')))
                else:
                    btns_menu_width = int(btns_width)

                if isinstance(btns_height, str) and '%' in btns_height:
                    base_height = (menu_height - title_height - title_y)
                    btns_menu_height = int((base_height / 100) * int(btns_height.replace('%', '')))
                else:
                    btns_menu_height = int(btns_height)

                buttons_x, buttons_y, buttons_x1, buttons_y1 = Fancygotchi.pos_convert(
                    self._fancygotchi,
                    self.menu_theme.get('buttons_position', ['center', 'center'])[0],
                    self.menu_theme.get('buttons_position', ['center', 'center'])[1],
                    btns_width,
                    btns_height,
                    r=0,
                    r0=menu_width,
                    r1=menu_height,
                )

                button_font_size = self.menu_theme.get('button_font_size', 'Medium')
                button_font = getattr(self._fancygotchi, button_font_size, None)

                visible_buttons = (menu_height - title_height - title_y) // (btn_height + button_spacing)
                scroll_offset = max(0, current_menu.current_index - visible_buttons + 1)

                for i, (item_name, item_action) in enumerate(current_menu.items[scroll_offset:scroll_offset + visible_buttons]):
                    button_y = title_height + title_y + i * (btn_height + button_spacing)

                    if button_font:
                        button_text = item_name
                        text_width, text_height = draw.textsize(button_text, font=button_font)
                        

                    text_x, text_y, _, _ = Fancygotchi.pos_convert(
                        self._fancygotchi,
                        self.menu_theme.get('text_position', ['center', '5'])[0],
                        self.menu_theme.get('text_position', ['center', '5'])[1],
                        text_width,
                        text_height,
                        r=0,
                        r0=btns_menu_width,
                        r1=btn_height,
                    )

                    button_image = Image.new("RGBA", (btns_menu_width, btn_height), bg_color)
                    
                    button_draw = ImageDraw.Draw(button_image)
                    if self.menu_theme.get('button_bg_color', (0,0,0,0)) == '': button_bg_color = (0,0,0,0)
                    else: button_bg_color = self.menu_theme.get('button_bg_color', 'white')

                    button_bg_image_path = None
                    highlight_button_bg_image_path = None

                    if self.menu_theme.get('button_bg_image', ''):
                        button_bg_image_path = os.path.join(self._fancygotchi._th_path, 'img', 'menu', self.menu_theme.get('button_bg_image'))

                    if self.menu_theme.get('highlight_button_bg_image', ''):
                        highlight_button_bg_image_path = os.path.join(self._fancygotchi._th_path, 'img', 'menu', self.menu_theme.get('highlight_button_bg_image'))

                    if button_bg_image_path and button_bg_image_path not in self.loaded_images:
                        if os.path.exists(button_bg_image_path):
                            try:
                                button_bg_image = Image.open(button_bg_image_path)
                                button_bg_image = button_bg_image.convert("RGBA")
                                button_bg_image = button_bg_image.resize((btns_menu_width, btn_height), Image.ANTIALIAS)
                                self.loaded_images[button_bg_image_path] = button_bg_image
                            except Exception as e:
                                logging.error(f"[FancyMenu] Failed to load button background image: {e}")
                                self.loaded_images[button_bg_image_path] = None
                        else:
                            logging.warning(f"Button background image not found: {button_bg_image_path}")
                            self.loaded_images[button_bg_image_path] = None

                    if highlight_button_bg_image_path and highlight_button_bg_image_path not in self.loaded_images:
                        if os.path.exists(highlight_button_bg_image_path):
                            try:
                                highlight_button_bg_image = Image.open(highlight_button_bg_image_path)
                                highlight_button_bg_image = highlight_button_bg_image.convert("RGBA")
                                highlight_button_bg_image = highlight_button_bg_image.resize((btns_menu_width, btn_height), Image.ANTIALIAS)
                                self.loaded_images[highlight_button_bg_image_path] = highlight_button_bg_image
                            except Exception as e:
                                logging.error(f"[FancyMenu] Failed to load highlight button background image: {e}")
                                self.loaded_images[highlight_button_bg_image_path] = None
                        else:
                            logging.warning(f"Highlight button background image not found: {highlight_button_bg_image_path}")
                            self.loaded_images[highlight_button_bg_image_path] = None

                    if i + scroll_offset == current_menu.current_index:
                        highlight_color = self.menu_theme.get('highlight_color', 'black')
                        highlight_text_color = self.menu_theme.get('highlight_text_color', 'white')
                        
                        button_draw.rectangle([0, 0, btns_menu_width, btn_height], fill=highlight_color)

                        image_to_use_path = highlight_button_bg_image_path if self.loaded_images.get(highlight_button_bg_image_path) else button_bg_image_path
                        if self.loaded_images.get(image_to_use_path):
                            button_image.paste(self.loaded_images[image_to_use_path], (0, 0), self.loaded_images[image_to_use_path].split()[3])

                        button_size = button_draw.textsize(button_text, font=button_font)
                        if button_size[0] > menu_width and self.menu_theme.get('motion_text', True):
                            self.scroll_text(button_draw, button_text, highlight_text_color, button_text, button_font, menu_width, text_speed)
                        else:
                            button_draw.text((text_x, text_y), button_text, font=button_font, fill=highlight_text_color)

                    else:
                        button_text_color = self.menu_theme.get('button_text_color', 'black')
                        button_draw.rectangle([0, 0, btns_menu_width, btn_height], fill=button_bg_color)

                        if self.loaded_images.get(button_bg_image_path):
                            button_image.paste(self.loaded_images[button_bg_image_path], (0, 0), self.loaded_images[button_bg_image_path].split()[3])

                        button_size = button_draw.textsize(button_text, font=button_font)
                        if button_size[0] > menu_width and self.menu_theme.get('motion_text', True):
                            self.scroll_text(button_draw, button_text, button_text_color, button_text, button_font, menu_width, text_speed)
                        else:
                            button_draw.text((text_x, text_y), button_text, font=button_font, fill=button_text_color)
                    menu_image.paste(button_image, (buttons_x, button_y), button_image.split()[3])

                    draw.rectangle([0, 0, menu_width - 1, menu_height - 1], outline=self.menu_theme.get('border_color', 'black'))

                    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
                    canvas.paste(menu_image, (menu_x, menu_y))

                return canvas

        except Exception as e:
            logging.error(f"Failed to render menu: {e}")
            logging.error(traceback.format_exc())

    def scroll_text(self, draw, menu_item_key, color, scrolltext, scrollfont, menu_width, distance=10):
        scroll_state = self.scroll_state.get(menu_item_key, None)
        if not scroll_state:
            text_width, text_height = draw.textsize(scrolltext, font=scrollfont)
            
            scroll_state = {
                'text_width': text_width,
                'position': 10 
            }
            self.scroll_state[menu_item_key] = scroll_state

        text_width = scroll_state['text_width']
        text_position = scroll_state['position']
        draw.text((text_position, 0), scrolltext, font=scrollfont, fill=color)

        if text_position + text_width < menu_width:
            draw.text((text_position + text_width, 0), f' - {scrolltext}', font=scrollfont, fill=color)

        text_position -= distance

        if text_position + text_width <= 0:
            text_position += text_width

        self.scroll_state[menu_item_key]['position'] = text_position

class Menu:
    def __init__(self, name, items, back_reference="Main menu"):
        self.name = name
        self.back_reference = back_reference
        self.current_index = 0

        if not name == 'Main menu':
            if self.back_reference == "Main menu":
                self.items = [
                    ("Home", {"action": "submenu", "name": "Main menu"})
                ] + items
            else:
                self.items = [
                    ("Back", {"action": "submenu", "name": back_reference}),
                    ("Home", {"action": "submenu", "name": "Main menu"})
                ] + items
        else:
            self.items = items

    def navigate(self, direction):
        if direction in ['up', 'down']:
            self.current_index = (self.current_index + (1 if direction == 'down' else -1)) % len(self.items)

    def add_button(self, title, action):
        self.items.insert(0, (title, action))  

def menu_contains_button(menu, button_name):
    for item in menu.items:
        if item[0] == button_name:
            return True
    return False

MENUS = {
    'Main menu': Menu('Main menu', [
        ("Plugins", {"action": "submenu", "name": "Plugins"}),
        ("Fancygotchi",{"action": "submenu", "name": "Fancygotchi"}),
        ("System", {"action": "submenu", "name": "System"}),
    ]),
    'System': Menu('System', [
        ("Restart Auto", {"action": "restart", "mode": "auto"}),
        ("Restart Manu", {"action": "restart", "mode": "manu"}),
        ("Reboot Auto", {"action": "reboot", "mode": "auto"}),
        ("Reboot Manu", {"action": "reboot", "mode": "manu"}),
        ("Shutdown", {"action": "shutdown"}),
    ]),
    'Fancygotchi': Menu('Fancygotchi', [
        ("Theme selector", {"action": "submenu", "name": "Theme selector"}),
        ("Second screen", {"action": "submenu", "name": "Second screen"}),
        ("Theme refresh", {"action": "theme_refresh"}),
        ("Stealth mode", {"action": "stealth_mode"}),
    ]),
    'Plugins': Menu('Plugins', [
        ("Refresh plugins", {"action": "refresh_plugins"}),
        ("Plugins toggle", {"action": "submenu", "name": "Plugins toggle"}),
    ]),
    'Second screen': Menu('Second screen', [
        ('Activate second screen', {'action': 'enable_second_screen'}),
        ('Switch screen mode', {'action': 'switch_screen_mode'}),
        ('Switch screen saver mode', {'action': 'switch_screen_saver'}),
    ]),
}

def check_internet_and_repo():
    try:
        requests.get("https://www.google.com", timeout=5)
        response = requests.get(THEMES_REPO, timeout=5)
        
        if response.status_code == 200:
            return True, "Connection successful"
        else:
            error_msg = f"Repository not accessible. Status code: {response.status_code}"
            logging.warning(error_msg)
            return False, error_msg
            
    except requests.ConnectionError as e:
        error_msg = f"No internet connection: {str(e)}"
        logging.warning(error_msg)
        return False, error_msg
        
    except requests.Timeout as e:
        error_msg = f"Connection timed out: {str(e)}"
        logging.warning(error_msg)
        return False, error_msg

def get_all_plugin_names(fancygotchi):
    config_dict = fancygotchi._config 
    plugins = list(config_dict['main'].get('plugins', {}).keys())
    custom_plugins_path = config_dict['main'].get('custom_plugins', '')
    all_plugins = plugins
    return all_plugins

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def box_to_xywh(position):
    dist_1 = math.sqrt(position[0]**2 + position[1]**2)
    dist_2 = math.sqrt(position[2]**2 + position[3]**2)
    
    if dist_1 <= dist_2:
        x, y = position[0], position[1]
        x2, y2 = position[2], position[3]
    else:
        x, y = position[2], position[3]
        x2, y2 = position[0], position[1]

    w = abs(x - x2)
    h = abs(y - y2)
    
    return [x, y, w, h]

def adjust_image(image_path, zoom, mask=False, refine=150, alpha=False, invert=False, crop=[0,0,0,0]):
    try:
        if isinstance(image_path, str):
            try:
                image = Image.open(image_path)
            except Exception as e:
                logging.error(f"Error opening image: {e}")
                return None
        elif isinstance(image_path, Image.Image):
            image = image_path
        if invert:
            image = invert_pixels(image)
        if crop != [0,0,0,0]:
            image = image.crop(crop)
        image = image.convert('RGBA') 
        
        original_width, original_height = image.size
        new_width = int(original_width * zoom)
        new_height = int(original_height * zoom)

        adjusted_image = image.resize((new_width, new_height))
        if mask:
            new_img = adjusted_image
            adjusted_image = masking(new_img, refine)
        
        if alpha: 
            adjusted_image = alphamask(adjusted_image)
        
        return adjusted_image
    except Exception as e:
        logging.error("Error:", str(e))
        return None
    
def invert_pixels(image):
    try:
        image = image.convert('RGBA')
        data = list(image.getdata())
        inverted_data = [(255-r, 255-g, 255-b, a) for r, g, b, a in data]
        inverted_image = Image.new('RGBA', image.size)
        inverted_image.putdata(inverted_data)
        return inverted_image
    except Exception as e:
        logging.error(f"Error in invert_pixels: {str(e)}")
        logging.error(traceback.format_exc())
        return image  

def alphamask(src_image):
    src_image = src_image.convert('RGBA')
    data = src_image.getdata()
    newData = []
    for item in data:
        if item[0] in range(240, 256) and item[1] in range(240, 256) and item[2] in range(240, 256):
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    src_image.putdata(newData)
    src_image = src_image.convert('RGBA')
    return src_image

def masking(src_image, refine):
    image = src_image.convert('RGBA') 
    width, height = image.size
    pixels = image.getdata()
    new_pixels = []
    for pixel in pixels:
        r, g, b, a = pixel
        if a > refine:
            new_pixel = (0, 0, 0, 255)
        else:
            new_pixel = (0, 0, 0, 0)
        new_pixels.append(new_pixel)
    new_img = Image.new("RGBA", image.size)
    new_img.putdata(new_pixels)
    adjusted_image = new_img
    return adjusted_image

def image_mode(canvas, image, mode):
    w, h = canvas.size
    width, height = image.size
    logging.debug(f"Mode: {mode}")
    logging.debug(f"Image size: {width}x{height}")
    logging.debug(f"Canvas size: {w}x{h}")
    if mode == 'normal':
        image = image.convert('RGBA')
        canvas.paste(image, (0,0,width, height), image.split()[3])
    elif mode == 'stretch':
        img_resized = image.resize((w,h))
        canvas.paste(img_resized, (0, 0), img_resized)
    elif mode == 'tile':
        for x in range(0, w, image.width):
            for y in range(0, h, image.height):
                canvas.paste(image, (x, y), image)
    elif mode == 'center':
        x = (w - image.width) // 2
        y = (h - image.height) // 2
        canvas.paste(image, (x, y), image)
    elif mode == 'fit':
        original_width, original_height = image.size
        canvas_width, canvas_height = canvas.size

        original_aspect = original_width / original_height
        canvas_aspect = canvas_width / canvas_height

        if original_aspect > canvas_aspect:
            new_width = canvas_width
            new_height = int(canvas_width / original_aspect)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * original_aspect)

        image_resized = image.resize((new_width, new_height), Image.ANTIALIAS)

        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2

        canvas.paste(image_resized, (x, y), image_resized) 

    elif mode == 'fill':
        img_resized = ImageOps.fit(image, (w,h))
        canvas.paste(img_resized, (0, 0), img_resized)
    return canvas


def verify_font_info(ft):
    font_list = [fonts.Bold, fonts.BoldSmall, fonts.Medium, fonts.Huge, fonts.BoldBig, fonts.Small]

    font_info = {
        'Bold': fonts.Bold,
        'BoldSmall': fonts.BoldSmall,
        'Medium': fonts.Medium,
        'Huge': fonts.Huge,
        'BoldBig': fonts.BoldBig,
        'Small': fonts.Small
    }

    for font in font_info:
        if font_info[font].size == ft.size and font_info[font].getname() == ft.getname():
            return font
    return ft

def allowed_file(filename):
    allowed_ext = {'zip'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext

def unzip_file(zip_file, extract_to):
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    os.remove(zip_file)

def serializer(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

class Fancygotchi(plugins.Plugin):
    __author__ = 'V0rT3x'
    __github__ = 'https://github.com/V0r-T3x/fancygotchi'
    __version__ = '2.0.2'
    __license__ = 'GPL3'
    __description__ = 'The Ultimate theme manager for pwnagotchi'

    def __init__(self):
        self.pyenv = sys.executable    
        self.running = False
        self.fancy_menu = None
        self.actions_log = []
        self.second_screen = Image.new('RGBA', (1,1), 'black')
        self.fancy_menu_img = None
        self.display_config = {'mode': 'screen_saver', 'sub_mode': 'show_logo'}
        self.screen_modes = ['screen_saver', 'auxiliary', 'terminal']
        self.screen_saver_modes = ['show_logo', 'moving_shapes', 'random_colors', 'hyper_drive', 'show_animation']
        self.dispHijack = False
        self.loop = None
        self.refacer_thread = None
        self._stop_event = threading.Event()

        self.bitmap_widget = ('Bitmap', 'WardriverIcon', 'InetIcon', 'Frame')
        self._config = pwnagotchi.config
        self.gittoken = self._config['main']['plugins']['Fancygotchi'].get('github_token', None)
        logging.warning(self.gittoken)
        self.cfg_path = None
        self.cursor_list = ['█', '-']
        self.options = dict()
        self._agent = None
        self.ready = False
        self.stealth_mode = False
        self.refresh = False
        self.refresh_menu = False
        self.refresh_trigger = -1
        self.star = '*'
        logging.info(f'[Fancygotchi]{20*self.star}[Fancygotchi]{20*self.star}')
        self._pwny_root = os.path.dirname(pwnagotchi.__file__)
        self._plug_root = os.path.dirname(os.path.realpath(__file__))
        self._default = {
            'theme': {
                'options': {
                    'boot_animation': False,
                    'boot_mode': 'normal', # Implementation to adjust the boot animation image with normal, stretch, fit, fill, center or tile
                    'boot_max_loops': 1,
                    'boot_total_duration': 1,
                    'screen_mode': 'screen_saver',
                    'screen_saver': 'show_logo',
                    'second_screen_fps': 1,
                    'webui_fps': 1,
                    'second_screen_webui': False,
                    'bg_fg_select': 'manu',
                    'bg_mode': 'normal',
                    'fg_mode': 'normal',
                    'fg_image': '',
                    'bg_color': 'white',
                    'bg_image': '',
                    'bg_anim_image': '',
                    #[Bold, BoldSmall, Medium, Huge, BoldBig, Small]
                    'font_sizes': [14, 9, 14, 25, 19, 9],
                    'font': 'DejaVuSansMono',
                    'font_bold': 'DejaVuSansMono-Bold',
                    'status_font': 'DejaVuSansMono',
                    'font_awesome': '',
                    'size_offset': 5,
                    'label_spacing': 9,
                    'label_line_spacing': 0,
                    'cursor': '❤',
                    'friend_bars': '▌',
                    'friend_no_bars': '│',
                    'base_text_color': ['black'],
                    'main_text_color': ['black'],
                    'color_mode': ['P', 'P']
                },
                'widget': {}
            }
        }
        self._default_menu = {
            'motion_text': True,
            'motion_text_speed': 20,

            'bg_select': 'manu',
            'bg_mode': 'normal',

            'position': [0, 0],
            'title_position': ['center', '5'],
            'title_font_size': 'Medium',
            'title_color': 'black',
            'width': 100,
            'height': '100%',

            'buttons_position': ['center', '5'],
            'buttons_width': '90%',
            'button_height': 15,
            'button_spacing': 3,

            'bg_color': 'white',
            'border_color': 'black',
            'highlight_color': 'black',
            'highlight_border_color': 'white',
            'highlight_text_color': 'white',
            'button_bg_color': 'white',
            'button_bg_border_color': 'black',
            'button_text_color': 'black',

            'bg_image': "",
            'button_bg_image': "",
            'highlight_button_bg_image': "",

            'text_position': ['center', 'center'],
            'button_font_size': "Medium",
            'timeout': 30,
        }
        text_widget_defaults = {
            'position': [0, 0],
            'color': ['#000000'],
            'z_axis': 0,
            'text_font': '',
            'text_font_size': "Medium",
            'size_offset': 0,
            'icon': False,
            'icon_color': False,
            'invert': False,
            'alpha': False,
            'crop': [0,0,0,0],
            'mask': False,
            'refine': 150,
            'zoom': 1,
            'image_type': 'png',
            'wrap': False,
            'max_length': 0
        }
        labeledvalue_widget_defaults = {
            'position': [0, 0],
            'color': ['#000000'],
            'z_axis': 0,
            'text_font': '',
            'text_font_size': "Medium",
            'size_offset': 0,
            'icon': False,
            'icon_color': False,
            'invert': False,
            'alpha': False,
            'crop': [0,0,0,0],
            'mask': False,
            'refine': 150,
            'zoom': 1,
            'label': '',
            'label_font': '',
            'label_font_size': "Medium",
            'label_spacing': 0,
            'label_line_spacing': 0,
            'f_awesome': False,
            'f_awesome_size': 0
        }
        line_widget_defaults = {
            'position': [0, 0, 0, 0],
            'color': ['#000000'],
            'z_axis': 0,
            'width': 1
        }
        rect_widget_defaults = {
            'position': [0, 0, 0, 0],
            'color': ['#000000'],
            'z_axis': 0
        }
        filledrect_widget_defaults = {
            'position': [0, 0, 0, 0],
            'color': ['#000000'],
            'z_axis': 0
        }
        bitmap_widget_defaults = {
            'position': [0, 0],
            'color': ['#000000'],
            'z_axis': 0,
            'icon': False,
            'invert': False,
            'alpha': False,
            'crop': [0,0,0,0],
            'mask': False,
            'refine': 150,
            'zoom': 1,
            'icon_color': False,
        }
        self.widget_defaults = {
            'Text': text_widget_defaults,
            'LabeledValue': labeledvalue_widget_defaults,
            'Line': line_widget_defaults,
            'Rect': rect_widget_defaults,
            'FilledRect': filledrect_widget_defaults,
            'Bitmap': bitmap_widget_defaults
        }
        
        self._theme_name = 'Default'
        self._theme = copy.deepcopy(self._default)
        self._th_path = None
        self._res = []
        self._color_mode = ['P', 'P']
        self._bg = ''
        self._fg = ''
        self._i = 0
        self._imax = None
        self._frames = []
        self._icolor = 0
        self.font_name = 'DejaVuSansMono'
        self.font_bold_name = 'DejaVuSansMono-Bold'
        self.f_awesome_name = ''
        self.Bold = None
        self.BoldSmall = None
        self.BoldBig = None
        self.Medium = None
        self.Small = None
        self.Huge = None
        self._state = {}
        self._state_default = {}

        self.Tag = '# Pwned by V0rT3x'
        v_code = [{'replace': False, 
                    'reference': 'lv.draw(self._canvas, drawer)',
                    'paste': """
                if hasattr(self, '_pwncanvas'):
                    rot = pwnagotchi.config['main']['plugins']['Fancygotchi']['rotation']
                    if self._pwncanvas_tmp is not None:
                        self._pwncanvas = self._pwncanvas_tmp
                        self._pwncanvas_tmp = None
                    if self._pwncanvas is not None:
                        if isinstance(self._pwncanvas, Image.Image):
                            self._canvas = self._canvas.convert('RGBA')
                            self._canvas.paste(self._pwncanvas, (0, 0), self._pwncanvas)
                    web_tmp = self._canvas
                    hw_tmp = self._canvas
                    if rot in [90,270]: hw_tmp = hw_tmp.rotate(-90, expand=True)
                    self._canvas = hw_tmp.convert(self._web_mode)"""},
                    {'replace': False, 'reference': 'web.update_frame(self._canvas)',
                    'paste':"""                if hasattr(self, '_pwncanvas'):
                    self._canvas = hw_tmp.convert(self._hw_mode)
                    if rot == 90: self._canvas = self._canvas.rotate(90, expand=True)
                    if rot == 270: self._canvas = self._canvas.rotate(-90, expand=True)
                    if rot == 180: self._canvas = self._canvas.rotate(180)"""}]
        s_code = [{'replace': False, 
                    'reference': 'self._listeners[key](prev, value)',
                    'paste': """
    # Start of the Fancygotchi hack                    
    def get_attr(self, key, attribute='value'):
        with self._lock:
            if key in self._state:
                return getattr(self._state[key], attribute)
            else:
                return None
    # End of the Fancygotchi hack
    """}]
        i_code = [{'replace': False, 'reference': 'import logging', 'paste': 'import shutil'},
                    {'replace': True, 
                    'reference': """                self._view.on_keys_generation()
                logging.debug("generating %s ..." % self.priv_path)
                os.system("pwngrid -generate -keys '%s'" % self.path)""",
                    'paste': """                if os.path.exists(f'{self.priv_path}.backup') and os.path.exists(f'{self.pub_path}.backup') and os.path.exists(f'{self.fingerprint_path}.backup'):
                    shutil.copy(f'{self.priv_path}.backup', self.priv_path)
                    shutil.copy(f'{self.pub_path}.backup', self.pub_path)
                else:
                    self._view.on_keys_generation()
                    logging.debug("generating %s ..." % self.priv_path)
                    os.system("pwngrid -generate -keys '%s'" % self.path)"""},
                    {'replace': False, 'reference': 'self._view.on_starting()',
                    'paste': """                if not os.path.exists(f'{self.priv_path}.backup'):
                    shutil.copy(self.priv_path, f'{self.priv_path}.backup')
                if not os.path.exists(f'{self.pub_path}.backup'):
                    shutil.copy(self.pub_path, f'{self.pub_path}.backup')
                if not os.path.exists(f'{self.fingerprint_path}.backup'):
                    shutil.copy(self.fingerprint_path, f'{self.fingerprint_path}.backup')"""}]
        p_code  = [{'replace': False, 
                'reference': 'source /usr/bin/pwnlib',
                'paste': f"""
if [ -f "/usr/local/bin/boot_animation.py" ]; then
    {self.pyenv} /usr/local/bin/boot_animation.py
fi"""}]
        v_f = os.path.join(self._pwny_root, 'ui', 'view.py')
        s_f = os.path.join(self._pwny_root, 'ui', 'state.py')
        i_f = os.path.join(self._pwny_root, 'identity.py')
        p_f = '/usr/bin/pwnagotchi-launcher'
        rst = 0
        if self.adjust_code(v_f, v_code): rst = 1
        if self.adjust_code(s_f, s_code): rst = 1
        if self.adjust_code(i_f, i_code): rst = 1
        if self.adjust_code(p_f, p_code): rst = 1
        if self.zram_check(): rst = 1
        self.check_and_fix_fb()
        if rst:
            self.log('The pwnagotchi need to restart.')
            os.system('sudo systemctl restart pwnagotchi.service')
            os.system('sudo service pwnagotchi restart')
        self.log('Initiated')

    def adjust_code(self, file_path, changes):
        self.log(f'Adjusting code in {file_path}')
        rst = 0
        with open(file_path, 'r') as file:
            lines = file.readlines()

        for code in changes:
            replace_flag = code.get('replace', False)
            reference_lines = code.get('reference', '').split('\n')
            paste_code = code.get('paste', '')

            if not lines[-1].strip() == self.Tag:
                reference_index = 0
                for i, line in enumerate(lines):
                    if reference_index < len(reference_lines) and reference_lines[reference_index] in line:
                        reference_index += 1
                    else:
                        reference_index = 0
                    if reference_index == len(reference_lines):
                        if replace_flag:
                            lines[i - len(reference_lines) + 1:i + 1] = [paste_code + '\n']
                        else:
                            lines[i] = lines[i].rstrip() + '\n' + paste_code + '\n'
                        rst = 1
        if rst:
            lines.append(self.Tag + '\n')
        with open(file_path, 'w') as file:
            file.writelines(lines)
        
        return rst

    def check_and_fix_fb(self):
        config_paths = [
            "/boot/firmware/config.txt",
            "/boot/config.txt"
        ]
        correct_overlay = "dtoverlay=vc4-fkms-v3d"
        wrong_overlay = "dtoverlay=vc4-kms-v3d"

        fb_device_exists = any(os.path.exists(f"/dev/fb{i}") for i in range(10))
        self.log(f"[Fancygotchi] Framebuffer device exists: {fb_device_exists}")
        config_file = None
        for path in config_paths:
            if os.path.exists(path):
                config_file = path
                break

        if not config_file:
            return

        with open(config_file, 'r') as file:
            lines = file.readlines()

        found_correct_overlay = any(correct_overlay in line for line in lines)

        if fb_device_exists:
            self.log("[Fancygotchi] Framebuffer device exists. No reboot needed.")
            return
        elif found_correct_overlay:
            self.log("[Fancygotchi] config.txt already contains the correct overlay. No reboot needed.")
            return
        else:
            self.log("[Fancygotchi] Framebuffer device does not exist config.txt already don't contain the correct overlay. Rebooting system to apply changes...")

        backup_path = config_file + ".bak"
        shutil.copy(config_file, backup_path)
        with open(config_file, 'r') as file:
            lines = file.readlines()
        found_wrong_overlay = False
        found_correct_overlay = False
        new_lines = []
        for line in lines:
            if wrong_overlay in line:
                found_wrong_overlay = True
                new_lines.append(line.replace(wrong_overlay, correct_overlay))
            elif correct_overlay in line:
                found_correct_overlay = True
                new_lines.append(line)
            else:
                new_lines.append(line)
        if not found_correct_overlay:
            new_lines.append(f"\n{correct_overlay}\n")
            self.log(f"{correct_overlay} added to {config_file}")
        with open(config_file, 'w') as file:
            file.writelines(new_lines)
        self.log("Rebooting system to apply changes...")
        subprocess.run(["sudo", "reboot"])

    def zram_check(self):
        rst = 0
        if 'fs' in self._config and 'memory' in self._config['fs'] and 'mounts' in self._config['fs']['memory'] and 'data' in self._config['fs']['memory']['mounts']:
            fs_data = self._config['fs']['memory']['mounts']['data']
            if 'enabled' in fs_data and fs_data['enabled']:
                if 'mount' != '': mount = fs_data['mount']
                else: self._config['fs']['memory']['mounts']['data']['mount'] = "/var/tmp/pwnagotchi"
                if 'zram' in fs_data and fs_data['zram']:
                    if 'size' in fs_data:
                        size = num_size = int(re.search(r'\d+', fs_data['size']).group())
                        if num_size < 50:
                            self._config['fs']['memory']['mounts']['data']['size'] = '50M' 
                            save_config(self._config, '/etc/pwnagotchi/config.toml')
                            rst= 1
        return rst

    def log(self, msg):
        try:
            # working state
            # log = False
            # debug = True
            log = False
            debug = True

            if 'theme' in self._theme and 'dev' in self._theme['theme'] and 'log' in self._theme['theme']['dev']:
                log = self._theme['theme']['dev']['log']

            if 'theme' in self._theme and 'dev' in self._theme['theme'] and 'debug' in self._theme['theme']['dev']:
                debug = self._theme['theme']['dev']['debug']

            if log:
                if debug: logging.debug(msg)
                else: logging.info(f'[Fancygotchi] {msg}')
        except Exception as ex:
            logging.error(ex)

    def on_ready(self, agent):
        self._agent = agent
        self.mode = 'MANU' if agent.mode == 'manual' else 'AUTO'

    def on_loaded(self):
        logging.info("[Fancygotchi] Loaded")
        self.ready = True

    def on_unload(self, ui):
        with ui._lock:
            self.cleanup_display()
            self.dispHijack = False
            if not self.dispHijack:
                if hasattr(self, 'display_controller') and self.display_controller:
                    self.display_controller.stop()
                logging.warning(ui._enabled)
                if hasattr(ui, '_enabled') and not ui._enabled:
                    ui._enabled = True
                    logging.warning("[Fancygotchi] Switched back to the original display.")
        if self._config['ui']['display']['enabled']:
            ui._enabled = True
            ui.init_display()

            self.cleanup_display()
        self.cleanup_fancyserver()
        if hasattr(self, 'listener'):
            self.listener.close()
        if hasattr(ui, '_pwncanvas'):
            del ui._pwncanvas
        if hasattr(ui, '_pwncanvas_tmp'):
            del ui._pwncanvas_tmp
        if hasattr(ui, '_update'):
            del ui._update
        if hasattr(ui, '_web_mode'):
            del ui._web_mode
        if hasattr(ui, '_hw_mode'):
            del ui._hw_mode
        screenshots_path = os.path.join(self._pwny_root, 'ui/web/static/screenshots')
        if os.path.exists(screenshots_path):
            os.system(f'rm -r {screenshots_path}')
        repo_screenshots_path = os.path.join(self._pwny_root, 'ui/web/static/repo_screenshots')
        if os.path.exists(repo_screenshots_path):
            os.system(f'rm -r {repo_screenshots_path}')
        css_dst = os.path.join(self._pwny_root, 'ui/web/static/css/style.css')
        css_backup = css_dst + '.backup'
        if os.path.exists(css_backup):
            copyfile(css_backup, css_dst)
            os.remove(css_backup)
        img_dst = os.path.join(self._pwny_root, 'ui/web/static/img')
        if os.path.islink(img_dst):
            os.unlink(img_dst)
        font_dst = '/usr/share/fonts/truetype/theme_fonts'
        os.system('rm %s' % (font_dst))
        icon_dst = os.path.join(self._pwny_root, 'ui/web/static/images/pwnagotchi.png')
        icon_bkup = icon_dst + '.backup'
        if os.path.exists(icon_bkup):
            copyfile(icon_bkup, icon_dst)
            os.remove(icon_bkup)
        fancytools_path = "/usr/local/bin/fancytools"
        if os.path.exists(fancytools_path):
            os.remove(fancytools_path)
        diagnostic_path = "/usr/local/bin/diagnostic.sh"
        if os.path.exists(diagnostic_path):
            os.remove(diagnostic_path)

        logging.info('[Fancygotchi] Unloaded')

    def on_ui_setup(self, ui):
        logging.info('[Fancygotchi] UI setup start')
        setattr(ui, '_pwncanvas_tmp', None)
        setattr(ui, '_pwncanvas', None)
        setattr(ui, '_web_mode', self._color_mode[0])
        setattr(ui, '_hw_mode', self._color_mode[1])
        setattr(ui, '_update', {
            'update': True,
            'partial': False,
            'dict_part': {}
        })
        self._res = [ui._width, ui._height]
        self.theme_update(ui, True)
        self.pwncanvas_creation(self._res)
        self.display_controller = FancyDisplay(self._config['ui']['display']['enabled'], self.fps, self._th_path, )
        self.log('UI setup finished')

    def cleanup_display(self):

        if hasattr(self, 'display_controller') and self.display_controller:
            if self.display_controller.is_running():
                self.display_controller.stop()
            self.display_controller = None
            del self.display_controller

    def cleanup_fancyserver(self):
        if hasattr(self, 'fancy_server'):
            if self.fancy_server and self.fancy_server.running:
                self.fancy_server.stop()
            
            self.fancy_server = None

        if hasattr(self, 'fancy_menu'):
            del self.fancy_menu
        
        if hasattr(self, 'fancyserver'):
            self.fancyserver = False


    def navigate_fancymenu(self, cmd=None):
        try:
            if hasattr(self, 'fancy_menu'):
                if cmd:
                    menu_command = cmd
                else:
                    menu_command = self.check_menu_command()
                if menu_command:
                    cmd = menu_command['action']
                    self.log(f'menu_command: {cmd}')
                    if cmd == 'menu_toggle':
                        self.fancy_menu.toggle()
                        self.log('toggle menu')
                    elif cmd in ['menu_up', 'menu_down', 'menu_left', 'menu_right']:
                        direction = cmd.split('_')[1]
                        self.fancy_menu.navigate(direction)
                        self.log(direction)
                    elif cmd == 'menu_select':
                        self.fancy_menu.select()
                        self.log('select')
        except Exception as e:
            logging.error(f"Error in navigate_fancymenu: {e}")
            logging.error(traceback.format_exc())

    def on_ui_update(self, ui):
        try:
            if not self.dispHijack:
                if hasattr(self, 'display_controller') and self.display_controller:
                    self.display_controller.stop()
                    self.display_controller = None
                if self._config['ui']['display']['enabled']:
                    if hasattr(ui, '_enabled') and not ui._enabled:
                        ui._enabled = True
                        ui.init_display()
                        logging.debug("[Fancygotchi] Switched back to the original display.")
            else:
                ui._enabled = False
                if hasattr(self, 'display_controller') and not self.display_controller:
                    logging.debug("[Fancygotchi] Starting display hijack.")
                    self.display_controller = FancyDisplay(self._config['ui']['display']['enabled'], self.fps, self._th_path)
                    self.display_controller.start(self._res, self.options.get('rotation', 0), self._color_mode[1])
                    mode = self.display_config.get('mode', 'screen_saver')
                    submode = self.display_config.get('sub_mode', 'show_logo')
                    config = self.display_config.get('config', {})
                    self.display_controller.set_mode(mode, submode, config)
                else:
                    logging.debug("[Fancygotchi] Display controller is already running.")
 

            self._res = [ui._width, ui._height]
            self.second_screen = Image.new('RGBA', self._res, 'black')
            if hasattr(ui, '_update') and isinstance(ui._update, dict) and ui._update.get('update', {'update': False, 'partial': False, 'dict_part':[]}) or self.refresh:
                self.theme_update(ui)
                if hasattr(ui, '_update'):
                    ui._update['update'] = False
                    ui._update['partial'] = False
                    ui._update['dict_part'] = {}
                self.refresh = False
            th = self._theme['theme']
            th_opt = th['options']
            th_widget = th['widget']
            rot = self.options['rotation']
            self.pwncanvas_creation(self._res)
            self.remove_widgets(ui)
            ui_state = list(ui._state.items())
            for key, state in ui_state:
                widget_type = type(state).__name__
                if widget_type in self.bitmap_widget:
                    widget_type = 'Bitmap'
                self.add_widget(ui, key, widget_type, th_widget)
                if  widget_type == 'Text' or widget_type == 'LabeledValue':
                    if not 'value' in self._state[key]:
                        self._state[key].update({'value': None})
                    self._state[key]['value'] = ui._state.get(key)
                    
                    if key == 'name':
                        custom_char = th_opt["cursor"]

                        name_value = ui._state.get(key)

                        for char in self.cursor_list:
                            if name_value.endswith(char):
                                name_value = name_value.rstrip(char) + f' {custom_char}'
                                break 

                        self._state[key]['value'] = name_value

                    if key == 'friend_name' and ui._state.get(key) != None:
                        friend_name = ui._state.get(key)
                        friend_name = friend_name.replace('▌', th_opt['friend_bars']).replace('│', th_opt['friend_no_bars'])
                    
                    value = self._state[key]['value']
                if widget_type == 'Bitmap':
                    
                    if key in th_widget and th_widget[key].get('icon'):
                        img_ref = ui._state.get_attr(key, 'image') 
                        if key in self._state and 'image_dict' in self._state[key]:
                            img_map = self._state[key].get('image_dict')
                            matched_custom_image = None
                            for id_number, (img_a, img_b) in img_map.items():
                                if ImageChops.difference(img_a, img_ref).getbbox() is None:
                                    matched_custom_image = img_b
                                    break  
                            if matched_custom_image:
                                self._state[key].update({'image': matched_custom_image})
                            else:
                                self.log('No matching image found.')
                    else:
                        if 'image_dict' not in self._state[key]:
                            self._state[key]['image_dict'] = {}

                        image_dict = self._state[key]['image_dict']
                        original_img = ui._state.get_attr(key, 'image')

                        corresponding_adj_img = None

                        for i, (orig, adj) in image_dict.items():
                            try:
                                if orig == original_img:
                                    corresponding_adj_img = adj
                                    break
                            except AttributeError:
                                continue

                        if corresponding_adj_img is None:
                            i = len(image_dict)
                            try:
                                corresponding_adj_img = adjust_image(original_img, self._state[key]['zoom'], False, self._state[key]['refine'], self._state[key]['alpha'], self._state[key]['invert'])
                                image_dict[i] = [original_img, corresponding_adj_img]
                            except AttributeError:
                                corresponding_adj_img = original_img

                        self._state[key].update({'image_dict': image_dict})

                        self._state[key].update({'image': corresponding_adj_img})

            if 'theme' in self._theme and 'dev' in self._theme['theme'] and 'refresh' in self._theme['theme']['dev']:
                self.refresh_trigger = self._theme['theme']['dev']['refresh']

            if hasattr(self, 'fancyserver') and self.fancyserver and self.fancyserver and hasattr(self, 'fancy_menu'):
                menu_command = self.check_menu_command()
                if menu_command:
                    cmd = menu_command['action']
                    if self.dispHijack:
                        if cmd == 'menu_toggle':
                                self.dispHijack = False
                        elif self.display_config['mode'] == 'screen_saver':
                            if cmd == 'menu_up':
                                logging.warning('switch screen saver mode')
                                self.process_actions({'action': 'next_screen_saver'})
                            elif cmd == 'menu_down':
                                logging.warning('switch screen saver mode')
                                self.process_actions({'action': 'previous_screen_saver'})
                            else:
                                self.process_actions(menu_command)
                        elif self.display_config['mode'] == 'auxiliary':
                            logging.warning('enable auxiliary mode')
                            self.process_actions(menu_command)
                        elif self.display_config['mode'] == 'terminal':
                            self.process_actions(menu_command)
                        else:
                            self.process_actions(menu_command)
                        
                    elif self.fancy_menu.active:
                        self.log(f'menu_command: {menu_command}')
                        self.log(f'menu_command: {cmd}')
                        if cmd == 'menu_toggle':
                            self.process_actions(menu_command)
                        elif cmd in ['menu_up', 'menu_down', 'menu_left', 'menu_right']:
                            direction = cmd.split('_')[1]
                            self.fancy_menu.navigate(direction)
                            self.log(direction)
                        elif cmd == 'menu_select':
                            menu_cmd = self.fancy_menu.select()
                            self.log(f'menu command:{menu_cmd}')
                            try:
                                self.process_actions(menu_cmd)
                            except OSError as e:
                                logging.error(f'error while processing command: {e}')
                        else:
                            self.process_actions(menu_command)
                    else:
                        self.process_actions(menu_command)

            if self._i == self.refresh_trigger:
                self.theme_update(ui)

            self.drawer()

            if rot == 90 or rot == 270:
                self._pwncanvas = self._pwncanvas.rotate(90, expand=True)

            if hasattr(ui, '_pwncanvas_tmp') and ui._pwncanvas_tmp == None:
                setattr(ui, '_pwncanvas_tmp', self._pwncanvas)
            if hasattr(ui, '_pwncanvas') and ui._pwncanvas == None:
                setattr(ui, '_pwncanvas', self._pwncanvas)

            if self._imax != None:
                if self._imax - 1 == self._i:
                    self._i = 0
                else:
                    self._i += 1

        except Exception as e:
            self.log("non fatal error while updating Fancygotchi: %s" % e)
            self.log(traceback.format_exc())
    
    # Theme section
    def generate_default_config(self, config_path, actual_state):
        default_config = {
            'theme': {
                'options': copy.deepcopy(self._default['theme']['options']),
                'menu': {
                    'options': copy.deepcopy(self._default_menu),
                },
                'widget': {}
            }
        }

        for widget_name, state in actual_state.items():
            widget_type = state['widget_type']
            if widget_type in self.bitmap_widget:
                widget_type = 'Bitmap'
            default_widget_config = self.widget_defaults.get(widget_type, {})
            
            default_config['theme']['widget'][widget_name] = copy.deepcopy(default_widget_config)

        for widget_name, state in self._state_default.items():
            if widget_name in default_config['theme']['widget']:
                default_config['theme']['widget'][widget_name].update(state)

                if 'widget_type' in default_config['theme']['widget'][widget_name]:
                    del default_config['theme']['widget'][widget_name]['widget_type']

        with open(config_path, 'w') as f:
            toml.dump(default_config, f)

        logging.debug(f"Default configuration saved to {config_path}")
        return default_config

    def check_menu_command(self):
        if hasattr(self, 'fancy_server'):
            command = self.fancy_server.get_last_command()
            return command
        return None

    def refresh_plugins(self):
        new_plugs = ''
        if 'custom_plugins' in self._agent._config['main']:
            path = self._agent._config['main']['custom_plugins']
            logging.debug("loading plugins from %s" % (path))
            for filename in glob.glob(os.path.join(path, "*.py")):
                plugin_name = os.path.basename(filename.replace(".py", ""))
                if not plugin_name in plugins.database:
                    logging.debug("New plugin: %s" % (plugin_name))
                    plugins.database[plugin_name] = filename
                    new_plugs += ",%s" % plugin_name
            if new_plugs != '':
                self.log("found new:%s" % (new_plugs))


    def load_and_run_module(self, module_path):
        if module_path.startswith('/'): module_file_path = module_path
        else: module_file_path = os.path.join(self._th_path, 'scripts', module_path)
        
        if not os.path.exists(module_file_path):
            self.log(f"Module file {module_file_path} does not exist.")
            return
        
        try:
            module_name = os.path.splitext(os.path.basename(module_file_path))[0] 
            spec = importlib.util.spec_from_file_location(module_name, module_file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'main'): 
                module.main()
            else:
                self.log(f"Module {module_name} imported successfully, but no 'main' function found.")
        
        except Exception as e:
            logging.error(f"Error while loading and executing module {module_file_path}: {e}")
            logging.error(traceback.format_exc())

    def process_actions(self, command):
        if command is None:
            logging.error("[Fancygotchi] Action is None, unable to process.")
            return
        try:
            action = command.get('action')
            mode = command.get('mode', 'manu')
            self.actions_log.append(action)
            self.actions_log = self.actions_log[-12:]
            self.log(f'Action: {action}')

            if action == 'submenu':
                self.fancy_menu.navigate("right")
            elif action == 'menu_toggle':
                self.fancy_menu.toggle()
            elif action == 'menu_plugin':
                name = command.get('name')
                state = command.get('enable')
                if name != 'None' and name is not None:
                    self.log(f'Plugin command: {name}, state: {state}')
                    is_change = toggle_plugin(name, enable=state)
                    self.log(f'{name} {"changed state" if is_change else "did not change state"}')
            elif action == 'refresh_plugins':
                self.refresh_plugins()
            elif action == 'shutdown':
                pwnagotchi.shutdown()
            elif action == 'restart':
                pwnagotchi.restart(mode)
            elif action == 'reboot':
                pwnagotchi.reboot(mode)
            elif action == 'theme_select':
                name = command.get('name')
                rotation = command.get('rotation')
                self.theme_save_config(name, rotation, True)
                self.refresh = True
            elif action == 'theme_refresh':
                self.refresh = True
            elif action == 'stealth_mode':
                self.stealth_mode = not self.stealth_mode
                self.refresh = True
            elif action == 'switch_screen_mode':
                try:
                    self.display_config['mode'] = self.display_controller.switch_mode()
                except:
                    self.display_config['mode'] = self.screen_modes[(self.screen_modes.index(self.display_config['mode']) + 1) % len(self.screen_modes)]
            elif action == 'switch_screen_mode_reverse':
                try:
                    self.display_config['mode'] = self.display_controller.switch_mode('previous')
                except:
                    self.display_config['mode'] = self.screen_modes[(self.screen_modes.index(self.display_config['mode']) - 1) % len(self.screen_modes)]
            elif action == 'enable_second_screen':
                self.dispHijack = True
                self.fancy_menu.active = False
            elif action == 'disable_second_screen':
                logging.warning('disable second screen')
                self.dispHijack = False
            elif action == 'next_screen_saver':
                logging.warning('next screen saver')
                try:
                    self.display_config['sub_mode'] = self.display_controller.switch_screen_saver_submode('next')
                except:
                    self.display_config['sub_mode'] = self.screen_saver_modes[(self.screen_saver_modes.index(self.display_config['sub_mode']) + 1) % len(self.screen_saver_modes)]
            elif action == 'previous_screen_saver':
                logging.warning('previous screen saver')
                try:
                    self.display_config['sub_mode'] =  self.display_controller.switch_screen_saver_submode('previous')
                except:
                    self.display_config['sub_mode'] = self.screen_saver_modes[(self.screen_saver_modes.index(self.display_config['sub_mode']) + 1) % len(self.screen_saver_modes)]
            elif action == 'run_bash':
                script = command.get('file')
                if script.startswith('/'): script_path = script
                else: script_path = os.path.join(self._th_path, 'scripts', script)
                if os.path.exists(script_path):
                    self.log(f'Running script: {script_path}')
                    os.system(f'chmod +x {script_path}')
                    self.log(f'Running command: {script_path}')
                    exit_code = os.system(f'{script_path}')
                    self.log(f"Script exited with code: {exit_code}")
                else:
                    self.log(f"Script not found: {script_path}")
            elif action == 'run_python':
                file_path = command.get('file')
                self.load_and_run_module(file_path)

        except Exception as e:
            logging.error(f'error while processing menu command: {e}')

    def theme_creator(self, theme_name, state, oriented=False, resolution=False):
        themes_folder = os.path.join(self._plug_root, 'themes')
        res = ''

        new_theme_folder = os.path.join(themes_folder, theme_name)
        
        if os.path.exists(new_theme_folder):
            self.log(f"Theme '{theme_name}' already exists. Skipping creation.")
            return False

        os.makedirs(new_theme_folder, exist_ok=True)

        folders = ['config', 'img', 'fonts']
        for folder in folders:
            os.makedirs(os.path.join(new_theme_folder, folder), exist_ok=True)

        img_subfolders = ['bg', 'face', 'friend_face', 'widgets', 'icons']
        for subfolder in img_subfolders:
            os.makedirs(os.path.join(new_theme_folder, 'img', subfolder), exist_ok=True)

        if resolution:
            res = f'{self._res[0]}x{self._res[1]}'
            os.makedirs(os.path.join(new_theme_folder, 'config', res), exist_ok=True)

        info_json = {
            "author": "",
            "version": "1.0.0",
            "resolutions": "",
            "display": "",
            "plugins": ["", ""],
            "notes": ""
        }
        with open(os.path.join(new_theme_folder, 'info.json'), 'w') as f:
            json.dump(info_json, f, indent=2)

        original_css_backup = os.path.join(self._pwny_root, 'ui/web/static/css/style.css.backup')
        original_css_path = os.path.join(self._pwny_root, 'ui/web/static/css/style.css')
        new_css_path = os.path.join(new_theme_folder, 'style.css')

        with open(new_css_path, 'w+') as f:
            f.write(CSS)

        config_path = os.path.join(new_theme_folder, 'config')
        if resolution:
            config_path_res = os.path.join(config_path, res)
            if oriented:
                config_path = os.path.join(config_path_res, 'config-h.toml')
                self.generate_default_config(config_path, state)
                config_path = os.path.join(config_path_res, 'config-v.toml')
                self.generate_default_config(config_path, state)
            else:
                config_path = os.path.join(config_path_res, 'config.toml')
                self.generate_default_config(config_path, state)
        else:
            if oriented:
                config_path_uni = config_path
                config_path = os.path.join(config_path_uni, 'config-h.toml')
                self.generate_default_config(config_path, state)
                config_path = os.path.join(config_path_uni, 'config-v.toml')
                self.generate_default_config(config_path, state)
            else:
                config_path = os.path.join(config_path, 'config.toml')
                self.generate_default_config(config_path, state)

        return True

    def theme_selector(self, config, boot=False):
        self._theme = {} 
        th_path = None
        self._theme_name = 'Default'
        self.fancyserver = False
        try:
            if not boot: self.log('Theme selector')
            self._theme = copy.deepcopy(self._default)
            fancy_opt = config['main']['plugins']['Fancygotchi']
            self.options['rotation'] = fancy_opt.get('rotation', 0)

            size = f'{self._res[0]}x{self._res[1]}'
            if 'theme' in fancy_opt and fancy_opt['theme'] != '':
                theme = fancy_opt['theme']
                self._theme_name = theme
                rot = fancy_opt['rotation']
                th_path = os.path.join(self._plug_root, 'themes', theme)
                self._th_path = th_path

                cfg_path = os.path.join(th_path, "config")

                if not os.path.exists(cfg_path):
                    self.log(f"Warning: Theme config folder {cfg_path} does not exist, loading default theme.")
                    self._theme = copy.deepcopy(self._default)
                    return

                toml_files = [f for f in os.listdir(cfg_path) if f.endswith('.toml')]
                
                if len(toml_files) == 1:
                    cfg_file = toml_files[0]
                elif 'config-v.toml' in toml_files and 'config-h.toml' in toml_files:
                    cfg_file = 'config-v.toml' if rot in [90, 270] else 'config-h.toml'
                else:
                    size_folder = os.path.join(cfg_path, size)
                    if os.path.exists(size_folder):
                        size_toml_files = [f for f in os.listdir(size_folder) if f.endswith('.toml')]
                        if len(size_toml_files) == 1:
                            cfg_file = os.path.join(size, size_toml_files[0])
                        else:
                            cfg_file = os.path.join(size, 'config-v.toml' if rot in [90, 270] else 'config-h.toml')
                    else:
                        cfg_file = 'config-h.toml'

                self.cfg_path = os.path.join(cfg_path, cfg_file)

                if os.path.exists(self.cfg_path):
                    with open(self.cfg_path, 'r') as f:
                        self._theme = toml.load(f)
                else:
                    self._theme = copy.deepcopy(self._default)

            else:
                self._theme = copy.deepcopy(self._default)
            if th_path:
                css_src = os.path.join(th_path, 'style.css')
                css_dst = os.path.join(self._pwny_root, 'ui/web/static/css/style.css')
                css_backup = css_dst + '.backup'
                if os.path.exists(css_src):
                    if not os.path.exists(css_backup):
                        copyfile(css_dst, css_backup)
                    copyfile(css_src, css_dst)

                img_src = os.path.join(th_path, 'img')
                img_dst = os.path.join(self._pwny_root, 'ui/web/static')
                icon_src = os.path.join(th_path, 'img', 'icons', 'favicon.png')
                icon_dst = os.path.join(self._pwny_root, 'ui/web/static/images/pwnagotchi.png')
                icon_bkup = icon_dst + '.backup'
                icon_dst_dir = os.path.dirname(icon_dst)
                if not os.path.exists(icon_dst_dir):
                    os.makedirs(icon_dst_dir)

                if os.path.exists(icon_src):
                    if not os.path.exists(icon_bkup):
                        if not os.path.exists(icon_dst):
                            copyfile(icon_src, icon_dst)
                        else:
                            copyfile(icon_dst, icon_bkup)
                    copyfile(icon_src, icon_dst)
                else:
                    if os.path.exists(icon_bkup):
                        copyfile(icon_bkup, icon_dst)
                        os.remove(icon_bkup)
                if os.path.exists(img_dst):
                    os.system('rm %s/img' % (img_dst))
                if os.path.exists(img_src):
                    os.system('ln -s %s %s' % (img_src, img_dst))
            else:
                icon_dst = os.path.join(self._pwny_root, 'ui/web/static/images/pwnagotchi.png')
                icon_bkup = icon_dst + '.backup'
                css_dst = os.path.join(self._pwny_root, 'ui/web/static/css/style.css')
                css_backup = css_dst + '.backup'
                if os.path.exists(css_backup):
                    copyfile(css_backup, css_dst)
                    os.remove(css_backup)
                if os.path.exists(icon_bkup):
                    copyfile(icon_bkup, icon_dst)
                    os.remove(icon_bkup)

            if 'fancyserver' in fancy_opt:
                self.fancyserver = self._config.get('main', {}).get('plugins', {}).get('Fancygotchi', {}).get('fancyserver', False)
            else:
                self.fancyserver = False
            if not boot:self.log(f'Theme: {self._theme_name}')

        except Exception as e:
            self.log(f"Error in theme selector: {str(e)}")
            self.log(traceback.format_exc())
            return None

    def save_screenshot(self, theme_name, screenshot_url, headers):
        screenshots_path = os.path.join(self._pwny_root, 'ui/web/static/repo_screenshots')
        theme_folder_path = os.path.join(screenshots_path, theme_name)
        os.makedirs(theme_folder_path, exist_ok=True)
        response = requests.get(screenshot_url, headers=headers).content
        screenshot_path = os.path.join(theme_folder_path, 'screenshot.png')
        with open(screenshot_path, 'wb') as f:
            f.write(response)
        return os.path.join('repo_screenshots', theme_name, 'screenshot.png')

    def fetch_themes(self):
        themes = {}
        screenshots_path = os.path.join(self._pwny_root, 'ui/web/static/repo_screenshots')
        try:
            if os.path.exists(screenshots_path):
                shutil.rmtree(screenshots_path)
            headers = {"Authorization": f"Bearer {self.gittoken}"} if self.gittoken else {}
            response = requests.get(THEMES_REPO, headers=headers)
            response.raise_for_status()
            for item in response.json():
                if item["type"] == "dir":
                    theme_name = item["name"]
                    self.log(f"Fetching theme: {theme_name}")
                    theme_url = item["url"]
                    themes[theme_name] = {"info": None, "screenshot": None}
                    theme_contents = requests.get(theme_url, headers=headers).json()
                    for file in theme_contents:
                        if file["name"] == "info.json":
                            info_url = file["download_url"]
                            info_data = requests.get(info_url, headers=headers).json()
                            themes[theme_name]["info"] = info_data
                        elif file["name"] == "img" and file["type"] == "dir":
                            img_folder_url = file["url"]
                            img_contents = requests.get(img_folder_url, headers=headers).json()
                            if isinstance(img_contents, list):
                                for img_file in img_contents:
                                    if isinstance(img_file, dict) and img_file.get("name") == "screenshot.png":
                                        local_screenshot_path = self.save_screenshot(theme_name, img_file["download_url"], headers)
                                        themes[theme_name]["screenshot"] = local_screenshot_path
            sorted_themes = dict(sorted(themes.items(), key=lambda item: item[0].lower()))
            self.log("Themes fetched successfully:")
            for theme, info in sorted_themes.items():
                version = info["info"].get("version") if info["info"] else "Unknown"
                self.log(f"{theme}: Version {version}, Screenshot: {info['screenshot']}")
            return sorted_themes

        except requests.RequestException as e:
            logging.error(f"Error fetching themes: {e}")
            return {}

    def theme_downloader(self, theme_name):
        try:
            headers = {"Authorization": f"Bearer {self.gittoken}"} if self.gittoken else {}
            theme_contents_url = os.path.join(THEMES_REPO, theme_name)
            response = requests.get(theme_contents_url, headers=headers)
            response.raise_for_status()
            contents = response.json()
            temp_dir = tempfile.mkdtemp()
            temp_theme_path = os.path.join(temp_dir, theme_name)
            final_path = os.path.join(self._plug_root, "themes", theme_name)
            os.makedirs(temp_theme_path, exist_ok=True)
            def download_content(contents, current_path):
                for item in contents:
                    item_path = os.path.join(current_path, item['name'])
                    if item['type'] == 'dir':
                        os.makedirs(item_path, exist_ok=True)
                        dir_response = requests.get(item['url'], headers=headers)
                        dir_response.raise_for_status()
                        download_content(dir_response.json(), item_path)
                    else:
                        file_response = requests.get(item['download_url'], headers=headers)
                        file_response.raise_for_status()
                        with open(item_path, 'wb') as f:
                            f.write(file_response.content)
            download_content(contents, temp_theme_path)
            if os.path.exists(final_path):
                shutil.rmtree(final_path)
            shutil.move(temp_theme_path, final_path)
            shutil.rmtree(temp_dir)
            logging.warning(f"Theme {theme_name} downloaded successfully to {final_path}")

        except requests.RequestException as e:
            logging.error(f"Error downloading themes: {e}")
            logging.error(traceback.format_exc())
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir)


    def save_active_config(self, data):
        cfg_path = self.cfg_path
        self.log(f"Saving active config to: {self.cfg_path}")
            
        if os.path.exists(cfg_path):
            os.remove(cfg_path)

        with open(cfg_path, 'w') as f:
            toml.dump(data, f)

    def theme_save_config(self, theme, rotation):
        if self._config['ui'] ['display']['rotation'] != 0:
            self._config['ui'] ['display']['rotation'] = 0
        self._config['main']['plugins']['Fancygotchi']['rotation'] = int(rotation)
        if theme == 'Default': theme = ''
        self._config['main']['plugins']['Fancygotchi']['theme'] = theme
        
        
        self.log('Theme save config')
        pwnagotchi.config = merge_config(self._config, pwnagotchi.config)
        if self._agent:
            self._agent._config = merge_config(self._config, pwnagotchi.config)
        save_config(pwnagotchi.config, '/etc/pwnagotchi/config.toml')

    def toggle_fancyserver(self, fancyserver):
        self._config['main']['plugins']['Fancygotchi']['fancyserver'] = fancyserver
        self.fancyserver = fancyserver
        pwnagotchi.config = merge_config(self._config, pwnagotchi.config)
        if self._agent:
            self._agent._config = merge_config(self._config, pwnagotchi.config)
        save_config(pwnagotchi.config, '/etc/pwnagotchi/config.toml')

    def setup_fancyserver(self, th_menu):
        if hasattr(self, 'fancy_menu'):
            
            del self.fancy_menu
        menu_theme = copy.deepcopy(self._default_menu)
        menu_opt = th_menu.get('options', {})
        menu_theme.update(menu_opt)
        custom_menus = {}
        if 'menu' in self._theme.get('theme', {}):
            custom_menus = self._theme.get("theme", {}).get("menu", {})
            custom_menus.pop('options', None)
        if self.fancyserver:   
            if not hasattr(self, 'fancy_server') or (hasattr(self, 'fancy_server') and getattr(self, 'fancy_server', None) is None):
                self.fancy_server = FancyServer()

                try:
                    self.fancy_server.start()
                except OSError as e:
                    if e.errno == 98: 
                        logging.warning("[Fancygotchi] Address already in use. FancyServer could not start.")
                    else:
                        logging.error(f"[Fancygotchi] Error starting FancyServer: {e}")

        else:
            if hasattr(self, 'fancy_server'):
                self.running = False
                self.log("[Fancygotchi] Stopping FancyServer.")
                self.cleanup_fancyserver()
                fancytools_path = "/usr/local/bin/fancytools"
                diagnostic_path = "/usr/local/bin/diagnostic.sh"
                if os.path.exists(fancytools_path):
                    os.remove(fancytools_path)
                if os.path.exists(diagnostic_path):
                    os.remove(diagnostic_path)

                logging.debug("[Fancygotchi] FancyServer instance deleted.")
            else:
                logging.debug("[Fancygotchi] FancyServer is disabled and no instance exists.")
        fancygotchi_config = pwnagotchi.config.get('main', {}).get('plugins', {}).get('Fancygotchi', {})
        diagnostic_path = "/usr/local/bin/diagnostic.sh"
        if os.path.exists(diagnostic_path):
            os.remove(diagnostic_path)
        with open(diagnostic_path, "w") as diagnostic_file:
            diagnostic_file.write(DIAGNOSTIC)
        os.system(f'chmod +x {diagnostic_path}')
        self.fancy_menu = FancyMenu(self, menu_theme, custom_menus)
        if fancygotchi_config.get('fancyserver', False):
            try:
                fancytools_content = FANCYTOOLS.replace("{pyenv}", self.pyenv)
                fancytools_path = "/usr/local/bin/fancytools"
                logging.debug(f"Writing content to {fancytools_path}")
                if os.path.exists(fancytools_path):
                    os.remove(fancytools_path)

                with open(fancytools_path, "w") as fancytools_file:
                    fancytools_file.write(fancytools_content)

                os.system(f'chmod +x {fancytools_path}')
                self.running = True
            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")

    def theme_update(self, ui, boot=False):
        th_opt = copy.deepcopy(self._default['theme']['options'])
        self._i = 0
        if not boot:self.log('Theme update')
        if hasattr(ui, '_update') and ui.update:
            if not ui._update['partial']:
                self._state = {}
                with open('/etc/pwnagotchi/config.toml', 'r') as f:
                    f_toml = toml.load(f)
                    try:
                        self.options['rotation'] = f_toml['main']['plugins']['Fancygotchi']['rotation']
                    except:
                        self.options['rotation'] = 0
                        f_toml['main']['plugins']['Fancygotchi']['rotation'] = self.options['rotation']

                    try:
                        self.options['theme'] = f_toml['main']['plugins']['Fancygotchi']['theme']
                    except:
                        self.options['theme'] = ''
                        f_toml['main']['plugins']['Fancygotchi']['theme'] = self.options['theme']

                    try:
                        self.options['fancyserver'] = f_toml['main']['plugins']['Fancygotchi']['fancyserver']
                    except:
                        self.options['fancyserver'] = False
                        f_toml['main']['plugins']['Fancygotchi']['fancyserver'] = self.options['fancyserver']

                rot = self.options['rotation']
                th = self.options['theme']
                fancys = self.options['fancyserver']
                pwnagotchi.config['main']['plugins']['Fancygotchi']['rotation'] = rot
                pwnagotchi.config['main']['plugins']['Fancygotchi']['theme'] = th
                pwnagotchi.config['main']['plugins']['Fancygotchi']['fancyserver'] = fancys
                pwnagotchi.config = merge_config(f_toml, pwnagotchi.config)
                if self._agent:
                    self._agent._config = merge_config(f_toml, pwnagotchi.config)
                save_config(pwnagotchi.config, '/etc/pwnagotchi/config.toml')
                self.theme_selector(f_toml, boot)

                th = self._theme['theme']
                th_opt = th['options']
                th_widget = th['widget']
                th_menu = th.get('menu', {})
            else:
                self.log('Partial update')
                if 'options' in ui._update['dict_part']:
                    th_opt = ui._update['dict_part']['options']
                th = ui._update['dict_part']
                th_widget = {}
                if 'widget' in ui._update['dict_part']:
                    th_widget = th['widget']
                
            if th_opt:
                if 'font' in th_opt and th_opt['font'] != '':
                    ft = th_opt['font_sizes']
                    self.font_name  = th_opt['font']
                    self.setup_font(ft[0], ft[1], ft[2], ft[3], ft[4], ft[5])
                if 'font_awesome' in th_opt and th_opt['font_awesome'] != '':
                    self.f_awesome_name = th_opt['font_awesome']
                if 'color_mode' in th_opt and th_opt['color_mode'] != '':
                    self._color_mode = th_opt['color_mode']
                    setattr(ui, '_web_mode', self._color_mode[0])
                    setattr(ui, '_hw_mode', self._color_mode[1])
                if hasattr(th_opt, 'main_text_color') and th_opt.get('main_text_color', []) != []:
                    self._icolor = 0
                if hasattr(th_opt, 'base_text_color') and th_opt.get('base_text_color', []) != []:
                    self._icolor = 0
                self.fps = th_opt.get('second_screen_fps', 1)
                self.webui_fps = int(1000*th_opt.get('webui_fps', 1))
                if rot in (90, 270):
                    startname = f'{self._res[1]}x{self._res[0]}' 
                    w = self._res[1]
                    h = self._res[0]
                elif rot in (0, 180):
                    startname = f'{self._res[0]}x{self._res[1]}' 
                    w = self._res[0]
                    h = self._res[1]
                if  th_opt.get('bg_fg_select', 'manu') not in ('auto', 'manu'):
                    th_opt['bg_fg_select'] = 'manu'
                screen_mode = th_opt.get('screen_mode', 'screen_saver')
                if screen_mode in self.screen_modes:
                    self.display_config['mode'] = screen_mode
                screen_saver = th_opt.get('screen_saver', 'show_logo')
                if screen_saver in self.screen_saver_modes:
                    self.display_config['sub_mode'] = screen_saver
                self.display_config['second_screen_webui'] = th_opt.get('second_screen_webui', False)
                bgfg_mode = th_opt.get('bg_fg_select', 'manu')
                if self._th_path is not None:
                    bg_folder_path = os.path.join(self._th_path, 'img', 'bg')
                    if bgfg_mode == 'manu':
                        bga_name = th_opt.get('bg_anim_image', '')
                        bga_path = os.path.join(bg_folder_path, bga_name)
                        bg_name = th_opt.get('bg_image', '')
                        bg_path = os.path.join(bg_folder_path, bg_name)
                        fg_name = th_opt.get('fg_image', '')
                        fg_path = os.path.join(bg_folder_path, fg_name)
                    elif bgfg_mode == 'auto':
                        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp')
                        valid_anim_extensions = ('.gif')

                        bga_fname = f'{startname}bga'
                        bg_fname = f'{startname}bg'
                        fg_fname = f'{startname}fg'

                        bga_path = next((os.path.join(bg_folder_path, f) for f in os.listdir(bg_folder_path) 
                                        if f.lower().startswith(bga_fname) and f.lower().endswith(valid_anim_extensions)), None)
                        
                        bg_path = next((os.path.join(bg_folder_path, f) for f in os.listdir(bg_folder_path) 
                                        if f.lower().startswith(bg_fname) and f.lower().endswith(valid_extensions)), None)
                        
                        fg_path = next((os.path.join(bg_folder_path, f) for f in os.listdir(bg_folder_path) 
                                        if f.lower().startswith(fg_fname) and f.lower().endswith(valid_extensions)), None)

                        if not bga_path:
                            bga_path = next((os.path.join(bg_folder_path, f) for f in os.listdir(bg_folder_path) 
                                            if f.lower().startswith('bga') and f.lower().endswith(valid_anim_extensions)), None)

                        if not bg_path:
                            bg_path = next((os.path.join(bg_folder_path, f) for f in os.listdir(bg_folder_path) 
                                            if f.lower().startswith('bg') and f.lower().endswith(valid_extensions)), None)

                        if not fg_path:
                            fg_path = next((os.path.join(bg_folder_path, f) for f in os.listdir(bg_folder_path) 
                                            if f.lower().startswith('fg') and f.lower().endswith(valid_extensions)), None)

                    self._frames = []
                    self._i = 0
                    if ('bg_anim_image' in th_opt and th_opt['bg_anim_image'] != '') or bga_path is not None:
                        if bga_path and os.path.exists(bga_path) and not os.path.isdir(bga_path):
                            gif = Image.open(bga_path)
                            self._i = 0
                            self._frames = []
                            frames = ImageSequence.Iterator(gif)
                            for frame in frames:
                                canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                                frame = frame.convert("RGBA")
                                frame = image_mode(canvas, frame, th_opt.get('bg_mode', 'normal'))
                                self._frames.append(frame)
                            self._imax = len(self._frames)

                    if ('bg_image' in th_opt and th_opt['bg_image'] != '') or bg_path is not None:
                        canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))

                        if bg_path and os.path.exists(bg_path) and not os.path.isdir(bg_path):
                            bg_tmp = Image.open(bg_path)
                            bg_tmp = bg_tmp.convert("RGBA")
                            self._bg = image_mode(canvas, bg_tmp, th_opt.get('bg_mode', 'normal'))
                        else:
                            self._bg = ''
                    else:
                        self._bg = ''

                    if ('fg_image' in th_opt and th_opt['fg_image'] != '') or fg_path is not None:
                        canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                        if fg_path and os.path.exists(fg_path) and not os.path.isdir(fg_path):
                            fg_tmp = Image.open(fg_path) 
                            fg_tmp = fg_tmp.convert("RGBA")
                            self._fg = image_mode(canvas, fg_tmp, th_opt.get('fg_mode', 'normal'))
                        else:
                            self._fg = ''
                    else:
                        self._fg = ''

                    if 'boot_max_loops' in th_opt and th_opt['boot_max_loops'] != 0:
                        th_opt['boot_max_loops'] = int(th_opt['boot_max_loops'])
                    else:
                        th_opt['boot_max_loops'] = 1
                    if 'boot_total_duration' in th_opt and th_opt['boot_total_duration'] != 0:
                        th_opt['boot_total_duration'] = int(th_opt['boot_total_duration'])
                    else:
                        th_opt['boot_total_duration'] = 5
                    boot_anim_file = '/usr/local/bin/boot_animation.py'
                    if 'boot_animation' in th_opt and th_opt['boot_animation'] and self._config['ui']['display']['enabled']:
                        img_path = os.path.join(self._th_path, 'img', 'boot')
                        color_mode_web, color_mode_hw = th_opt['color_mode']
                        boot_anim_py = BOOT_ANIM.format(img_path=img_path, width=self._res[0], height=self._res[1], max_loops=th_opt['boot_max_loops'], total_duration=th_opt['boot_total_duration'], rotation=rot, color_mode=color_mode_hw)
                        with open(boot_anim_file, 'w') as f:
                            f.write(boot_anim_py)
                    else:
                        if os.path.exists(boot_anim_file):
                            os.remove(boot_anim_file)
                self.setup_fancyserver(th_menu)

    def theme_list(self):
        themes_path = os.path.join(self._plug_root, 'themes')
        themes = []
        if not os.path.exists(themes_path):
            os.makedirs(themes_path)
        items = os.listdir(themes_path)
        screenshots_path = os.path.join(self._pwny_root, 'ui/web/static/screenshots')
        if os.path.exists(screenshots_path):
            os.system(f'rm -r {screenshots_path}')
        if not os.path.exists(screenshots_path):
            os.makedirs(screenshots_path, exist_ok=True)
            image = Image.new('RGBA', self._res, (0, 0, 0, 0))
            image_path = os.path.join(screenshots_path, 'screenshot.png')
            image.save(image_path)
        for item in items:
            if os.path.isdir(os.path.join(themes_path, item)):
                themes.append(item)
                screenshots_path = os.path.join(self._pwny_root, 'ui/web/static/screenshots')
                screenshot_path = os.path.join(themes_path, item, 'img', 'screenshot.png')
                subfolder = os.path.join(screenshots_path, item)
                
                if os.path.exists(screenshot_path):
                    if not os.path.exists(subfolder):
                        os.makedirs(subfolder, exist_ok=True)
                    os.system(f'cp {screenshot_path} {subfolder}')

        return sorted(themes, key=lambda x: x.lower())

    def change_font(self, old_font, new_font=None, size_offset=None):
        if new_font == None:
            new_font = self._theme['theme']['options']['status_font']
        if size_offset == None:
            size_offset = self._theme['theme']['options']['size_offset']
        return ImageFont.truetype(self.get_font_path(new_font), size=old_font.size + size_offset)

    def theme_export(self, theme_name):
        self.log(f"Exporting theme {theme_name}")
        try:
            themes_folder = os.path.join(self._plug_root, 'themes')
            theme_path = os.path.join(themes_folder, theme_name)
            if not os.path.exists(theme_path):
                return make_response(jsonify({"error": "Theme not found"}), 404)

            zip_filename = f"{theme_name}_export.zip"
            zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(theme_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(theme_name, os.path.relpath(file_path, theme_path))
                        zipf.write(file_path, arcname)

            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        except Exception as e:
            logging.error(f"Error exporting theme {theme_name}: {str(e)}")
            return f"Error exporting theme: {str(e)}", 500

    def get_font_path(self, font_name):
        if '.' not in font_name:
            return font_name
        else:
            return os.path.join(self._th_path, 'fonts', font_name)

    def setup_font(self, bold, bold_small, medium, huge, bold_big, small):
        self.Small = ImageFont.truetype(self.get_font_path(self.font_name), small)
        self.Medium = ImageFont.truetype(self.get_font_path(self.font_name), medium)
        self.BoldSmall = ImageFont.truetype(self.get_font_path(self.font_bold_name), bold_small)
        self.Bold = ImageFont.truetype(self.get_font_path(self.font_bold_name), bold)
        self.BoldBig = ImageFont.truetype(self.get_font_path(self.font_bold_name), bold_big)
        self.Huge = ImageFont.truetype(self.get_font_path(self.font_bold_name), huge)

    def rgba_text(self, text, tfont, color='black', width=None, height=None):
        try:
            th_opt = self._theme['theme']['options']
            if color == 'white' : color = (249, 249, 249, 255)
            if color == 255 : color = 'black'
            if text is not None and tfont is not None:
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
                imgtext = Image.new('1', (w,h), 0xff)
                dt = ImageDraw.Draw(imgtext)
                dt.text((0,0), text, font=tfont, fill=0x00)
                if color == 0: color = 'black'
                imgtext = ImageOps.colorize(imgtext.convert('L'), black = color, white = 'white')
                imgtext = imgtext.convert("RGBA")
                data = imgtext.getdata()
                newData = []
                for item in data:
                    if item[0] in range(250, 256) and item[1] in range(250, 256) and item[2] in range(250, 256):
                        newData.append((255, 255, 255, 0))
                    else:
                        newData.append(item)
                imgtext.putdata(newData)
                imgtext = imgtext.convert('RGBA')
                return imgtext
        except Exception as e:
            self.log(f"Error while rgba_text ({text}; {tfont}; {color}; {width}; {height}): {str(e)}")
            self.log(traceback.format_exc())
            return None

    def add_widget(self, ui, key, widget_type, th_widget):
        conf = 0
        th_opt = self._theme['theme']['options']
        if key in self._state:
            if key in th_widget and th_widget[key].get('position'):
                if self._state[key]['position'] != tuple(th_widget[key]['position']):
                    self._state[key]['position'] =  tuple(th_widget[key]['position'])
            else:
                if self._state[key]['position'] != tuple(ui._state.get_attr(key, 'xy')):
                    position = ui._state.get_attr(key, 'xy')
                    position = tuple(int(coord) for coord in position)
                    if len(position) >= 3:
                        position = box_to_xywh(position)
                    self._state[key]['position'] = position
            if key in th_widget and th_widget[key].get('color'):
                if self._state[key]['color'] != th_widget[key]['color']:
                    self._state[key]['color'] = th_widget[key]['color']
                    self._state[key]['icolor'] = 0
            elif "base_text_color" in th_opt and th_opt['base_text_color']:
                if self._state[key]['color'] != th_opt['base_text_color']:
                    self._state[key]['color'] = th_opt['base_text_color']
                    self._state[key]['icolor'] = 0
            else:
                if self._state[key]['color'] != [ui._state.get_attr(key, 'color')]:
                    self._state[key]['color'] = [ui._state.get_attr(key, 'color')]
                    self._state[key]['icolor'] = 0

        elif key not in self._state:
            conf = 1
            self._state[key] = {}
            self._state_default[key] = {}
            self._state_default[key] = copy.deepcopy(self._state[key])
            default_values = self.widget_defaults.get(widget_type, {})
            self._state[key] = copy.deepcopy(default_values)
            self._state[key].update({'widget_type': widget_type})
            self._state_default[key].update({'widget_type': widget_type})

            position = ui._state.get_attr(key, 'xy')
            position = tuple(int(coord) for coord in position)
            
            if len(position) >= 3:
                position = box_to_xywh(position)
            self._state[key].update({'position': position})
            self._state_default[key].update({'position': position})

            if key in th_widget and th_widget[key].get('position'):
                self._state[key].update({'position': tuple(th_widget[key]['position'])})
            self._state_default[key].update({'color': [ui._state.get_attr(key, 'color')]})
            if key in th_widget and th_widget[key].get('color'):
                self._state[key].update({'color': th_widget[key]['color']})
                self._state[key].update({'icolor': 0})
            elif th_opt.get('base_text_color'):
                self._state[key].update({'color': th_opt['base_text_color']})
                self._state[key].update({'icolor': 0})
            else:
                self._state[key].update({'color': [ui._state.get_attr(key, 'color')]})
                self._state[key].update({'icolor': 0})
            if key in th_widget and 'z_axis' in th_widget[key]:
                self._state[key].update({'z_axis': th_widget[key]['z_axis']})
            if widget_type == 'Text' or widget_type == 'LabeledValue':
                if key in th_widget and th_widget[key].get('text_font'):
                    if th_widget[key].get('text_font') == '' or th_widget[key].get('text_font') == None:
                        self._state[key].pop('text_font', None)
                    else:
                        self._state[key].update({'text_font': th_widget[key]['text_font']})
                if widget_type == 'Text':
                    self._state_default[key].update({'text_font_size': verify_font_info(ui._state.get_attr(key, 'font'))})
                if widget_type == 'LabeledValue':
                    self._state_default[key].update({'text_font_size': verify_font_info(ui._state.get_attr(key, 'text_font'))})
                if key in th_widget and th_widget[key].get('text_font_size'):
                    self._state[key].update({'text_font_size': th_widget[key]['text_font_size']})
                else:
                    if widget_type == 'Text':
                        self._state[key].update({'text_font_size': verify_font_info(ui._state.get_attr(key, 'font'))})
                    if widget_type == 'LabeledValue':
                        self._state[key].update({'text_font_size': verify_font_info(ui._state.get_attr(key, 'text_font'))})
                if key in th_widget and th_widget[key].get('size_offset'):
                    self._state[key].update({'size_offset': th_widget[key]['size_offset']})
                if key in th_widget and th_widget[key].get('icon'):
                    self._state[key].update({'icon': th_widget[key]['icon']})
                if key in th_widget and th_widget[key].get('icon_color'):
                    self._state[key].update({'icon_color': th_widget[key]['icon_color']})
                if key in th_widget and th_widget[key].get('invert'):
                    self._state[key].update({'invert': th_widget[key]['invert']})
                if key in th_widget and th_widget[key].get('alpha'):
                    self._state[key].update({'alpha': th_widget[key]['alpha']})
                if key in th_widget and th_widget[key].get('crop'):
                    self._state[key].update({'crop': th_widget[key]['crop']})
                if key in th_widget and th_widget[key].get('mask'):
                    self._state[key].update({'mask': th_widget[key]['mask']})
                if key in th_widget and th_widget[key].get('refine'):
                    self._state[key].update({'refine': th_widget[key]['refine']})
                if key in th_widget and th_widget[key].get('zoom'):
                    self._state[key].update({'zoom': th_widget[key]['zoom']})
                if key in th_widget and th_widget[key].get('image_type'):
                    self._state[key].update({'image_type': th_widget[key]['image_type']})
            if widget_type == 'Text':
                self._state_default[key].update({'wrap': ui._state.get_attr(key, 'wrap')})
                if key in th_widget and th_widget[key].get('wrap'):
                    self._state[key].update({'wrap': th_widget[key]['wrap']})
                else:
                    self._state[key].update({'wrap': ui._state.get_attr(key, 'wrap')})
                self._state[key].update({'max_length': ui._state.get_attr(key, 'max_length')})
                if key in th_widget and th_widget[key].get('max_length'):
                    self._state[key].update({'max_length': th_widget[key]['max_length']})
                else:
                    self._state[key].update({'max_length': ui._state.get_attr(key, 'max_length')})
                if key in th_widget and th_widget[key].get('face'):
                    self._state[key].update({'max_length': th_widget[key]['max_length']})
            if widget_type == 'LabeledValue':
                self._state_default[key].update({'label': ui._state.get_attr(key, 'label')})
                if key in th_widget and 'label' in th_widget[key]:
                    self._state[key].update({'label': th_widget[key]['label']})
                else:
                    self._state[key].update({'label': ui._state.get_attr(key, 'label')})
                if key in th_widget and th_widget[key].get('label_font'):
                    self._state[key].update({'label_font': th_widget[key]['label_font']})
                if key in th_widget and th_widget[key].get('label_font_size'):
                    self._state[key].update({'label_font_size': th_widget[key]['label_font_size']})
                else:
                    self._state[key].update({'label_font_size': verify_font_info(ui._state.get_attr(key, 'label_font'))})
                self._state_default[key].update({'label_spacing': ui._state.get_attr(key, 'label_spacing')})
                if key in th_widget and th_widget[key].get('label_spacing'):
                    self._state[key].update({'label_spacing': th_widget[key]['label_spacing']})
                elif 'label_spacing' in th_opt and th_opt['label_spacing']:
                    self._state[key].update({'label_spacing': th_opt['label_spacing']})
                else:
                    self._state[key].update({'label_spacing': ui._state.get_attr(key, 'label_spacing')})
                if key in th_widget and th_widget[key].get('label_line_spacing'):
                    self._state[key].update({'label_line_spacing': th_widget[key]['label_line_spacing']})
                elif 'label_line_spacing' in th_opt and th_opt['label_line_spacing']:
                    self._state[key].update({'label_line_spacing': th_opt['label_line_spacing']})
                else:
                    self._state[key].update({'label_line_spacing': 0})

                if key in th_widget and th_widget[key].get('f_awesome'):
                    self._state[key].update({'f_awesome': th_widget[key]['f_awesome']})
                if key in th_widget and th_widget[key].get('f_awesome_size'):
                    self._state[key].update({'f_awesome_size': th_widget[key]['f_awesome_size']})
            if widget_type == 'Line':
                self._state_default[key].update({'width': ui._state.get_attr(key, 'width')})
                if key in th_widget and th_widget[key].get('width'):
                    self._state[key].update({'width': th_widget[key]['width']})
                else:
                    self._state[key].update({'width': ui._state.get_attr(key, 'width')})
            if widget_type == 'Bitmap':
                self._state[key].update({'f_awesome': False})
                if key in th_widget and th_widget[key].get('icon'):
                    self._state[key].update({'icon': th_widget[key]['icon']})
                if key in th_widget and th_widget[key].get('invert'):
                    self._state[key].update({'invert': th_widget[key]['invert']})
                if key in th_widget and th_widget[key].get('alpha'):
                    self._state[key].update({'alpha': th_widget[key]['alpha']})
                if key in th_widget and th_widget[key].get('crop'):
                    self._state[key].update({'crop': th_widget[key]['crop']})
                if key in th_widget and th_widget[key].get('mask'):
                    self._state[key].update({'mask': th_widget[key]['mask']})
                if key in th_widget and th_widget[key].get('refine'):
                    self._state[key].update({'refine': th_widget[key]['refine']})
                if key in th_widget and th_widget[key].get('zoom'):
                    self._state[key].update({'zoom': th_widget[key]['zoom']})
                if key in th_widget and th_widget[key].get('icon_color'):
                    self._state[key].update({'icon_color': th_widget[key]['icon_color']})

        if conf:
            self.configure_widget(ui, key, widget_type)
    
    def get_face_path(self, img_path, face, image_type):
        variations = [
            face, 
            face.upper(),
            face.lower(),
            face.capitalize(),
            face.replace('-', '_'),
            face.replace('_', '-'),
            face.replace('-', '_').upper(),
            face.replace('_', '-').upper(),
            face.replace('-', '_').lower(),
            face.replace('_', '-').lower()
        ]

        for variation in variations:
            face_path = os.path.join(img_path, f'{variation}.{image_type}')
            if os.path.exists(face_path):
                return face_path

        return None

    def configure_widget(self, ui, key, widget_type):
        try:
            if key == 'face':
                self._state[key].update({'face': True})
                self._state[key].update({'f_awesome': False})
                if self._state[key]['icon']:
                    face_dict = self._config['ui']['faces']
                    img_path = os.path.join(self._th_path, 'img', 'face')
                    for face in face_dict:
                        image_type = self._state[key].get('image_type', 'png')
                        if isinstance(face_dict[face], str):
                            face_path = self.get_face_path(img_path, face, image_type)
                            if face_path:
                                if 'face_map' not in self._state[key]:
                                    self._state[key].update({'face_map': {}})
                                self._state[key]['face_map'].update({
                                    face: [
                                        face_dict[face],
                                        adjust_image(face_path, self._state[key]['zoom'], self._state[key]['mask'], self._state[key]['refine'], self._state[key]['alpha'], self._state[key]['invert'], self._state[key]['crop'])
                                    ]
                                })
                            else:
                                logging.warning(f"[Fancygotchi] No valid face path found for '{face}'")
                     
            if key == 'friend_face':
                self._state[key].update({'friend_face': True})
                face_dict = self._config['ui']['faces']
                self._state[key].update({'f_awesome': False})
                if self._state[key]['icon']:
                    face_dict = self._config['ui']['faces']
                    img_path = os.path.join(self._th_path, 'img', 'friend_face')
                    for face in face_dict:
                        image_type = self._state[key].get('image_type', 'png')
                        if isinstance(face_dict[face], str):
                            face_path = self.get_face_path(img_path, face, image_type)
                            if face_path:
                                if 'friend_face_map' not in self._state[key]:
                                    self._state[key].update({'friend_face_map': {}})
                                self._state[key]['friend_face_map'].update({
                                    face: [
                                        face_dict[face],
                                        adjust_image(face_path, self._state[key]['zoom'], self._state[key]['mask'], self._state[key]['refine'], self._state[key]['alpha'], self._state[key]['invert'], self._state[key]['crop'])  
                                    ]
                                })
                            else:
                                print(f"Warning: No valid face path found for '{face}'")

            if self._state[key].get('icon'):
                if self._state[key]['icon'] == True:
                    source = 'label'
                    if key not in ['face', 'friend_face']:
                        if widget_type == 'LabeledValue' and not self._state[key]['f_awesome']:
                            
                            icon_path = os.path.join(self._th_path, 'img', 'widgets', key, self._state[key][source])
                            self._state[key].update({'icon_image': adjust_image(Image.open(icon_path), self._state[key]['zoom'], self._state[key]['mask'], self._state[key]['refine'], self._state[key]['alpha'], self._state[key]['invert'], self._state[key]['crop'])})
                        if not self._state[key]['f_awesome']:
                            if widget_type == 'Bitmap':
                                img_path = os.path.join(self._th_path, 'img', 'widgets', key)
                                files = [f for f in os.listdir(img_path)]
                                file_count = len(files)
                                if file_count == 1:
                                    image_path = os.path.join(img_path, files[0])
                                    self._state[key].update({'image': adjust_image(image_path, self._state[key]['zoom'], self._state[key]['mask'], self._state[key]['refine'], self._state[key]['alpha'], self._state[key]['invert'], self._state[key]['crop'])})

                                elif file_count > 3 and file_count % 2 == 0:
                                    image_dict = {}
                                    file_names = [os.path.splitext(f)[0] for f in files] 

                                    for file in file_names:
                                        if file.endswith('A'):
                                            id_number = file[:-1] 
                                            corresponding_b = id_number + 'B' 
                                            
                                            if corresponding_b in file_names:
                                                original_a = [f for f in files if os.path.splitext(f)[0] == file][0]
                                                original_b = [f for f in files if os.path.splitext(f)[0] == corresponding_b][0]
                                                
                                                img_a = Image.open(os.path.join(img_path, original_a))
                                                img_b = adjust_image(Image.open(os.path.join(img_path, original_b)), self._state[key]['zoom'], self._state[key]['mask'], self._state[key]['refine'], self._state[key]['alpha'], self._state[key]['invert'], self._state[key]['crop'])
                                                
                                                image_dict[int(id_number)] = [img_a, img_b]
                                    self._state[key].update({'image_dict': image_dict})
                                    img_o, img_c = image_dict[2]
                                    self._state[key].update({'image': img_c})
                                else:
                                    self.log(f"Error: There are {file_count} images.")
                                    icon_img = Image.new('1', (10, 10), 0x00)
                                    self._state[key].update({'image': icon_img})
                        else:
                            fa_path = os.path.join(self._th_path, 'fonts', self.f_awesome_name)
                            fa = ImageFont.truetype(fa_path, self._state[key]['f_awesome_size'])
                            try:
                                code_point = int(self._state[key][source], 16)
                            except:
                                self.log("wrong font awesome icon code point: %s" % self._state[key][source])
                                code_point = int("f00d", 16)
                            icon = chr(code_point)
                            w,h = fa.getsize(icon)
                            icon_img = Image.new('1', (int(w), int(h)), 0xff)
                            dt = ImageDraw.Draw(icon_img)
                            dt.text((0,0), icon, font=fa, fill=0x00)
                            icon_img = icon_img.convert('RGBA')
                            self._state[key].update({'icon_image': icon_img})
        except Exception as e:
            self.log("non fatal error while configuring Fancygotchi widget: %s" % e)
            self.log(traceback.format_exc())

    def remove_widgets(self, ui):
            if self._state:
                keys_to_delete = [] 
                for key, state in self._state.items():
                    tag = 0
                    for k, s in ui._state.items():
                        if key == k:
                            tag = 1
                    if tag == 0:
                        keys_to_delete.append(key)
                for key in keys_to_delete:
                    self.log(f'[Fancygotchi] remove widget: {key}')
                    del self._state[key]
    def pwncanvas_creation(self, res):
        try:
            th_opt = self._theme['theme']['options']
            rot = self.options['rotation']
            if rot == 0 or rot == 180:
                x, y = res
                l = x
                w = y
            elif rot == 90 or rot == 270:
                x, y = res
                l = y
                w = x

            bg_color = th_opt['bg_color']
            if isinstance(bg_color, list):
                bg_color = tuple(bg_color)

            if not bg_color or bg_color == '':
                bg_color = (0,0,0,0)
            
            self._pwncanvas = Image.new('RGBA', (l, w), bg_color)
            self._pwndata = Image.new('RGBA', (l, w), (0,0,0,0))

            if not self._frames == []:
                iframe = self._frames[self._i]
                self._pwncanvas.paste(iframe, (0,0), iframe)

            if isinstance(self._bg, Image.Image) and self._bg is not None:
                self._pwncanvas.paste(self._bg, (0,0), self._bg.convert('RGBA'))

        except Exception as e:
            logging.error(f"Error in pwncanvas_creation: {e}")
            raise 

    def pos_convert(self, x, y, w, h, r=None, r0=None, r1=None):
        rot = self._config.get('main',{}).get('plugins',{}).get('Fancygotchi',{}).get('rotation', 0)
        if r is not None:
            rot = r
        if rot == 0 or rot == 180:
            if r0 is not None: width = r0
            else: width = self._res[0]
            if r1 is not None: height = r1
            else: height = self._res[1]
        if rot == 90 or rot == 270:
            width = self._res[1]
            height = self._res[0]
            if r1 is not None: width = r1
            else: width = self._res[0]
            if r0 is not None: height = r0
            else: height = self._res[1]
        if isinstance(w, str) and '%' in w:
            try:
                percent_value = float(w.replace('%', ''))
                w = (percent_value / 100) * width
            except ValueError:
                self.log(f"Invalid percentage value for width: {w}")
                w = 0  
        else:
            w = int(w)

        if isinstance(h, str) and '%' in h:
            try:
                percent_value = float(h.replace('%', ''))
                h = (percent_value / 100) * height
            except ValueError:
                self.log(f"Invalid percentage value for height: {h}")
                h = 0  
        else:
            h = int(h)
        top = 0
        bottom = height - h
        right = width - w
        left = width
        center_x = (width / 2) - (w / 2)
        center_y = (height / 2) - (h / 2)
        
        def replace_keywords(formula, axis):
            keyword_mapping = {
                "center_x": center_x,
                "center_y": center_y,
                "left": left,
                "right": right,
                "top": top,
                "bottom": bottom,
                "width": width,
                "height": height,
                "w": w,
                "h": h,
            }

            if axis == 'x':
                keyword_mapping["center"] = center_x
                keyword_mapping.pop('center_y', None)
                keyword_mapping.pop('top', None)
                keyword_mapping.pop('bottom', None)
                keyword_mapping.pop('height', None)
            elif axis == 'y':
                keyword_mapping["center"] = center_y
                keyword_mapping.pop('center_x', None)
                keyword_mapping.pop('left', None)
                keyword_mapping.pop('right', None)
                keyword_mapping.pop('width', None)
            else:
                raise ValueError("Invalid axis. Choose 'x' or 'y'.")

            for keyword, value in keyword_mapping.items():
                if keyword in formula:
                    formula = formula.replace(keyword, str(value))

            return formula

        def safe_eval(expr):
            try:
                if re.search(r'[^0-9\+\-\*/\(\)\. ]', expr):
                    raise ValueError(f"Invalid expression: {expr}")
                result = eval(expr)
                return result
            except Exception as e:
                self.log(f"Error evaluating expression: {expr}. Exception: {e}")
                return 0

        axis = 'x'
        if not is_int(x):
            try:
                x = replace_keywords(x, axis)
                x = safe_eval(x) 
            except ValueError as e:
                self.log(f"Error processing x: {e}")
                x = 0
        else:
            x = int(x)
            if x < 0:
                x = width + x

        axis = 'y'
        if not is_int(y):
            try:
                y = replace_keywords(y, axis)
                y = safe_eval(y) 
            except ValueError as e:
                self.log(f"Error processing y: {e}")
                y = 0
        else:
            y = int(y)
            if y < 0:
                y = height + y

        x2 = int(x + w)

        y2 = int(y + h)

        return int(x), int(y), int(x2), int(y2)
    
    def paste_image(self, img, x, y):
        
        if isinstance(img, Image.Image):
            w, h = img.size
            x, y, x2, y2 = self.pos_convert(x,y,w,h)
            img = img.convert('RGBA') 
            self._pwndata.paste(img, (x, y, x2, y2), img)

            x, y ,x2 ,y2 = self.pos_convert(x, y, w, h)

    def paste_value(self, value, pos, txt_font_size, color, wrap=None):
        x, y = pos

        if wrap and hasattr(self, 'wrapper') and self.wrapper is not None:
            try:
                text = '\n'.join(self.wrapper.wrap(value))
            except AttributeError:
                text = value
        else:
            text = value

        imgtext = self.rgba_text(text, txt_font_size, color, self._res[0], self._res[1])
        self.paste_image(imgtext, x, y)

    def drawer(self):
        try:
            th_opt = copy.deepcopy(self._default['theme']['options'])
            th_opt.update( self._theme['theme']['options'])
            draw = ImageDraw.Draw(self._pwndata)
            draw_state = dict(sorted(self._state.items(), key=lambda item: item[1].get('z_axis', 0)))
            
            keys_to_remove = {key: value for key, value in draw_state.items() if value.get('z_axis', 0) < 0}
            for key in keys_to_remove:
                del draw_state[key]

            if self.stealth_mode:
                keys_to_remove = {key for key, value in draw_state.items() if value.get('z_axis', 0) < 100}
                for key in keys_to_remove:
                    del draw_state[key]
            for widget, state in draw_state.items():
                if 'wrap' in state:
                    wrap = state['wrap']
                else:
                    wrap = False
                if 'main_text_color' in th_opt and th_opt['main_text_color'] in ([], ""):
                    if 'color' in state:
                        color = state['color'][state['icolor']]
                    else:
                        color = ['black']
                elif 'main_text_color' in th_opt and th_opt['main_text_color'] != []:
                    color = th_opt['main_text_color'][self._icolor]

                if len(state['position']) >= 3:
                    x, y, w, h = state['position']
                    x, y, x2, y2 = self.pos_convert(x,y,w,h)
                else:
                    if state['widget_type'] == 'LabeledValue':
                        x, y = state['position']
                        #logging.warning(f'****************{widget}****************')
                        #logging.warning(f'label line spacing: {state["label_line_spacing"]}')
                        #logging.warning(f'label spacing: {state["label_spacing"]}')
                        #logging.warning(f'x: {x}, y: {y}')
                        
                        v_y = y + state['label_line_spacing']
                        v_x = x + state['label_spacing'] + 5 * len(state['label'])
                        #logging.warning(f'v_x: {v_x}, v_y: {v_y}')
                    else:
                        v_x, v_y = state['position']
                
                self.wrapper = TextWrapper(width=state['max_length'], replace_whitespace=False) if wrap else None

                if state['widget_type'] == 'Text' or state['widget_type'] == 'LabeledValue':
                    if state['widget_type'] == 'LabeledValue':
                        try:
                            label_font_size = eval(f'self.{state["label_font_size"]}')
                        except Exception as e:
                            label_font_size = state["label_font_size"]
                    try:
                        txt_font_size = eval(f'self.{state["text_font_size"]}') 
                    except Exception as e:
                        txt_font_size = state["text_font_size"]
                    
                    if 'text_font' in state or 'size_offset' in state:
                        if 'text_font' in state and state['text_font']:
                            font = state['text_font']
                        else:
                            font = th_opt['status_font']

                        if 'size_offset' in state:
                            size_offset = state['size_offset']
                        else:
                            size_offset = th_opt['size_offset']
                        if txt_font_size is not None:
                            txt_font_size = self.change_font(txt_font_size, font, size_offset)

                    if state['value'] is not None:
                        if not state['icon']:
                            self.paste_value(state['value'], (v_x,v_y), txt_font_size, color, wrap)
                            if state['widget_type'] == 'LabeledValue':
                                l_text = state['label']
                            if state['widget_type'] == 'LabeledValue':
                                imgtext = self.rgba_text(l_text, label_font_size, color, self._res[0], self._res[1])
                                self.paste_image(imgtext, x, y)
                        else:
                            if 'f_awesome' in state and state['f_awesome'] == False:
                                if widget not in ['face', 'friend_face']:
                                    self.paste_value(state['value'], (v_x,v_y), txt_font_size, color, wrap)
                                    icon_image = state['icon_image']
                                else:
                                    if widget == 'face':
                                        x = v_x
                                        y = v_y
                                        for face in state['face_map'].items():
                                            face_name, face_map = face
                                            if face_map[0] == state['value']:
                                                icon_image = face_map[1]
                                    elif widget == 'friend_face':
                                        x = v_x
                                        y = v_y
                                        for face in state['friend_face_map'].items():
                                            friend_face_name, friend_face_map = face
                                            if friend_face_map[0] == state['value']:
                                                icon_image = friend_face_map[1]

                                if 'icon_color' in state and state['icon_color']:
                                    alpha = 0
                                    wht = (255, 255, 255, 255)
                                    if color == 'white': color = (249,249,249,256)
                                    if icon_image.mode in ('RGBA', 'LA') or (icon_image.mode == 'P' and 'transparency' in icon_image.info):
                                        alpha = 1
                                        white_image = Image.new('RGB', icon_image.size, wht)
                                        white_image.paste(icon_image, mask=icon_image.split()[3])
                                        icon_image = white_image
                                    L_image = icon_image.convert('L')
                                    icon_image = ImageOps.colorize(L_image, black = color, white = wht)
                                    if alpha:
                                        icon_image = icon_image.convert('RGBA')
                                        data = icon_image.getdata()
                                        newData = []
                                        for item in data:
                                            if item[0] in range(250, 256) and item[1] in range(250, 256) and item[2] in range(250, 256):
                                                newData.append((255, 255, 255, 0))
                                            else:
                                                newData.append(item)
                                        icon_image.putdata(newData)
                                        icon_image = icon_image.convert('RGBA')
                                self.paste_image(icon_image, x, y)

                            else:
                                if color == 'white': color = (249,249,249,255)
                                img = state['icon_image'].convert('L')
                                icon_image = ImageOps.colorize(img, black = color, white = 'white')
                                icon_image = icon_image.convert('RGBA')
                                data = icon_image.getdata()
                                newData = []
                                for item in data:
                                    if item[0] in range(240, 256) and item[1] in range(240, 256) and item[2] in range(240, 256):
                                        newData.append((255, 255, 255, 0))
                                    else:
                                        newData.append(item)
                                icon_image.putdata(newData)
                                icon_image = icon_image.convert('RGBA')
                                self.paste_value(state['value'], (v_x,v_y), txt_font_size, color, wrap)
                                self.paste_image(icon_image, x, y)

                elif state['widget_type'] == 'Bitmap':
                    icon_bmp = state['image']
                    alpha = 0
                    original = icon_bmp
                    if icon_bmp is not None:
                        if icon_bmp.mode in ('RGBA', 'LA') or (icon_bmp.mode == 'P' and 'transparency' in icon_bmp.info):
                            alpha = 1
                            if 'mask' in state and state['mask']:
                                refine = state['refine']
                                image = icon_bmp.convert('RGBA')
                                
                                width, height = image.size
                                pixels = image.getdata()
                                new_pixels = []
                                
                                for pixel in pixels:
                                    r, g, b, a = pixel
                                    
                                    if r > 255 - refine and g > 255 - refine and b > 255 - refine:
                                        new_pixel = (255, 255, 255, 0)  
                                    else:
                                        new_pixel = (r, g, b, a)
                                    
                                    new_pixels.append(new_pixel)
                                
                                refined_image = Image.new("RGBA", image.size)
                                refined_image.putdata(new_pixels)
                                white_image = Image.new('RGB', refined_image.size, (255, 255, 255))
                                white_image.paste(icon_bmp, mask=refined_image.split()[3])
                                icon_bmp = white_image
                        if 'icon_color' in state and state['icon_color']:
                            L_image = icon_bmp.convert('L')
                            icon_bmp = ImageOps.colorize(L_image, black = color, white = (255, 255, 255))
                        if 'alpha' in state and state['alpha']:
                            if alpha:
                                icon_bmp = alphamask(icon_bmp)
                        self.paste_image(icon_bmp, v_x, v_y)
                elif state['widget_type'] == 'Line':
                    draw.line([x,y,x2,y2], fill=color, width=state['width'])
                elif state['widget_type'] == 'Rect':
                    draw.rectangle([x,y,x2,y2], fill=color)
                elif state['widget_type'] == 'FilledRect':
                    draw.rectangle([x,y,x2,y2], fill=color)

                if state['icolor'] + 1 >= len(state['color']):
                    state['icolor'] = 0
                else:
                    state['icolor'] += 1

            if self._icolor + 1 >= len(th_opt['main_text_color']):
                self._icolor = 0
            else:
                self._icolor += 1  
        
            if self._fg != '':
                self._pwndata.paste(self._fg, (self._pwndata.size[0], self._pwndata.size[1]), self._fg)

            if hasattr(self, 'fancy_menu'):
                if getattr(self.fancy_menu, 'active', False): 
                    menu_img = self.fancy_menu.render()
                    self.fancy_menu_img = menu_img
                    if self.fancy_menu_img is not None:
                        self._pwndata.paste(self.fancy_menu_img, (0, 0, self._pwndata.size[0], self._pwndata.size[1]), self.fancy_menu_img.split()[3])

            self._pwncanvas.paste(self._pwndata, (0, 0), self._pwndata)

        except Exception as e:
            logging.error(f"Error in Fancygotchi drawer: {e}")
            logging.error(traceback.format_exc())
            raise

    def ui2(self):
        try:
            image = self.second_screen
            if hasattr(self, 'display_controller') and self.display_config['second_screen_webui']:
                image = self.display_controller.screen()
            img_io = BytesIO()
            image.save(img_io, 'PNG')
            img_io.seek(0) 
            return send_file(img_io, mimetype='image/png'), 200

        except Exception as ex:
            image = self.second_screen
            img_io = BytesIO()
            image.save(img_io, 'PNG')
            img_io.seek(0) 
            return send_file(img_io, mimetype='image/png'), 200

    def on_webhook(self, path, request):
        try:
            if not self.ready:
                return "Plugin not ready"
            if request.method == "GET":
                fancyS = False 
                if hasattr(self, '_config') and 'Fancygotchi' in self._config['main']['plugins']:
                    fancyS = self._config['main']['plugins']['Fancygotchi'].get('fancyserver', False)

                if path == "/" or not path:
                    themes = sorted(self.theme_list(), key=lambda x: x.lower())
                    if self._theme_name != 'Default':
                        css_path = os.path.join(self._th_path, 'style.css')
                        info_path = os.path.join(self._th_path, 'info.json')
                        rot = self._config['main']['plugins']['Fancygotchi']['rotation']
                        
                        if self.cfg_path is not None:
                            cfg_path = self.cfg_path
                        else:
                            cfg_path = 'No custom configuration'

                        name = self._theme_name
                        if os.path.exists(css_path):
                            css = open(css_path, 'r').read()
                        else:
                            css = ''
                            css_path = 'No custom css'

                        if os.path.exists(info_path):
                            info = open(info_path, 'r').read()
                        else:
                            info = ''
                            info_path = 'No custom info'

                    else:
                        css_path = 'default has no custom css'
                        info_path = 'default has no custom info'
                        cfg_path = 'default has no custom configuration'
                        css = ''
                        info = ''
                        name = 'Default'
                    files = {'CSS': [css_path, css], 'Info': [info_path, info]}
                    return render_template_string(
                        INDEX, themes=themes, 
                        default_theme=name, 
                        rotation=self._config['main']['plugins']['Fancygotchi']['rotation'],
                        author=Fancygotchi.__author__,
                        version=Fancygotchi.__version__,
                        files=files,
                        cfg_path=cfg_path,
                        name=name,
                        logo=LOGO,
                        fancyserver=fancyS,
                        webui_fps=self.webui_fps,
                        fancy_repo=FANCY_REPO,
                    )

                elif path == "ui2":
                    return self.ui2()

                elif path == "active_theme":
                    return json.dumps({"theme": self._theme_name})

                elif path == "theme_list":
                    themes = self.theme_list()
                    return json.dumps(themes)

                elif path == "theme_download_list":
                    self.log("Theme download list fetching started...")
                    try:
                        isInternet, msg = check_internet_and_repo()
                        self.log(f"isInternet: {isInternet}, msg: {msg}")
                        if isInternet:

                            themes_dict = self.fetch_themes()
                            logging.warning(themes_dict)
                            return json.dumps({"status": 200, "data": themes_dict}), 200
                        else:
                            return json.dumps({"error": msg}), 500
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return json.dumps({"error": "Theme download list error"}), 500

                    
                elif str(path).split("/")[0] == "theme_export":
                    try: 
                        theme_name = path.split("/")[-1]
                        return self.theme_export(theme_name)
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "theme selection error", 500

                elif path == "load_config":
                    try:
                        if self.cfg_path is not None:
                            cfg_path = self.cfg_path
                            with open(cfg_path, 'r') as f:
                                config = toml.load(f)
                        else:
                            config = {}
                            cfg_path = ""
                        if self._theme_name != 'Default':
                            css_path = os.path.join(self._th_path, 'style.css')
                            info_path = os.path.join(self._th_path, 'info.json')

                            if os.path.exists(css_path):
                                with open(css_path, 'r') as f:
                                    css_content = f.read()
                            else:
                                css_content = 'No custom CSS'

                            if os.path.exists(info_path):
                                with open(info_path, 'r') as f:
                                    info_content = f.read()
                            else:
                                info_content = 'No custom Info'
                        else:
                            css_content = 'No custom CSS'
                            info_content = 'No custom Info'
                            css_path = 'No custom CSS path'
                            info_path = 'No custom Info path'

                        return json.dumps({
                            "config": config,
                            "css": css_content,
                            "info": info_content,
                            "name": self._theme_name,
                            "cfg_path": cfg_path,
                            "css_path": css_path,
                            "info_path": info_path,
                        })
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Error loading configuration", 500

            elif request.method == "POST":
                if path == "theme_select":
                    try:
                        jreq = request.get_json()
                        response = json.loads(json.dumps(jreq))
                        rot = int(response['rotation'])
                        theme = response['theme']
        
                        self.theme_save_config(response['theme'], response['rotation'])
                        self.refresh = True
                        return "success"
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "theme selection error", 500

                elif path == "version_compare":
                    is_newer = None
                    local_version = None
                    try:
                        jreq = request.get_json() 
                        response = json.loads(json.dumps(jreq)) 
                        theme = response['theme']
                        version = response['version']
                        logging.warning(f'Download selection: theme {theme} version {version}')
                        info_path = os.path.join(self._plug_root, "themes", theme, "info.json")
                        if not os.path.exists(info_path):
                            logging.error(f"Theme {theme} not found locally.")
                        else:
                            with open(info_path, 'r') as f:
                                local_info = json.load(f)
                                local_version = local_info.get('version')
                            if local_version is None:
                                logging.warning(f"Local version not found for theme {theme}.")
                                local_version = 'Unknown'
                            logging.warning(f"Local theme version: {local_version}")
                            is_newer = version > local_version if local_version != 'Unknown' else False
                        logging.warning(f'Is the online theme newer: {is_newer}')
                        return json.dumps({
                            'is_newer': is_newer,
                            'local_version': local_version
                        }), 200
                    except Exception as ex:
                        logging.error(f"Error handling theme version: {ex}")
                        logging.error(traceback.format_exc())
                        return json.dumps({'error': 'Theme version error'}), 500

                if path == "theme_download_select":
                    try:
                        jreq = request.get_json()
                        response = json.loads(json.dumps(jreq))
                        theme = response['theme']
                        logging.warning(f'Download selection: theme {theme}')
                        self.theme_downloader(theme)
                        return "success", 200
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return json.dumps({'error': f"theme download error: {ex}"}) , 500

                elif path == "fancyserver":
                    try:
                        jreq = request.get_json()
                        response = json.loads(json.dumps(jreq))
                        self.toggle_fancyserver(response['fancyserver'])
                        self.refresh = True
                        return "success"
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "theme selection error", 500
            
                elif path == "reset_css":
                    try:
                        data = request.get_json()
                        original_css_backup = os.path.join(self._pwny_root, 'ui/web/static/css/style.css.backup')
                        with open(original_css_backup, 'w+') as f:
                            f.write(CSS)
                        return "CSS reset successful!"
                    except Exception as e:
                        self.log(f"Error: {e}")
                        return "Error resetting CSS", 500

                elif path == "save_config":
                    try:
                        data = request.get_json()

                        config = data.get('config')
                        css = data.get('css')
                        info = data.get('info')
                        theme_cfg = {}
                        theme_cfg['theme'] = config['theme']
                        self.save_active_config(theme_cfg)
                        if self._th_path:  
                            css_src = os.path.join(self._th_path, 'style.css')
                            info_src = os.path.join(self._th_path, 'info.json')

                            if info != "No custom Info":
                                if os.path.exists(info_src):
                                    os.remove(info_src)
                                with open(info_src, 'w') as info_file:
                                    info_file.write(info)
                                self.log(f"Updated Info files at {self._th_path}")

                            if css != "No custom CSS":
                                if os.path.exists(css_src):
                                    os.remove(css_src)
                                with open(css_src, 'w') as css_file:
                                    css_file.write(css)
                                self.log(f"Updated CSS files at {self._th_path}")
                            
                            self.log(f"Updated CSS and Info files at {self._th_path}")
                        self.refresh = True
                        return "Configuration saved successfully", 200
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Error saving configuration", 500

                elif path == "create_theme":
                    try:
                        data = request.get_json()
                        theme_name = data['theme_name']
                        use_resolution = data['use_resolution']
                        use_orientation = data['use_orientation']
                        is_created = self.theme_creator(theme_name, state=self._state, oriented=use_orientation, resolution=use_resolution)
                        if is_created:
                            return "Theme created successfully", 200
                        else:
                            return "Theme with same name is existing", 500
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Error creating theme", 500

                elif path == "theme_copy":
                    try:
                        data = request.get_json()
                        theme = data['theme']
                        new_name = data['new_name']
                        themes_folder = os.path.join(self._plug_root, 'themes')
                        src_path = os.path.join(themes_folder, theme)
                        dst_path = os.path.join(themes_folder, new_name)
                        
                        if os.path.exists(dst_path):
                            self.log(f"Theme '{theme}' already exists. Skipping creation.")
                            return "Theme with same name is existing", 500

                        if os.path.exists(src_path):
                            copytree(src_path, dst_path)
                            return "Theme copied successfully", 200
                        else:
                            return "Source theme not found", 404
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Error copying theme", 500

                elif path == "theme_rename":
                    try:
                        data = request.get_json()
                        theme = data['theme']
                        new_name = data['new_name']
                        themes_folder = os.path.join(self._plug_root, 'themes')
                        src_path = os.path.join(themes_folder, theme)
                        dst_path = os.path.join(themes_folder, new_name)
                        
                        if os.path.exists(dst_path):
                            self.log(f"Theme '{theme}' already exists. Skipping creation.")
                            return "Theme with same name is existing", 500

                        if os.path.exists(src_path):
                            os.rename(src_path, dst_path)
                            return "Theme renamed successfully", 200
                        else:
                            return "Theme not found", 404
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Error renaming theme", 500

                elif path == "theme_upload":
                    try:
                        if 'zipFile' in request.files:
                            file = request.files['zipFile']
                            if file.filename == '':
                                return 'No selected file', 400
                            if file and allowed_file(file.filename):
                                filename = file.filename
                                themepath = os.path.join(self._plug_root, 'themes')
                                filepath = os.path.join(themepath, filename)
                                file.save(filepath)

                                with tempfile.TemporaryDirectory() as temp_dir:
                                    unzip_file(filepath, temp_dir)

                                    folders_in_zip = [
                                        name for name in os.listdir(temp_dir)
                                        if os.path.isdir(os.path.join(temp_dir, name))
                                    ]

                                    existing_folders = []
                                    for folder in folders_in_zip:
                                        target_folder = os.path.join(themepath, folder)
                                        if os.path.exists(target_folder):
                                            existing_folders.append(folder)

                                    if existing_folders:
                                        return f'{existing_folders} folders were not copied because they already exist.', 400

                                    for folder in folders_in_zip:
                                        source = os.path.join(temp_dir, folder)
                                        target = os.path.join(themepath, folder)
                                        copytree(source, target)

                                return 'Zip file uploaded and extracted successfully', 200
                            else:
                                return 'Invalid file type', 400
                        else:
                            return 'No file part in the request', 400
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return 'Theme upload error', 500
                
                elif path == "theme_delete":
                    try:
                        jreq = request.get_json()
                        response = json.loads(json.dumps(jreq))
                        theme = response['theme']
                        if theme in ['', self._theme_name]:
                            self.log('theme can\'t be deleted')
                            return "theme can't be deleted", 500
                        else:
                            themepath = os.path.join(self._plug_root, 'themes')
                            filepath = os.path.join(themepath, theme)
                            self.log(f'Delete theme at {filepath}')
                            os.system(f'rm -r {filepath}')
                            return "success"
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "theme selection error", 500
                elif path == "theme_info":
                    jreq = request.get_json()
                    response = json.loads(json.dumps(jreq))
                    theme = response['theme']
                    descpath = os.path.join(self._plug_root, 'themes', theme, 'info.json')
                    info = {
                        "author": "Unknown",
                        "version": "Unknown",
                        "display": "Unknown",
                        "plugins": "Unknown",
                        "notes": "Unknown"
                    }
                    if theme in ['Default', None]:
                        descpath = None
                        info = {
                                "author": "<a href='https://github.com/V0r-T3x'>V0rT3x</a>",
                                "version": "1.0.0",
                                "display": "All",
                                "plugins": "all",
                                "notes": "Default theme"
                            }

                    try:
                        if descpath is not None:
                            if descpath and os.path.exists(descpath):
                                with open(descpath, 'r') as json_file:
                                    info = json.load(json_file)
                        theme_info = info
                        return json.dumps(theme_info, default=serializer), 200

                    except Exception as ex:
                        logging.error(f"Error in theme info: {str(ex)}")
                        logging.error(traceback.format_exc())
                        return "theme selection error", 500

                elif path == "display_hijack":
                    try:
                        self.dispHijack = True
                        return "success", 200
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Display hijacking error", 500
                
                elif path == "display_pwny":
                    try:
                        self.dispHijack = False
                        return "success", 200
                    except Exception as ex:
                            logging.error(ex)
                            logging.error(traceback.format_exc())
                            return "Display Pwny error", 500
                elif path == "display_next":
                    try:
                        self.process_actions({"action": "switch_screen_mode"})
                        return "success", 200
                    except Exception as ex:
                            logging.error(ex)
                            logging.error(traceback.format_exc())
                            return "Display next error", 500
                elif path == "display_previous":
                    try:
                        self.process_actions({"action": "switch_screen_mode_reverse"})
                        return "success", 200
                    except Exception as ex:
                            logging.error(ex)
                            logging.error(traceback.format_exc())
                            return "Display previous error", 500
                elif path == "screen_saver_next":
                    try:
                        self.process_actions({"action": "next_screen_saver"})
                        return "success", 200
                    except Exception as ex:
                            logging.error(ex)
                            logging.error(traceback.format_exc())
                            return "Next screen saver error", 500
                elif path == "screen_saver_previous":
                    try:
                        self.process_actions({"action": "previous_screen_saver"})
                        return "success", 200
                    except Exception as ex:
                            logging.error(ex)
                            logging.error(traceback.format_exc())
                            return "previous screen saver error", 500
                elif path == "stealth":
                    try:
                        self.process_actions({"action": "stealth_mode"})
                        return "success", 200
                    except Exception as ex:
                            logging.error(ex)
                            logging.error(traceback.format_exc())
                            return "Stealth mode error", 500
                elif path == "navmenu":
                    try:
                        jreq = request.get_json()
                        response = json.loads(json.dumps(jreq))
                        action = response['action']
                        
                        action_mapping = {
                            'up': 'menu_up',
                            'down': 'menu_down',
                            'left': 'menu_left', 
                            'right': 'menu_right',
                            'select': 'menu_select',
                            'toggle': 'menu_toggle'
                        }
                        
                        menu_action = action_mapping.get(action)
                        if menu_action:
                            self.navigate_fancymenu({"action": menu_action})
                            return "success", 200
                        else:
                            return "Invalid navigation action", 400
                            
                    except Exception as ex:
                        logging.error(ex)
                        logging.error(traceback.format_exc())
                        return "Navigation error", 500

        except Exception as e:
            self.log(f"Error in webhook: {str(e)}")
            self.log(traceback.format_exc())
            return None