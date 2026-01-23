import sys
import logging
from . import fetcher, parser, serializer, view, config, state
from .plugin import manager as plugin_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]\t%(message)s")
config.load("config.ini")
plugin_manager.load()
view.setup()

def open_url(url):
    room = parser.parse(fetcher.fetch(url))
    view.open(room)

url = sys.argv[1]

open_url(url)
for _ in view.run():
    if state.next_url:
        open_url(state.next_url)
        state.next_url = None
        
