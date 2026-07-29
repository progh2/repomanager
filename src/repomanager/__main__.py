"""CLI entry: python -m repomanager"""

from repomanager.app import run


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
