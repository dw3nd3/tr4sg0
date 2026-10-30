import logging
import urllib.request
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError

from .plugin import manager as plugin_manager


def fetch(url: str):
    for callback in plugin_manager.plugin_before_fetch_callbacks:
        url = callback(url)

    d33_scheme = "d33://"
    if url.startswith(d33_scheme):
        print("embedded")
        return url[len(d33_scheme) :]

    is_local = urlparse(url).scheme == ""

    if is_local:
        with open(url, "rb") as f:
            bytes_ = f.read()
            for callback in plugin_manager.plugin_after_fetch_callbacks:
                bytes_ = callback(bytes_)
            return bytes_.decode("utf-8")

    else:
        try:
            logging.info("Fetching %s" % url)
            with urllib.request.urlopen(url) as response:
                bytes_ = response.read()
                for callback in plugin_manager.plugin_after_fetch_callbacks:
                    bytes_ = callback(bytes_)
                return bytes_.decode("utf-8")

        except URLError as e:
            logging.error(e.reason)

        except HTTPError as e:
            logging.error(e.code)
            logging.error(e.reason)
