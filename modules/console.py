from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
import threading
import time

console = Console()

class OmniHunterUI:
    def __init__(self):
        self.stats = {'recon': 0, 'params': 0, 'scanned': 0, 'findings': 0}
        self.findings = []
        self.live = None
        self.running = False
        self.layout = Layout()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_ui)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.live:
            self.live.stop()

    def _run_ui(self):
        with Live(self._generate_layout(), refresh_per_second=4, screen=True) as live:
            self.live = live
            while self.running:
                live.update(self._generate_layout())
                time.sleep(0.25)

    def _generate_layout(self):
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        layout["header"].update(Panel(Text("OmniHunter - Ultimate Bug Bounty Tool", style="bold cyan"), style="white"))
        # Body split into two columns
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        # Left column: stats
        stats_table = Table(title="Statistics", show_header=False)
        stats_table.add_column("Metric")
        stats_table.add_column("Value")
        stats_table.add_row("URLs processed", str(self.stats['recon']))
        stats_table.add_row("Endpoints", str(self.stats['params']))
        stats_table.add_row("Scans performed", str(self.stats['scanned']))
        stats_table.add_row("Findings", str(self.stats['findings']))
        layout["left"].update(Panel(stats_table, title="Stats"))
        # Right column: latest findings
        findings_table = Table(title="Latest Findings")
        findings_table.add_column("Type")
        findings_table.add_column("URL")
        findings_table.add_column("Confidence")
        for f in self.findings[-5:]:
            findings_table.add_row(f['type'], f['url'][:50], str(f.get('confidence', '')))
        layout["right"].update(Panel(findings_table, title="Findings"))
        # Footer: status
        layout["footer"].update(Panel("Running...", style="green"))
        return layout

    def update_stats(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.stats:
                self.stats[k] = v

    def add_finding(self, finding):
        self.findings.append(finding)
        self.stats['findings'] += 1
