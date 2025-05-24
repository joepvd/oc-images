import subprocess
import json

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        result.check_returncode()
    return json.loads(result.stdout)
