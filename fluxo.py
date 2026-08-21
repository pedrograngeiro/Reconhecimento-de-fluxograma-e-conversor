"""Atalho compatível para a nova interface do conversor.

Use ``python fluxo.py --help``. O comando recomendado após a instalação é
``flowchart-converter``.
"""

from flowchart_converter.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
