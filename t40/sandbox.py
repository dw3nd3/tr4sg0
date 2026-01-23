import logging
from dataclasses import dataclass

from . import config, state
from .model import Room
from .plugin import manager as plugin_manager

import pygame

def execute(command, view):
    match command.varid:
        case "say":
            view.print(command.arg)
        case "tok":
            state.add_token(command.arg)
            logging.info("Obtained %s" % command.arg)
        case "del":
            state.remove_token(command.arg)
            logging.info("Removed %s" % command.arg)
        case "opn":
            state.next_url = command.arg
        case _:
            try_user_command(command)

def try_user_command(command):
    user_command = plugin_manager.plugin_commands.get(command.varid)
    if user_command:
        user_command(command.arg)
    else:
        logging.error("Unknown command %s" % command.varid)
