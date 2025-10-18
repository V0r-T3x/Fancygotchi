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
        self.original_name_pos = None
        self.loop_counter = 0

    # called when the plugin is loaded
    def on_loaded(self):
        logging.info("fancyshow plugin loaded.")

    # called when the plugin is unloaded
    def on_unload(self, ui):
        logging.info("fancyshow plugin unloaded")
        if self.original_name_pos and hasattr(ui, '_update'):
            # Set the update flag to revert the name position
            ui._update['update'] = True
            ui._update['partial'] = True
            ui._update['dict_part'] = {
                'widget': {
                    'name': {
                        'position': self.original_name_pos
                    }
                }
            }
            logging.info(f"fancyshow: reverting name position to its original state {self.original_name_pos}")

    # called to set up the ui elements
    def on_ui_setup(self, ui):
        pass

    # called when the ui is updated
    def on_ui_update(self, ui):
        # If we don't have the original position yet, try to get it. This should only run once.
        if self.original_name_pos is None:
            if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
                # Grab the position directly instead of re-running on_ui_setup
                self.original_name_pos = ui.fancy._state['name']['position']
                self.x, self.y = self.original_name_pos
                logging.info(f"fancyshow: found original name position at {self.original_name_pos}")

        # Only update every 2 loops for a more responsive demo
        self.loop_counter += 1
        if self.loop_counter % 2 != 0:
            return

        # Randomly move the 'name' widget's position
        self.x += random.randint(-2, 2)
        self.y += random.randint(-2, 2)

        # Don't start moving the widget until its original position has been loaded.
        if self.original_name_pos is None:
            return

        # Keep the widget on screen
        self.x = max(0, min(self.x, ui.width() - 50))
        self.y = max(0, min(self.y, ui.height() - 10))

        if hasattr(ui, '_update'):
            # Set the update flag and data for a partial theme update
            ui._update['update'] = True
            ui._update['partial'] = True
            # Define the widget and property to change
            ui._update['dict_part'] = {
                'widget': {
                    'name': {
                        'position': [self.x, self.y],
                    }
                }
            }
            logging.debug(f"fancyshow: updating name position to {[self.x, self.y]}")
