from urllib.parse import urlparse

__host = ""
_url = ""
_inventory = {}
next_url = None

def set_url(url):
    global _url, __host
    _url = url
    __host = urlparse(url).netloc

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