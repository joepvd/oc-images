import asyncio
import json
import subprocess


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        " ".join(cmd), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Process {cmd} failed with error {stderr}")
    return json.loads(stdout)
