import asyncio
import uuid
import aiohttp
from modules.interactsh import Interactsh

async def scan(endpoint, param, anti_block, **kwargs):
    """SSRF detection using interactsh."""
    client = Interactsh()
    token = str(uuid.uuid4())[:8]
    callback_url = client.get_url(token)
    base_url = endpoint + ('' if '?' in endpoint else '?')
    test_url = f"{base_url}{param}={callback_url}"
    try:
        async with aiohttp.ClientSession() as session:
            await session.get(test_url, headers=anti_block.get_headers(), proxy=anti_block.get_proxy(), timeout=5)
    except:
        pass
    await asyncio.sleep(5)  # Wait for potential callback
    if client.check_interaction(token):
        return {'url': test_url, 'param': param, 'type': 'SSRF', 'confidence': 85}
    return None
