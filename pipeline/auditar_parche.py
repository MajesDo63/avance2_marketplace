"""Execute behavior tests; words in comments cannot satisfy this gate."""
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
runner = ('import unittest,sys; '
          'suite=unittest.defaultTestLoader.discover("/qa-tests"); '
          'assert suite.countTestCases() >= 37, "Faltan pruebas de QA"; '
          'result=unittest.TextTestRunner(verbosity=2).run(suite); '
          'sys.exit(0 if result.wasSuccessful() else 1)')
command = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,noexec,nosuid,size=32m',
           '-e', 'PYTHONDONTWRITEBYTECODE=1', '-v', f'{root / "app"}:/home/appuser/app:ro',
           '-v', f'{root / "tests"}:/qa-tests:ro', '--entrypoint', 'python3',
           os.environ.get('QA_TEST_IMAGE', 'avance2_marketplace-api'), '-c', runner]
try:
    sys.exit(subprocess.run(command, check=False, timeout=120).returncode)
except (OSError, subprocess.TimeoutExpired) as error:
    print('BLOQUEADO: no se pudieron ejecutar las pruebas:', type(error).__name__)
    sys.exit(1)
