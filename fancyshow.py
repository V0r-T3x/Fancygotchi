import logging
import random

import pwnagotchi.plugins as plugins


class Fancyshow(plugins.Plugin):
    __author__ = 'V0r-T3x'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'An example plugin to show how to use Fancygotchi\'s ui._update feature.'

    def __init__(self):
        logging.debug("fancyshow plugin created")
        self.options = dict()
        self.x = 0
        self.y = 0
        self.loop_counter = 0

    # called when the plugin is loaded
    def on_loaded(self):
        logging.info("fancyshow plugin loaded.")

    # called to set up the ui elements
    def on_ui_setup(self, ui):
        # Initialize position based on UI dimensions
        self.x = ui.width() // 2
        self.y = ui.height() // 2

    # called when the ui is updated
    def on_ui_update(self, ui):
        # Only update every 8 loops
        self.loop_counter += 1
        if self.loop_counter % 8 != 0:
            return

        # Randomly move the 'name' widget's position
        self.x += random.randint(-2, 2)
        self.y += random.randint(-2, 2)

        # Keep the widget on screen
        self.x = max(0, min(self.x, ui.width() - 50))
        self.y = max(0, min(self.y, ui.height() - 10))

        # Check if Fancygotchi has initialized the _update attribute on the ui object
        if hasattr(ui, '_update'):
            # Set the update flag and data for a partial theme update
            ui._update['update'] = True
            ui._update['partial'] = True
            # Define the widget and property to change
            ui._update['dict_part'] = {
                'widget': {
                    'name': {
                        'position': [self.x, self.y]
                    }
                }
            }
            logging.debug(f"fancyshow: updating name position to {self.x}, {self.y}")
