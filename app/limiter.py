# app/limiter.py
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import ENV

_enabled = (ENV != "testing")
limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
