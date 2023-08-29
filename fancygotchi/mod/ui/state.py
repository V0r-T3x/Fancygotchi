from threading import Lock
import logging


class State(object):
    def __init__(self, state={}):
        self._state = state
        self._lock = Lock()
        self._listeners = {}
        self._changes = {}

    def add_element(self, key, elem):
        #logging.warning("Adding " + key + " = " + str(elem))
        self._state[key] = elem
        self._changes[key] = True

    def has_element(self, key):
        return key in self._state

    def remove_element(self, key):
        #logging.warning("Removing " + key)
        del self._state[key]
        self._changes[key] = True

    def add_listener(self, key, cb):
        with self._lock:
            self._listeners[key] = cb

    def items(self):
        with self._lock:
            return self._state.items()

    def get(self, key):
        with self._lock:
            return self._state[key].value if key in self._state else None
        
    def getallattr(self):
        for attr in dir(self._state):
            if not attr.startswith("__"):
                value = getattr(self._state, attr)
                #logging.warning('%s: %s' % (attr, value))
        
    def get_attr(self, key, attribute='value'):
        with self._lock:
            if key in self._state:
                return getattr(self._state[key], attribute)
            else:
                return None
        
    def get_color(self, key):
        with self._lock:
            return self._state[key].color if key in self._state else None

    def reset(self):
        with self._lock:
            self._changes = {}

    def changes(self, ignore=()):
        with self._lock:
            changes = []
            for change in self._changes.keys():
                if change not in ignore:
                    changes.append(change)
            return changes

    def has_changes(self):
        with self._lock:
            return len(self._changes) > 0

    def set(self, key, value):
        with self._lock:
            if key in self._state:
                prev = self._state[key].value
                self._state[key].value = value

                if prev != value:
                    self._changes[key] = True
                    if key in self._listeners and self._listeners[key] is not None:
                        self._listeners[key](prev, value)

    def set_color(self, key, value):
        with self._lock:
            if key in self._state:
                prev = self._state[key].color
                self._state[key].color = value

                if prev != value:
                    self._changes[key] = True
                    if key in self._listeners and self._listeners[key] is not None:
                        self._listeners[key](prev, value)

    def set_font(self, key, value):
        with self._lock:
            if key in self._state:
                self._state[key].font = value

    def set_textfont(self, key, value):
        with self._lock:
            if key in self._state:
                self._state[key].text_font = value

    def set_labelfont(self, key, value):
        with self._lock:
            if key in self._state:
                self._state[key].label_font = value


    def set_attr(self, key, attribute, value):
        #logging.warning('%s %s %s' % (key, attribute, value))
        with self._lock:
            if key in self._state:
                #logging.warning(self._state[key])
                prev = getattr(self._state[key], attribute)
                setattr(self._state[key], attribute, value)

                if prev != value:
                    self._changes[key] = True
                    if key in self._listeners and self._listeners[key] is not None:
                        self._listeners[key](prev, value)
