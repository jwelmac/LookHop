"""Entry point for `python -m lookhop` and for the packaged executable."""
import sys

from lookhop.app import main

if __name__ == "__main__":
    sys.exit(main())
