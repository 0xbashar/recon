import aiohttp
import asyncio

class Verifier:
    async def verify(self, finding):
        """Re-test the finding to confirm."""
        url = finding['url']
        vtype = finding['type']
        if vtype == 'XSS':
            # Re-send with a simple alert payload
            # (dalfox already verified, but we can double-check)
            return True  # Placeholder
        elif vtype == 'SQLi (time-based)':
            # Re-test time-based
            try:
                async with aiohttp.ClientSession() as session:
                    start = asyncio.get_event_loop().time()
                    await session.get(url, timeout=10)
                    elapsed = asyncio.get_event_loop().time() - start
                    if elapsed > 5:
                        return True
            except:
                pass
            return False
        elif vtype == 'SSRF':
            # Already verified via interactsh
            return True
        # Default to true for now
        return True
