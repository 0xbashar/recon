#!/usr/bin/env python3
"""
OmniHunter - Ultimate Automated Bug Bounty Tool
Author: Your Name
Description: Combines recon, parameter extraction, and multi-scanner vulnerability detection.
"""

import asyncio
import argparse
import yaml
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from modules.update import UpdateManager
from modules.recon import Recon
from modules.params import ParamExtractor
from modules.proxy_manager import ProxyManager
from modules.anti_block import AntiBlock
from modules.anomaly import AnomalyDetector
from modules.notifications import NotificationManager
from modules.console import OmniHunterUI
from modules import scanners
from modules.verify import Verifier
from modules.ml import MLHeuristics
import modules.db as db

console = Console()

class OmniHunter:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.target = self.config['target']
        self.platform = self.config.get('platform', 'unknown')
        self.db_path = Path(f"omnihunter_{self.target.replace('.', '_')}.db")
        db.init(self.db_path)
        self.proxy_manager = ProxyManager(use_free=self.config['proxy']['use_free'])
        self.anti_block = AntiBlock(proxy_manager=self.proxy_manager)
        self.anomaly = AnomalyDetector(self.config.get('anomaly', {}))
        self.notifier = NotificationManager(self.config.get('notifications', {}))
        self.ui = OmniHunterUI()
        self.ml = MLHeuristics(enabled=self.config.get('ml_enabled', True))
        self.update_mgr = UpdateManager(self.config.get('tools_path', '/usr/local/bin'))
        self.verifier = Verifier()
        self.scan_queue = asyncio.Queue()
        self.results = []
        self.running = True

    async def run(self):
        # 1. Update tools if needed
        if self.config.get('update_on_start', True):
            console.log("[bold yellow]Checking for tool updates...[/]")
            await self.update_mgr.check_all()

        # 2. Start real-time console in a thread
        self.ui.start()

        # 3. Recon phase
        console.log("[bold cyan]Starting reconnaissance...[/]")
        recon = Recon(self.target, self.config)
        subdomains = await recon.get_subdomains()
        console.log(f"[green]Found {len(subdomains)} subdomains[/]")
        live_urls = await recon.get_live_urls(subdomains)
        console.log(f"[green]Found {len(live_urls)} live URLs[/]")
        all_urls = await recon.gather_urls(live_urls)
        all_urls = list(set(all_urls))
        console.log(f"[green]Total unique URLs: {len(all_urls)}[/]")
        db.save_urls(all_urls)

        # 4. Parameter extraction
        console.log("[bold cyan]Extracting parameters...[/]")
        param_extractor = ParamExtractor(all_urls, self.config.get('scope'))
        endpoints = param_extractor.extract()
        console.log(f"[green]Extracted {len(endpoints)} endpoints with solid parameters[/]")
        db.save_endpoints(endpoints)

        # 5. Baseline collection (for anomaly detection)
        console.log("[bold cyan]Collecting baseline responses...[/]")
        await self.collect_baselines(endpoints)

        # 6. Enqueue scan tasks
        for endpoint, params in endpoints.items():
            for param in params:
                await self.scan_queue.put((endpoint, param))

        # 7. Start scanner workers
        workers = [asyncio.create_task(self.scanner_worker(i)) for i in range(self.config.get('concurrency', 10))]
        await self.scan_queue.join()
        for w in workers:
            w.cancel()
        self.running = False
        self.ui.stop()
        console.log("[bold green]Scan completed![/]")
        db.close()

    async def collect_baselines(self, endpoints):
        """Send clean requests to establish baseline response characteristics."""
        for endpoint, params in list(endpoints.items())[:10]:  # Limit for speed
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=self.anti_block.get_headers(), proxy=self.anti_block.get_proxy()) as resp:
                        text = await resp.text()
                        self.anomaly.record_baseline(endpoint, 'GET', params, resp, text)
            except:
                pass

    async def scanner_worker(self, worker_id):
        while self.running:
            try:
                endpoint, param = await asyncio.wait_for(self.scan_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            # Run all scanners on this endpoint+param
            tasks = []
            # SQLi
            tasks.append(self.run_scanner(scanners.sqli, endpoint, param))
            # XSS
            tasks.append(self.run_scanner(scanners.xss, endpoint, param))
            # SSRF
            tasks.append(self.run_scanner(scanners.ssrf, endpoint, param))
            # IDOR
            tasks.append(self.run_scanner(scanners.idor, endpoint, param))
            # Business logic
            if self.config.get('anomaly', {}).get('enabled'):
                tasks.append(self.run_scanner(scanners.business_logic, endpoint, param, anomaly=self.anomaly))
            # Add more scanners as needed
            results = await asyncio.gather(*tasks)
            for res in results:
                if res:
                    # Verify
                    verified = await self.verifier.verify(res)
                    if verified:
                        res['verified'] = True
                        res['platform'] = self.platform
                        db.save_finding(res)
                        self.notifier.notify_finding(res)
                        self.ui.add_finding(res)
            self.scan_queue.task_done()

    async def run_scanner(self, scanner_func, endpoint, param, **kwargs):
        try:
            result = await scanner_func(endpoint, param, self.anti_block, **kwargs)
            return result
        except Exception as e:
            console.log(f"[red]Scanner error: {e}[/]")
            return None

async def main():
    parser = argparse.ArgumentParser(description="OmniHunter")
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    args = parser.parse_args()
    hunter = OmniHunter(args.config)
    await hunter.run()

if __name__ == "__main__":
    asyncio.run(main())
