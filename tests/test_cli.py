from __future__ import annotations

from ai_newspaper.entrypoints.cli import build_parser, main


def test_parser_includes_expected_commands() -> None:
    parser = build_parser()

    for command in ("run", "fetch", "analyze", "render", "prune"):
        args = parser.parse_args([command])
        assert args.command == command


def test_help_exits_successfully(capsys: object) -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
