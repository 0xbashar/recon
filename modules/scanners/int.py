# Scanners package
"""
Vulnerability Scanners
----------------------
Each scanner module exports an async 'scan' function that takes:
    endpoint: str - The URL to test
    param: str - The parameter name to fuzz
    anti_block: AntiBlock - For rate limiting and proxy rotation
    **kwargs - Additional scanner-specific arguments

Returns a dict with finding details or None.
"""

from .sqli import scan as sqli
from .xss import scan as xss
from .ssrf import scan as ssrf
from .idor import scan as idor
from .business_logic import scan as business_logic

__all__ = ['sqli', 'xss', 'ssrf', 'idor', 'business_logic']
