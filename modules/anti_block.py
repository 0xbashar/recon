import random
import asyncio
from fake_useragent import UserAgent

class AntiBlock:
    def __init__(self, proxy_manager=None, delay_range=(1, 3)):
        self.proxy_manager = proxy_manager
        self.delay_range = delay_range
        self.ua = UserAgent()

    async def delay(self):
        await asyncio.sleep(random.uniform(*self.delay_range))

    def get_headers(self):
        return {'User-Agent': self.ua.random}

    def get_proxy(self):
        if self.proxy_manager:
            return self.proxy_manager.get_proxy()
        return None
