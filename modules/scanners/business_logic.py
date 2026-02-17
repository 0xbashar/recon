import asyncio
import aiohttp

async def scan(endpoint, param, anti_block, anomaly, **kwargs):
    """Use anomaly detector to find business logic flaws."""
    # This scanner is called after baseline collection.
    # We'll fuzz the parameter with a slightly modified value and check for anomalies.
    base_url = endpoint + ('' if '?' in endpoint else '?')
    # Get current value (if present in baseline)
    # For simplicity, assume param takes numeric values; we'll try +1
    test_url = base_url + f"{param}=999999"  # Arbitrary change
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, headers=anti_block.get_headers(), proxy=anti_block.get_proxy()) as resp:
                text = await resp.text()
                is_anomaly, reasons = anomaly.detect(endpoint, 'GET', param, resp, text)
                if is_anomaly:
                    return {'url': test_url, 'param': param, 'type': 'Business Logic', 'details': reasons, 'confidence': 50}
    except:
        pass
    return None
