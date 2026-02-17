import asyncio
import subprocess
from modules.anti_block import AntiBlock
from modules.proxy_manager import ProxyManager
import re

class Recon:
    def __init__(self, target, config):
        self.target = target
        self.config = config
        self.anti_block = AntiBlock(proxy_manager=ProxyManager(use_free=config['proxy']['use_free']))

    async def get_subdomains(self):
        """Run multiple subdomain discovery tools and return unique subdomains."""
        cmds = [
            f"subfinder -d {self.target} -silent",
            f"assetfinder --subs-only {self.target}",
            f"amass enum -passive -d {self.target}"
        ]
        subs = set()
        for cmd in cmds:
            proc = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            stdout, _ = await proc.communicate()
            for line in stdout.decode().splitlines():
                line = line.strip()
                if line:
                    subs.add(line)
        return list(subs)

    async def get_live_urls(self, subdomains):
        """Use httpx to filter live hosts."""
        if not subdomains:
            return []
        input_data = "\n".join(subdomains).encode()
        proc = await asyncio.create_subprocess_shell(
            f"httpx -silent -status-code -content-length -follow-redirects",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate(input=input_data)
        live = []
        for line in stdout.decode().splitlines():
            parts = line.split()
            if parts:
                live.append(parts[0])
        return live

    async def gather_urls(self, live_urls):
        """Collect URLs from various sources."""
        urls = set()
        # gau
        for url in live_urls:
            proc = await asyncio.create_subprocess_shell(
                f"gau --subs {url}",
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            for line in stdout.decode().splitlines():
                urls.add(line.strip())
        # waybackurls
        for url in live_urls:
            proc = await asyncio.create_subprocess_shell(
                f"waybackurls {url}",
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            for line in stdout.decode().splitlines():
                urls.add(line.strip())
        # hakrawler (requires URLs as input)
        input_data = "\n".join(live_urls).encode()
        proc = await asyncio.create_subprocess_shell(
            "hakrawler -subs -plain",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate(input=input_data)
        for line in stdout.decode().splitlines():
            urls.add(line.strip())
        # gospider
        for url in live_urls:
            proc = await asyncio.create_subprocess_shell(
                f"gospider -s {url} -c 5 -t 3 -d 1 --no-redirect",
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            stdout, _ = await proc.communicate()
            for line in stdout.decode().splitlines():
                if line.startswith("[url]") or line.startswith("[link]"):
                    u = line.split(' - ')[-1].strip()
                    urls.add(u)
        return list(urls)
