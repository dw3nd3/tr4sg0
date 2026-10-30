import importlib
import pkgutil
import logging
from . import index

loaded_plugins = {}
plugin_directives = {}
plugin_commands = {}
plugin_before_fetch_callbacks = []
plugin_after_fetch_callbacks = []
plugin_before_parse_callbacks = []
plugin_after_parse_callbacks = []
plugin_on_user_event_callbacks = []
plugin_on_window_open = []
plugin_on_window_close = []


def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def load():
    global loaded_plugins
    for finder, name, ispkg in iter_namespace(index):
        logging.info("Loading plugin: %s" % name)
        loaded_plugins[name] = importlib.import_module(name)
    logging.info("Loaded %s plugins" % len(loaded_plugins))
