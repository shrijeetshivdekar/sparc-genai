"""Shim so `python -m pricing.params <cmd>` works (delegates to params_cli)."""
from .params_cli import main

if __name__ == "__main__":
    main()
