import argparse
from pathlib import Path

from handoff.checkpoint import run_checkpoint, run_resume


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handoff")
    subparsers = parser.add_subparsers(dest="command", required=True)

    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--root", type=Path, default=Path.cwd())

    resume = subparsers.add_parser("resume")
    resume.add_argument("--root", type=Path, default=Path.cwd())

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "checkpoint":
        run_checkpoint(args.root)
        print(args.root / ".handoff" / "restore.md")
        return 0
    if args.command == "resume":
        print(run_resume(args.root))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
