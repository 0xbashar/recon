import asyncio
import subprocess
import tempfile
import os

async def scan(endpoint, param, anti_block, **kwargs):
    """Use dalfox for comprehensive XSS scanning."""
    # Create a temporary file with the target URL
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(f"{endpoint}?{param}=FUZZ")
        tmpfile = f.name
    try:
        # Run dalfox
        cmd = f"dalfox file {tmpfile} --silence --only-poc"
        proc = await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        stdout, _ = await proc.communicate()
        output = stdout.decode()
        if "[POC]" in output or "[V]" in output:
            # Extract the vulnerable URL
            lines = output.splitlines()
            for line in lines:
                if "[POC]" in line or "[V]" in line:
                    parts = line.split()
                    for part in parts:
                        if part.startswith("http"):
                            return {'url': part, 'param': param, 'type': 'XSS', 'confidence': 90}
    finally:
        os.unlink(tmpfile)
    return None
