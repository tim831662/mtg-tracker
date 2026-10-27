"""Entry point reserved for importing a local MTG_decklistcache checkout."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to a local tournament data directory")
    parser.parse_args()
    parser.error("Tournament import is not implemented yet; no data was read or written.")


if __name__ == "__main__":
    main()
