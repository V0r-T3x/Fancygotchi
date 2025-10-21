import logging
import random
import time
import pwnagotchi.plugins as plugins


class Fancyshow(plugins.Plugin):
    __author__ = 'V0r-T3x'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'An example plugin to show how to use Fancygotchi\'s ui._update feature.'

    def __init__(self):
        logging.debug("fancyshow plugin created")
        self.options = dict()
        self.original_name_pos = None
        self.position_set = False
        self.unloaded = False
        self.reverting = False

    # called when the plugin is loaded
    def on_loaded(self):
        logging.info("fancyshow plugin loaded.")
        self.unloaded = False

    # called when the plugin is unloaded
    def on_unload(self, ui):
        logging.info("fancyshow plugin unloading...")
        self.reverting = True
        if self.original_name_pos and hasattr(ui, '_update'):
            ui._update['update'] = True
            ui._update['partial'] = True
            ui._update['dict_part'] = {
                'widget': {
                    'name': {
                        'position': self.original_name_pos
                    }
                }
            }
            logging.info(f"fancyshow: attempting to revert 'name' position to {self.original_name_pos}")

            # Wait for the UI to confirm the change, with a timeout.
            timeout = 10  # seconds
            start_time = time.time()
            reverted = False
            while time.time() - start_time < timeout:
                if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
                    current_pos = ui.fancy._state['name'].get('position')
                    if tuple(current_pos) == tuple(self.original_name_pos):
                        logging.info("fancyshow: successfully reverted 'name' position.")
                        reverted = True
                        break
                time.sleep(0.5)  # Check every half-second

            if not reverted:
                logging.warning(f"fancyshow: could not verify 'name' position was reverted within {timeout} seconds.")
 
        self.unloaded = True
        self.original_name_pos = None
        self.position_set = False

    # called to set up the ui elements
    def on_ui_setup(self, ui):
        self._get_initial_pos(ui)

    # called when the ui is updated
    def on_ui_update(self, ui):
        if self.unloaded or self.reverting:
            return

        # Get original position if we haven't already
        if self.original_name_pos is None:
            self._get_initial_pos(ui)
            # If we still don't have it, we can't do anything yet.
            if self.original_name_pos is None:
                return

        # Set the position to [0, 0] once
        if not self.position_set and hasattr(ui, '_update') and not ui._update.get('update', False):
            ui._update['update'] = True
            ui._update['partial'] = True
            ui._update['dict_part'] = {
                'widget': {
                    'name': {
                        'position': [0, 0],
                    }
                }
            }
            self.position_set = True
            logging.info("fancyshow: setting 'name' position to [0, 0]")

        # After setting, we can verify its position on subsequent updates
        if self.position_set and hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
            current_pos = ui.fancy._state['name'].get('position')
            if tuple(current_pos) != (0, 0):
                logging.warning(f"fancyshow: 'name' position is {current_pos}, not [0, 0] as expected.")

    def _get_initial_pos(self, ui):
        # Only try to get the position if we don't have it yet.
        if self.original_name_pos is not None:
            return

        if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
            pos = ui.fancy._state['name'].get('position') # Use .get for safety
            if pos:
                self.original_name_pos = list(pos) # Make a copy
                logging.info(f"fancyshow: found original name position at {self.original_name_pos}")
            else:
                logging.warning("fancyshow: 'name' widget found in fancy._state, but has no 'position'.")
