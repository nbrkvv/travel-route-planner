"""Compatibility entry point using the complete CI inventory."""
from pathlib import Path
import subprocess
import sys
raise SystemExit(subprocess.call([sys.executable,
    str(Path(__file__).with_name('validate_lab5.py')), *sys.argv[1:], '--render']))
