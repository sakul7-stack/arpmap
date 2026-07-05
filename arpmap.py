"""Backward-compatibility shim.

The ARPMap code now lives in the ``arpmap/`` package. This file only exists so the
old entry point ``python arpmap.py`` keeps working; prefer ``python -m arpmap`` or
the installed ``arpmap`` command. Safe to delete with ``git rm arpmap.py``.
"""

from arpmap.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
