import subprocess
import requests
import asyncio
import os
from rich.console import Console

console = Console()

class UpdateManager:
    def __init__(self, tools_path):
        self.tools_path = tools_path
        self.tools = {
            "subfinder": {"cmd": "subfinder -version", "repo": "projectdiscovery/subfinder", "install": "go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"},
            "assetfinder": {"cmd": "assetfinder -version", "repo": "tomnomnom/assetfinder", "install": "go install -v github.com/tomnomnom/assetfinder@latest"},
            "amass": {"cmd": "amass -version", "repo": "OWASP/Amass", "install": "go install -v github.com/OWASP/Amass/v3/...@master"},
            "httpx": {"cmd": "httpx -version", "repo": "projectdiscovery/httpx", "install": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest"},
            "gau": {"cmd": "gau --version", "repo": "lc/gau", "install": "go install -v github.com/lc/gau/v2/cmd/gau@latest"},
            "waybackurls": {"cmd": "waybackurls -h", "repo": "tomnomnom/waybackurls", "install": "go install -v github.com/tomnomnom/waybackurls@latest"},
            "hakrawler": {"cmd": "hakrawler -version", "repo": "hakluke/hakrawler", "install": "go install -v github.com/hakluke/hakrawler@latest"},
            "gospider": {"cmd": "gospider --version", "repo": "jaeles-project/gospider", "install": "go install -v github.com/jaeles-project/gospider@latest"},
            "kxss": {"cmd": "kxss -h", "repo": "tomnomnom/hacks/kxss", "install": "go install -v github.com/tomnomnom/hacks/kxss@latest"},
            "Gxss": {"cmd": "Gxss -h", "repo": "KathanP19/Gxss", "install": "go install -v github.com/KathanP19/Gxss@latest"},
            "dalfox": {"cmd": "dalfox version", "repo": "hahwul/dalfox", "install": "go install -v github.com/hahwul/dalfox/v2@latest"},
            "xsstrike": {"cmd": "python3 xsstrike.py --help", "repo": "s0md3v/XSStrike", "install": "git clone https://github.com/s0md3v/XSStrike.git"},
            "sqlmap": {"cmd": "sqlmap --version", "repo": "sqlmapproject/sqlmap", "install": "git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev"},
            "nuclei": {"cmd": "nuclei -version", "repo": "projectdiscovery/nuclei", "install": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"},
            "ffuf": {"cmd": "ffuf -V", "repo": "ffuf/ffuf", "install": "go install -v github.com/ffuf/ffuf@latest"},
            "qsreplace": {"cmd": "qsreplace -h", "repo": "tomnomnom/qsreplace", "install": "go install -v github.com/tomnomnom/qsreplace@latest"},
            "interactsh-client": {"cmd": "interactsh-client -version", "repo": "projectdiscovery/interactsh", "install": "go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest"},
        }

    async def check_all(self):
        for name, info in self.tools.items():
            if not self._check_tool(name):
                console.log(f"[yellow]Updating {name}...[/]")
                await self._update_tool(name)

    def _check_tool(self, name):
        try:
            cmd = self.tools[name]["cmd"]
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except:
            return False

    async def _update_tool(self, name):
        info = self.tools[name]
        install_cmd = info["install"]
        proc = await asyncio.create_subprocess_shell(install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await proc.communicate()
        if proc.returncode == 0:
            console.log(f"[green]{name} updated successfully[/]")
        else:
            console.log(f"[red]Failed to update {name}[/]")
