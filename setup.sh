#!/bin/bash
# setup.sh – install OmniHunter dependencies

echo "[*] Installing Python dependencies..."
pip install -r requirements.txt

echo "[*] Installing Go tools..."
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/OWASP/Amass/v3/...@master
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
go install -v github.com/tomnomnom/waybackurls@latest
go install -v github.com/hakluke/hakrawler@latest
go install -v github.com/jaeles-project/gospider@latest
go install -v github.com/tomnomnom/hacks/kxss@latest
go install -v github.com/KathanP19/Gxss@latest
go install -v github.com/hahwul/dalfox/v2@latest
go install -v github.com/tomnomnom/qsreplace@latest
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
go install -v github.com/ffuf/ffuf@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

echo "[*] Done! Make sure your PATH includes ~/go/bin"
