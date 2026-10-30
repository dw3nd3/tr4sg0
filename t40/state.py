from urllib.parse import urlparse
import logging

__is_local = False
__host = ""
_url = ""
_inventory = {}
next_url = None

base_room_generator = None  # Must be initialized from the outside


def is_local():
    global __is_local
    return __is_local


def set_url(url):
    global _url, __host, __is_local
    _url = url
    if url.startswith("d33://"):
        __host = str(hash(url))
        __is_local = False
        logging.info("Set URL to <embedded>")
    else:
        __host = urlparse(url).netloc
        __is_local = __host == ""
        logging.info("Set URL to: %s | local: %s" % (url, __is_local))


def get_url():
    return _url


def get_inventory():
    return _inventory.get(__host, set("_"))


def add_token(token):
    current_inventory = get_inventory()
    current_inventory.add(token)
    _inventory[__host] = current_inventory


def remove_token(token):
    current_inventory = get_inventory()
    current_inventory.remove(token)
    _inventory[__host] = current_inventory
