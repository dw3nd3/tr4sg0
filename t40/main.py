# t40 - An extensible browser for the d33 web
# Copyright (C) 2026 MiguelMJ
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import time
import logging
import json
from pathlib import Path
from argparse import ArgumentParser
from . import fetcher, parser, serializer, view, config, state, model, crawler
from .plugin import manager as plugin_manager
from .util import nc

_dev_mode_filewatch = None


def update_watch():
    global _dev_mode_filewatch
    if state.is_local():
        _dev_mode_filewatch = os.path.getmtime(state.get_url())
        logging.info("Update file watch: %s" % _dev_mode_filewatch)
    else:
        _dev_mode_filewatch = None


def detect_change():
    global _dev_mode_filewatch
    has_changed = state.is_local() and _dev_mode_filewatch != os.path.getmtime(
        state.get_url()
    )
    if has_changed:
        update_watch()
        logging.info(
            "Detected change of %s at %s" % (state.get_url(), _dev_mode_filewatch)
        )
    return has_changed


def open_url(url):
    room = parser.parse(fetcher.fetch(url))
    view.open(room)
    state.set_url(url)
    update_watch()
    return room


def run():
    argparser = ArgumentParser(description="An extensible browser for the dw3nd3 web")
    argparser.add_argument("url", nargs="?")
    argparser.add_argument(
        "-d",
        "--dev",
        action="store_const",
        const="dev"
    )
    group = argparser.add_mutually_exclusive_group()
    group.add_argument(
        "-m",
        "--minify",
        action="store_true",
        help="instead of opening the room, print a standard minified version to stdout",
    )
    group.add_argument(
        "-e",
        "--expand",
        action="store_true",
        help="instead of opening the room, print a standard expanded version to stdout",
    )
    group.add_argument(
        "-c",
        "--crawl",
        action="store_true",
        help="obtain an index of rooms from a root hall"
    )

    args = argparser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s]\t%(message)s"
    )
    config.load(Path(__file__).parent / "config.ini")

    if args.minify:
        state.base_room_generator = lambda: model.Room.empty()
        room = parser.parse(fetcher.fetch(args.url))
        print(serializer.minify(room))
 
    elif args.expand:
        state.base_room_generator = lambda: model.Room.empty()
        room = parser.parse(fetcher.fetch(args.url))
        print(serializer.expand(room))

    elif args.crawl:
        state.base_room_generator = lambda: model.Room.empty()
        print(json.dumps(crawler.crawl(args.url), indent=2))

    else:
        plugin_manager.load()
        view.setup()
        state.base_room_generator = lambda: model.Room.default()

        open_url(nc(args.url, config.get("BROWSER", "Home", "", str)))

        mode = nc(args.dev, config.get("BROWSER", "Mode", "normal", str))
        logging.info("Browser mode: %s" % mode)

        for _ in view.run():
            if state.next_url:
                open_url(state.next_url)
                state.next_url = None

            if mode == "dev" and detect_change():
                backup = view.current_room()
                try:
                    room = open_url(state.get_url())  # refresh
                    logging.info("Reload after changes: %s" % state.get_url())
                except:
                    view.open(backup)
                    logging.warning("[dev mode] Could't reload")
