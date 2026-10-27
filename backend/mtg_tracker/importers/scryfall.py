"""Entry point reserved for importing a downloaded Scryfall bulk JSON file."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to a local bulk JSON file")
    parser.parse_args()
    parser.error("Scryfall import is not implemented yet; no data was read or written.")


if __name__ == "__main__":
    main()
