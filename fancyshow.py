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
        self.x = 0
        self.y = 0
        self.original_name_pos = None
        self.loop_counter = 0
        self.unloaded = False
        self.reverting = False

    # called when the plugin is loaded
    def on_loaded(self):
        logging.info("fancyshow plugin loaded.")
        self.unloaded = False

    # called when the plugin is unloaded
    def on_unload(self, ui):
        logging.info("fancyshow plugin unloading.")
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

    # called to set up the ui elements
    def on_ui_setup(self, ui):
        self._get_initial_pos(ui)

    # called when the ui is updated
    def on_ui_update(self, ui):
        self.loop_counter = (self.loop_counter + 1) % 8 # Update every 8 cycles
        if self.loop_counter != 0:
            return

        # Randomly move the 'name' widget's position
        self.x += random.randint(-2, 2)
        self.y += random.randint(-2, 2)

        # Ensure we have the original position before we start moving things.
        if self.original_name_pos is None:
            self._get_initial_pos(ui)

        # If we still don't have it, we can't proceed.
        if self.original_name_pos is None:
            return

        # Keep the widget on screen
        self.x = max(0, min(self.x, ui.width() - 50))
        self.y = max(0, min(self.y, ui.height() - 10))

        if hasattr(ui, '_update') and not ui._update.get('update', False):
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
            
            logging.debug(f"fancyshow: updating 'name' position to {[self.x, self.y]}")

    def _get_initial_pos(self, ui):
        # Only try to get the position if we don't have it yet.
        if self.original_name_pos is not None:
            return

        if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
            pos = ui.fancy._state['name'].get('position') # Use .get for safety
            if pos:
                self.original_name_pos = list(pos) # Make a copy
                self.x, self.y = self.original_name_pos
                logging.info(f"fancyshow: found original name position at {self.original_name_pos}")
            else:
                logging.warning("fancyshow: 'name' widget found in fancy._state, but has no 'position'.")
