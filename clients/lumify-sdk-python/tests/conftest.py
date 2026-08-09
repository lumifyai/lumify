import os
import sys

# Ensure the package under test is importable when running `pytest` from the
# package root without an editable install.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
