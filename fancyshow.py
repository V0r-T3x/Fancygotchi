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
        self.is_unloading = False

    # called when the plugin is loaded
    def on_loaded(self):
        logging.info("fancyshow plugin loaded.")
        self.is_unloading = False # Reset on load
        self.original_name_pos = None # Reset on load

    # called when the plugin is unloaded
    def on_unload(self, ui):
        logging.info("fancyshow plugin unloaded")
        self.is_unloading = True
        if self.original_name_pos and hasattr(ui, '_update'):
            # Set the update flag to revert the name position
            ui._update['update'] = True
            ui._update['partial'] = True # It's a partial update
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
        # Try to get the original position during setup.
        self._get_initial_pos(ui)

    # called when the ui is updated
    def on_ui_update(self, ui):
        if self.is_unloading:
            return
        self._get_initial_pos(ui)

        self.loop_counter = (self.loop_counter + 1) % 8
        if self.loop_counter != 0:
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
            
            logging.debug(f"fancyshow: updating name position to {[self.x, self.y]}")

    def _get_initial_pos(self, ui):
        # If a full theme update is happening, we need to get the new original position.
        if hasattr(ui, '_update') and ui._update.get('update', False) and not ui._update.get('partial', False):
            self.original_name_pos = None

        # Always try to get the current position from the UI state to ensure we're not working with stale data.
        current_pos = None
        if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
            current_pos = ui.fancy._state['name']['position']
        elif hasattr(ui, '_state') and 'name' in ui._state._state:
            try:
                current_pos = ui._state.get_attr('name', 'xy')
            except Exception:
                logging.warning("fancyshow: could not get 'name' widget position from ui._state.")

        if current_pos is not None:
            if self.original_name_pos is None:
                logging.info(f"fancyshow: found original name position from ui.fancy._state at {self.original_name_pos}")
                self.original_name_pos = current_pos
            self.x, self.y = current_pos
