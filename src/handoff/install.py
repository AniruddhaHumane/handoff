import argparse
import shutil
from contextlib import ExitStack
from importlib.resources import as_file, files
from pathlib import Path


SKILL_NAMES = ("handoff", "get-handoff")


def install_skills(
    *,
    runtime: str,
    home: Path | None = None,
    source_root: Path | None = None,
    mode: str = "auto",
) -> list[Path]:
    target_root = _target_root(runtime, home or Path.home())
    source_root = source_root or _detect_local_source()

    if source_root is not None:
        return _install_from_filesystem(
            source_root=source_root,
            target_root=target_root,
            mode="symlink" if mode == "auto" else mode,
        )

    if mode == "symlink":
        raise ValueError("Packaged skill assets cannot be installed with --mode symlink")
    return _install_from_package(target_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="handoff-install",
        description="Install portable-handoff skills into Codex or Claude.",
    )
    parser.add_argument("runtime", choices=("codex", "claude"))
    parser.add_argument("--home", type=Path, help="Override home directory for testing.")
    parser.add_argument(
        "--source",
        type=Path,
        help="Local skills directory containing handoff/ and get-handoff/.",
    )
    parser.add_argument(
        "--mode",
        choices=("auto", "copy", "symlink"),
        default="auto",
        help="Install mode. auto symlinks local sources and copies packaged assets.",
    )
    args = parser.parse_args(argv)

    installed = install_skills(
        runtime=args.runtime,
        home=args.home,
        source_root=args.source,
        mode=args.mode,
    )
    for path in installed:
        print(path)
    return 0


def _target_root(runtime: str, home: Path) -> Path:
    if runtime == "codex":
        return home / ".codex" / "skills"
    if runtime == "claude":
        return home / ".claude" / "skills"
    raise ValueError(f"Unsupported runtime: {runtime}")


def _detect_local_source() -> Path | None:
    candidate = Path.cwd() / "skills"
    if _valid_source(candidate):
        return candidate
    return None


def _valid_source(source_root: Path) -> bool:
    return all((source_root / name / "SKILL.md").exists() for name in SKILL_NAMES)


def _install_from_filesystem(
    *,
    source_root: Path,
    target_root: Path,
    mode: str,
) -> list[Path]:
    if not _valid_source(source_root):
        raise FileNotFoundError(
            f"{source_root} must contain handoff/SKILL.md and get-handoff/SKILL.md"
        )
    target_root.mkdir(parents=True, exist_ok=True)

    installed = []
    for name in SKILL_NAMES:
        source = source_root / name
        target = target_root / name
        _replace_target(target)
        if mode == "symlink":
            target.symlink_to(source.resolve(), target_is_directory=True)
        elif mode == "copy":
            shutil.copytree(source, target)
        else:
            raise ValueError(f"Unsupported install mode: {mode}")
        installed.append(target)
    return installed


def _install_from_package(target_root: Path) -> list[Path]:
    target_root.mkdir(parents=True, exist_ok=True)
    installed = []
    with ExitStack() as stack:
        for name in SKILL_NAMES:
            resource = files("handoff").joinpath("assets", name)
            source = stack.enter_context(as_file(resource))
            target = target_root / name
            _replace_target(target)
            shutil.copytree(source, target)
            installed.append(target)
    return installed


def _replace_target(target: Path) -> None:
    if target.is_symlink() or target.is_file():
        target.unlink()
        return
    if target.exists():
        shutil.rmtree(target)


if __name__ == "__main__":
    raise SystemExit(main())
