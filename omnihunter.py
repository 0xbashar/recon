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
    def __init__(self, args):
        self.args = args
        
        # Load config file if provided
        if args.config:
            with open(args.config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        
        # Override with command line arguments
        self.target = args.target or self.config.get('target', '')
        if not self.target:
            console.print("[red][-] Error: No target specified. Use --target or config.yaml[/]")
            sys.exit(1)
            
        self.platform = args.platform or self.config.get('platform', 'unknown')
        
        # Build configuration
        self.config.update({
            'target': self.target,
            'platform': self.platform,
            'concurrency': args.threads or self.config.get('concurrency', 10),
            'deep_scan': args.deep or self.config.get('deep_scan', False),
            'all_scanners': args.all_scanners or self.config.get('all_scanners', False),
            'output_file': args.output or self.config.get('output_file', 'omnihunter_output.txt'),
            'proxy': {
                'use_free': not args.no_proxy if args.no_proxy else self.config.get('proxy', {}).get('use_free', True),
                'max_proxies': self.config.get('proxy', {}).get('max_proxies', 50)
            },
            'update_on_start': self.config.get('update_on_start', True),
            'ml_enabled': args.ml_enabled or self.config.get('ml_enabled', True),
            'anomaly': {
                'enabled': args.anomaly_detection or self.config.get('anomaly', {}).get('enabled', True)
            },
            'verbose': args.verbose or self.config.get('verbose', False),
            'debug': args.debug or self.config.get('debug', False)
        })
        
        # Initialize components
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
        self.running = True
        self.results = []

    async def run(self):
        console.print(f"[bold green][+] Starting OmniHunter scan against {self.target}[/]")
        console.print(f"[bold green][+] Platform: {self.platform}[/]")
        
        # 1. Update tools if needed
        if self.config.get('update_on_start', True):
            console.print("[bold yellow][*] Checking for tool updates...[/]")
            await self.update_mgr.check_all()

        # 2. Start real-time console
        self.ui.start()

        # 3. Recon phase
        console.print("[bold cyan][*] Starting reconnaissance...[/]")
        recon = Recon(self.target, self.config)
        subdomains = await recon.get_subdomains()
        console.print(f"[bold green][+] Found {len(subdomains)} subdomains[/]")
        
        live_urls = await recon.get_live_urls(subdomains)
        console.print(f"[bold green][+] Found {len(live_urls)} live URLs[/]")
        
        all_urls = await recon.gather_urls(live_urls)
        all_urls = list(set(all_urls))
        console.print(f"[bold green][+] Total unique URLs: {len(all_urls)}[/]")
        db.save_urls(all_urls)

        # Save URLs to file
        with open('all_urls.txt', 'w') as f:
            for url in all_urls:
                f.write(f"{url}\n")
        console.print("[bold green][+] URLs saved to all_urls.txt[/]")

        # 4. Parameter extraction
        console.print("[bold cyan][*] Extracting parameters...[/]")
        param_extractor = ParamExtractor(all_urls, self.config.get('scope'))
        endpoints = param_extractor.extract()
        console.print(f"[bold green][+] Extracted {len(endpoints)} endpoints with solid parameters[/]")
        db.save_endpoints(endpoints)

        # Save endpoints to file
        with open('endpoints.txt', 'w') as f:
            for endpoint, params in endpoints.items():
                f.write(f"{endpoint} -> {', '.join(params)}\n")
        console.print("[bold green][+] Endpoints saved to endpoints.txt[/]")

        # 5. Baseline collection
        if self.config['anomaly']['enabled']:
            console.print("[bold cyan][*] Collecting baseline responses...[/]")
            await self.collect_baselines(endpoints)

        # 6. Enqueue scan tasks
        total_tasks = 0
        for endpoint, params in endpoints.items():
            for param in params:
                await self.scan_queue.put((endpoint, param))
                total_tasks += 1
        
        console.print(f"[bold green][+] Queued {total_tasks} scan tasks[/]")

        # 7. Start scanner workers
        workers = [asyncio.create_task(self.scanner_worker(i)) for i in range(self.config.get('concurrency', 10))]
        console.print(f"[bold green][+] Started {len(workers)} scanner workers[/]")
        
        # Wait for all tasks to complete
        await self.scan_queue.join()
        
        # Cancel workers
        for w in workers:
            w.cancel()
        
        self.running = False
        self.ui.stop()
        
        # Save results
        self.save_results()
        console.print("[bold green][+] Scan completed![/]")
        console.print(f"[bold green][+] Results saved to {self.config['output_file']}[/]")
        db.close()

    async def collect_baselines(self, endpoints):
        """Send clean requests to establish baseline response characteristics."""
        import aiohttp
        count = 0
        for endpoint, params in list(endpoints.items())[:20]:  # Limit for speed
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        endpoint, 
                        headers=self.anti_block.get_headers(), 
                        proxy=self.anti_block.get_proxy(),
                        timeout=10
                    ) as resp:
                        text = await resp.text()
                        self.anomaly.record_baseline(endpoint, 'GET', params, resp, text)
                        count += 1
            except Exception as e:
                if self.config.get('debug'):
                    console.print(f"[red]Baseline error for {endpoint}: {e}[/]")
            await self.anti_block.delay()
        console.print(f"[green][+] Collected {count} baselines[/]")

    async def scanner_worker(self, worker_id):
        """Worker process that runs scanners on queued items."""
        while self.running:
            try:
                endpoint, param = await asyncio.wait_for(self.scan_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            
            if self.config.get('verbose'):
                console.print(f"[dim][Worker {worker_id}] Testing {endpoint} with param {param}[/]")
            
            # Define which scanners to run
            scanners_to_run = []
            
            # Always run these
            scanners_to_run.extend([('sqli', scanners.sqli), ('xss', scanners.xss)])
            
            # Add more based on config
            if self.config.get('all_scanners', False) or self.config.get('deep_scan', False):
                scanners_to_run.extend([
                    ('ssrf', scanners.ssrf),
                    ('idor', scanners.idor),
                    ('business_logic', scanners.business_logic)
                ])
            
            tasks = []
            for scanner_name, scanner_func in scanners_to_run:
                tasks.append(self.run_scanner(scanner_name, scanner_func, endpoint, param))
            
            results = await asyncio.gather(*tasks)
            
            for result in results:
                if result:
                    # Verify the finding
                    verified = await self.verifier.verify(result)
                    if verified:
                        result['verified'] = True
                        result['platform'] = self.platform
                        db.save_finding(result)
                        self.notifier.notify_finding(result)
                        self.ui.add_finding(result)
                        self.results.append(result)
                        
                        # Save to output file immediately
                        with open(self.config['output_file'], 'a') as f:
                            f.write(f"[{datetime.now()}] {result['type']} - {result['url']}\n")
                        
                        console.print(f"[bold red][!] Verified {result['type']} at {result['url']}[/]")
                        
                        if self.args.pause_on_find:
                            input("[?] Press Enter to continue...")
            
            self.scan_queue.task_done()
            self.ui.update_stats(scanned=self.ui.stats.get('scanned', 0) + 1)

    async def run_scanner(self, scanner_name, scanner_func, endpoint, param, **kwargs):
        """Run a single scanner and return result."""
        try:
            result = await scanner_func(endpoint, param, self.anti_block, **kwargs)
            if result and self.config.get('debug'):
                console.print(f"[dim][Debug] {scanner_name} found: {result}[/]")
            return result
        except Exception as e:
            if self.config.get('debug'):
                console.print(f"[red][Debug] Scanner {scanner_name} error: {e}[/]")
            return None

    def save_results(self):
        """Save all results to various formats."""
        # Text output
        with open(self.config['output_file'], 'w') as f:
            f.write(f"OmniHunter Scan Results for {self.target}\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Platform: {self.platform}\n")
            f.write("=" * 50 + "\n\n")
            
            for result in self.results:
                f.write(f"Type: {result['type']}\n")
                f.write(f"URL: {result['url']}\n")
                f.write(f"Confidence: {result.get('confidence', 'N/A')}%\n")
                f.write(f"Verified: {result.get('verified', False)}\n")
                f.write("-" * 30 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="OmniHunter - Ultimate Automated Bug Bounty Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 omnihunter.py --target example.com
  python3 omnihunter.py --target example.com --platform hackerone --all-scanners
  python3 omnihunter.py --config config.yaml --target example.com --threads 20
  python3 omnihunter.py --target example.com --deep --output results.txt
        """
    )
    
    # Main arguments
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--target', help='Target domain to scan (e.g., example.com)')
    parser.add_argument('--platform', default='unknown', help='Bug bounty platform (hackerone, bugcrowd, etc.)')
    
    # Scan options
    parser.add_argument('--all-scanners', action='store_true', help='Enable all vulnerability scanners')
    parser.add_argument('--deep', action='store_true', help='Deep scan mode (more thorough)')
    parser.add_argument('--threads', type=int, help='Number of concurrent threads (default: 10)')
    parser.add_argument('--no-proxy', action='store_true', help='Disable proxy rotation')
    
    # Feature toggles
    parser.add_argument('--ml-enabled', action='store_true', help='Enable ML heuristics')
    parser.add_argument('--anomaly-detection', action='store_true', help='Enable anomaly detection for business logic')
    
    # Output options
    parser.add_argument('--output', '-o', default='omnihunter_results.txt', help='Output file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    # Interactive options
    parser.add_argument('--pause-on-find', action='store_true', help='Pause when a finding is discovered')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.target and not args.config:
        parser.print_help()
        console.print("\n[red][-] Error: Either --target or --config must be provided[/]")
        sys.exit(1)
    
    # Run the scanner
    hunter = OmniHunter(args)
    try:
        asyncio.run(hunter.run())
    except KeyboardInterrupt:
        console.print("\n[yellow][!] Scan interrupted by user[/]")
        hunter.running = False
        hunter.save_results()
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red][!] Fatal error: {e}[/]")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
