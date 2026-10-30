import pygame
import tempfile
import webbrowser
import logging

from .. import api as plugin_api
from ... import state, config
from ...util import pos2idx, rle_decompress
from ...model import RuleCase, Command
from ...view import get_view

_history = []
_cached_files = {}
_last_url_fetched = None

@plugin_api.before_fetch
def add_to_history(url):
    global _history, _last_url_fetched
    _last_url_fetched = url
    _history.append(url)
    return url

@plugin_api.before_fetch
def cache(url):
    global _cached_files
    if url in _cached_files:
        logging.info("Cache hit for %s" % url)
        return _cached_files[url]
    else:
        logging.info("Cache miss for %s" % url)
        return url
    
@plugin_api.before_fetch
def loading_notice(url):
    pygame.display.set_caption("Wait...")
    return url

@plugin_api.after_fetch
def final_caption(bytes_):
    global _last_url_fetched
    if _last_url_fetched.startswith("d33://"):
        caption = "<embedded>"
    else:
        caption = _last_url_fetched
    pygame.display.set_caption("d33 - " + _last_url_fetched)
    return bytes_

@plugin_api.after_fetch
def cache_response(bytes_):
    global _cached_files, _last_url_fetched
    if _last_url_fetched is None or _last_url_fetched in _cached_files:
        logging.info("Don't cache %s" % _last_url_fetched)
        return bytes_
    with tempfile.NamedTemporaryFile(delete=False) as f:
        logging.info("Caching %s" % _last_url_fetched)
        f.write(bytes_)
        _cached_files[_last_url_fetched] = f.name
    return bytes_


@plugin_api.on_user_event
def process_going_web(event):
    global _history
    if event.type == pygame.KEYDOWN and event.key == pygame.K_o:
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            logging.info("Opening %s" % _history[-1])
            get_view().print("Peeking at %s" % _history[-1])
            webbrowser.open(_history[-1])
    
@plugin_api.on_user_event
def process_refresh(event):
    global _history, _cached_files
    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            current_url = _history.pop()
            if current_url in _cached_files:
                del _cached_files[current_url]
            logging.info("Reloading %s" % current_url)
            state.next_url = current_url
    
@plugin_api.on_user_event
def process_go_back(event):
    global _history
    if len(_history) < 2: return
    if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
        _history.pop() 
        previous_url = _history.pop()
        logging.info("Go back to %s" % previous_url)
        state.next_url = previous_url
            

@plugin_api.after_parse
def create_backlink_door(room):
    if not config.get("PLUGIN.BROWSER_EXPERIENCE", "Backlink", False, bool):
        return room

    global _history
    if len(_history) > 1:
        logging.debug("Backlinking %s" % _history[-2])
        room.sprites["goback"] = (
            "bcbbbbcbbccccccbbcddddcbdccccccddcddddcddccccccddcddddcdbddddddb"
        )
        room.idxmap[pos2idx(*room.start)].update(
            {
                "sprite": "goback",
                "rule": "goback",
            }
        )
        room.rules["goback"] = [
            RuleCase(
                antecedents=[
                    set(["_"]),
                ],
                consequent=[
                    Command("opn", _history[-2]),
                ],
            )
        ]
    return room
