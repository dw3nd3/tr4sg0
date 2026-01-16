import logging
import urllib.request
from urllib.parse import urlparse
from urllib.error import URLError, HTTPError


def fetch(url):
    is_local = urlparse(url).scheme == ""
    
    if is_local:
        with open(url, "r") as f:
            return f.read()

    else:
        try:
            with urllib.request.urlopen(url) as response:
                return response.read()

        except URLError as e:
            logging.error(e.reason)
        
        except HTTPError as e:
            logging.error(e.code)
            logging.error(e.reason)
