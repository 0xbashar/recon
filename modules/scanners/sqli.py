import asyncio
import aiohttp
import re
from modules.payloads import get_sqli_payloads

async def scan(endpoint, param, anti_block, **kwargs):
    """Lightweight SQLi detection with time/error based payloads."""
    payloads = get_sqli_payloads('time_based')  # Load from payloads module
    base_url = endpoint + ('' if '?' in endpoint else '?')
    for payload in payloads:
        test_url = f"{base_url}{param}={payload}"
        try:
            async with aiohttp.ClientSession() as session:
                start = asyncio.get_event_loop().time()
                async with session.get(test_url, headers=anti_block.get_headers(), proxy=anti_block.get_proxy(), timeout=10) as resp:
                    text = await resp.text()
                elapsed = asyncio.get_event_loop().time() - start
                # Time-based detection
                if elapsed > 5:
                    return {'url': test_url, 'param': param, 'type': 'SQLi (time-based)', 'confidence': 70}
                # Error-based detection
                if re.search(r"SQL syntax|mysql_fetch|ORA-[0-9]{5}|PostgreSQL.*ERROR|Microsoft OLE DB", text, re.I):
                    return {'url': test_url, 'param': param, 'type': 'SQLi (error)', 'confidence': 80}
        except:
            pass
        await anti_block.delay()
    return None
