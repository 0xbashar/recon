import aiohttp
import asyncio
import random
from typing import List, Dict
import requests
from rich.console import Console

console = Console()

class ProxyManager:
    def __init__(self, use_free=True, max_proxies=50, test_url='http://httpbin.org/ip'):
        self.use_free = use_free
        self.max_proxies = max_proxies
        self.test_url = test_url
        self.proxies: List[Dict[str, str]] = []
        self.current_index = 0
        if use_free:
            asyncio.create_task(self._refresh_proxies())

    async def _refresh_proxies(self):
        """Fetch fresh proxies from public sources."""
        sources = [
            'https://free-proxy-list.net/',
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
        ]
        all_proxies = []
        for src in sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(src, timeout=10) as resp:
                        text = await resp.text()
                        # Simple parsing (assumes IP:PORT per line)
                        for line in text.splitlines():
                            line = line.strip()
                            if ':' in line:
                                ip, port = line.split(':')
                                all_proxies.append({'http': f'http://{ip}:{port}', 'https': f'http://{ip}:{port}'})
            except:
                continue
        # Test proxies (limited to max_proxies)
        tested = []
        for proxy in all_proxies[:self.max_proxies*2]:
            if await self._test_proxy(proxy):
                tested.append(proxy)
                if len(tested) >= self.max_proxies:
                    break
        self.proxies = tested
        console.log(f"[green]Proxy pool: {len(self.proxies)} working proxies[/]")

    async def _test_proxy(self, proxy):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.test_url, proxy=proxy['http'], timeout=5) as resp:
                    if resp.status == 200:
                        return True
        except:
            pass
        return False

    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return proxy['http']

    def rotate(self):
        self.current_index = (self.current_index + 1) % len(self.proxies) if self.proxies else 0
