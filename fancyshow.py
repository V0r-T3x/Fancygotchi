import logging
import time
import pwnagotchi.plugins as plugins

# This plugin is designed to demonstrate how to use the Fancygotchi's partial update feature (ui._update).
# It modifies the 'name' widget's position and color, verifies the changes, and reverts them upon unload.


class Fancyshow(plugins.Plugin):
    __author__ = 'V0r-T3x'
    __version__ = '1.0.0'
    __license__ = 'GPL3'
    __description__ = 'An example plugin to show how to use Fancygotchi\'s ui._update feature.'

    def __init__(self):
        logging.debug("fancyshow plugin created")
        # A dictionary to store options for the plugin (not used in this example but good practice).
        self.options = dict()
        # This will store the original properties of the widget we are modifying.
        self.original_widget_options = {}
        # A flag to ensure we only set our desired position once.
        self.position_set = False
        # Flags to control the plugin's state, especially during unload.
        self.unloaded = False
        self.reverting = False
        # The new widget properties we want to apply.
        self.widget_options = {
            'position': ["center", "center"],
            'color': ["lime", "red"]
        }
        # A counter to track if the UI state is consistently different from what we expect.
        self.discrepancy_counter = 0

    # called when the plugin is loaded
    def on_loaded(self):
        logging.info("fancyshow plugin loaded.")
        # Reset the unloaded flag when the plugin is loaded/reloaded.
        self.unloaded = False

    # called when the plugin is unloaded
    def on_unload(self, ui):
        logging.info("fancyshow plugin unloading...")
        self.reverting = True
        # Check if we have stored original options to revert to.
        if self.original_widget_options and hasattr(ui, '_update'):
            # Use Fancygotchi's partial update mechanism to revert the 'name' widget's properties.
            ui._update.update({
                'update': True,
                'partial': True,
                'dict_part': {'widget': {'name': self.original_widget_options}}
            })
            logging.info(f"fancyshow: attempting to revert 'name' options to {self.original_widget_options}")

            # Wait for the UI to confirm the change, with a timeout.
            timeout = 10  # seconds
            start_time = time.time()
            reverted = False
            while time.time() - start_time < timeout:
                # The `ui.fancy._state` attribute is provided by Fancygotchi and contains the current theme state.
                # We check this to verify that our reversion request has been processed.
                if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state and self.original_widget_options:
                    name_state = ui.fancy._state['name']
                    all_reverted = all(
                        # Normalize lists to tuples for comparison, handles nested lists if any.
                        (tuple(current) if isinstance(current, list) else current) ==
                        (tuple(expected_val) if isinstance(expected_val, list) else expected_val)
                        for prop, expected_val in self.original_widget_options.items()
                        for current in [name_state.get(prop)])
                    if all_reverted:
                        logging.info("fancyshow: successfully reverted 'name' position.")
                        reverted = True
                        break
                time.sleep(0.5)  # Check every half-second

            if not reverted:
                logging.warning(f"fancyshow: could not verify 'name' position was reverted within {timeout} seconds.")

        # Final cleanup of state variables for a clean unload.
        self.unloaded = True
        self.original_widget_options = {}
        self.position_set = False

    # This is called by Pwnagotchi when the UI is being set up.
    # called to set up the ui elements
    def on_ui_setup(self, ui):
        self._get_initial_options(ui)

    # called when the ui is updated
    def on_ui_update(self, ui):
        if self.unloaded or self.reverting:
            # Do nothing if the plugin is in the process of unloading.
            return

        # Get original position if we haven't already
        if not self.original_widget_options:
            self._get_initial_options(ui)
            # If we still don't have it, we can't do anything yet.
            if not self.original_widget_options:
                return

        # This block runs only once to apply the new widget options.
        if not self.position_set and hasattr(ui, '_update') and not ui._update.get('update', False):
            # Request a partial theme update to change the 'name' widget.
            ui._update.update({
                'update': True,
                'partial': True,
                'dict_part': {'widget': {'name': self.widget_options}}
            })
            self.position_set = True
            logging.info(f"fancyshow: setting 'name' options to {self.widget_options}")

        # This block runs on subsequent updates to verify that our changes have been applied and have persisted.
        # The UI state can be changed by other plugins or theme updates, so this check is important.
        # After setting, we can verify its position on subsequent updates
        if self.position_set and hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
            name_state = ui.fancy._state['name']
            for prop, expected_value in self.widget_options.items():
                current_value = name_state.get(prop)
                # Normalize lists to tuples for comparison
                if isinstance(expected_value, list):
                    expected_value = tuple(expected_value)
                if isinstance(current_value, list):
                    current_value = tuple(current_value)
                
                if current_value != expected_value:
                    # If the current state doesn't match our expected state, increment a counter.
                    # This might happen temporarily if another plugin is also updating the UI.
                    self.discrepancy_counter += 1
                    logging.warning(f"fancyshow: 'name' property '{prop}' is {current_value}, not {expected_value} as expected. Discrepancy count: {self.discrepancy_counter}")
                    if self.discrepancy_counter >= 15:
                        logging.warning("fancyshow: Discrepancy threshold reached. Investigating cause...")
                        
                        # Check if a pending partial update is the cause of the discrepancy
                        if hasattr(ui, '_update') and ui._update.get('update') and ui._update.get('partial'):
                            pending_changes = ui._update.get('dict_part', {}).get('widget', {}).get('name', {})
                            if pending_changes:
                                # Compare pending changes to our saved original options
                                if any(pending_changes.get(p) != self.original_widget_options.get(p) for p in pending_changes):
                                    logging.info("fancyshow: Detected a pending theme change. Updating baseline and re-applying options.")
                                    # The pending update is the new baseline
                                    self.original_widget_options.update(pending_changes)
                        else:
                            # No pending update, so re-check the current state from the UI
                            logging.info("fancyshow: No pending update detected. Re-evaluating original state from UI.")
                            self._get_initial_options(ui)

                        # Reset the flag to force re-application of widget_options
                        self.position_set = False
                        # Reset the counter
                        self.discrepancy_counter = 0
                        # Break the loop to allow re-application in the next on_ui_update cycle
                        break

    # A helper function to safely get the initial properties of the 'name' widget.
    def _get_initial_options(self, ui):
        # `ui.fancy._state` is a special attribute injected by Fancygotchi that holds the current theme's state.
        if hasattr(ui, 'fancy') and hasattr(ui.fancy, '_state') and 'name' in ui.fancy._state:
            name_state = ui.fancy._state['name']
            new_original_options = {}
            changed = False
            # We only care about the properties we intend to modify.
            for prop in self.widget_options.keys():
                if prop in name_state:
                    current_original_value = name_state.get(prop)
                    new_original_options[prop] = current_original_value
                    # Check if the baseline has changed since we last checked
                    if self.original_widget_options and self.original_widget_options.get(prop) != current_original_value:
                        changed = True
                else:
                    logging.warning(f"fancyshow: could not find original value for property '{prop}'.")
            
            # If this is the first time, store the fetched options.
            if not self.original_widget_options:
                self.original_widget_options = new_original_options
                logging.info(f"fancyshow: Stored initial 'name' options: {self.original_widget_options}")
            elif changed:
                # Check for false positive: if the "new" origin is what we're trying to set,
                # it's likely our own change being read back. Don't update the baseline.
                is_false_positive = all(
                    tuple(new_original_options.get(prop)) == tuple(val) if isinstance(val, list) else new_original_options.get(prop) == val
                    for prop, val in self.widget_options.items()
                )
                if is_false_positive:
                    logging.warning("fancyshow: Detected a potential false positive. The new baseline matches widget_options. Not updating original options.")
                else:
                    logging.warning(f"fancyshow: Original 'name' options changed from {self.original_widget_options} to {new_original_options}. Updating baseline.")
                    self.original_widget_options = new_original_options
            else:
                logging.debug("fancyshow: Re-checked original 'name' options. No changes to baseline.")
