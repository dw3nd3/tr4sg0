from typing import Callable, List

from ..parser import TokenType
from . import manager

def directive(name: str, args: List[TokenType], func: Callable):
    def wrapper(self, lx):
        parsed_args = [lx.token(arg) for arg in args]
        return func(*parsed_args)
    manager.plugin_directives[name] = wrapper
    return func

def command(name: str, func: Callable):
    manager.plugin_commands[name] = func
    return func

def before_fetch(func: Callable):
    manager.plugin_before_fetch_callbacks.append(func)
    return func

def after_fetch(func: Callable):
    manager.plugin_after_fetch_callbacks.append(func)
    return func

def before_parse(func: Callable):
    manager.plugin_before_parse_callbacks.append(func)
    return func

def after_parse(func: Callable):
    manager.plugin_after_parse_callbacks.append(func)
    return func

def on_user_event(func: Callable):
    manager.plugin_on_user_event_callbacks.append(func)
    return func

def on_window_open(func: Callable):
    manager.plugin_on_window_open.append(func)
    return func

def on_window_close(func: Callable):
    manager.plugin_on_window_close.append(func)
    return func