import configparser

_config = None

def load(configpath):
    global _config
    _config = configparser.ConfigParser()
    _config.read(configpath)

def get(section, value, default=None, type=None):
    global _config
    if _config is None:
        raise RuntimeError("Config not loaded")
    
    try:
        val = _config[section][value]
        if type is not None:
            return type(val)
    except KeyError:
        return default

def get_plugin_list():
    global _config
    if _config is None:
        raise RuntimeError("Config not loaded")
    
    try:
        return list(_config["PLUGINS"].keys())
    except KeyError:
        return []