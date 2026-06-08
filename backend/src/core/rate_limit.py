import os

from slowapi import Limiter
from slowapi.util import get_remote_address


enabled = os.getenv("TESTING") != "True" and os.getenv("DISABLE_RATE_LIMIT") != "True"

limiter = Limiter(key_func=get_remote_address, enabled=enabled)
