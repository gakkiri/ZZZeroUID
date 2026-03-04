import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterable, Set

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCAL_REPO = Path(__file__).resolve().parents[3] / "ZZZ-Plugin"
DEFAULT_DEST = ROOT / "utils" / "zzz_plugin_resources"
DEFAULT_GITHUB_ZIP = "https://github.com/ZZZure/ZZZ-Plugin/archive/refs/heads/main.zip"


def _file_count(path: Path) -> int:
    return sum(1 for p in path.rglob("*") if p.is_file())


def _list_relative_files(path: Path) -> Set[str]:
    files: Iterable[Path] = (p for p in path.rglob("*") if p.is_file())
    return {str(p.relative_to(path).as_posix()) for p in files}


def _replace_dir(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _sync_from_local(local_repo: Path, dst: Path) -> None:
    src = local_repo / "resources"
    if not src.exists():
        raise FileNotFoundError(f"未找到本地资源目录: {src}")

    _replace_dir(src, dst)

    src_files = _list_relative_files(src)
    dst_files = _list_relative_files(dst)
    if src_files != dst_files:
        missing = sorted(src_files - dst_files)
        extra = sorted(dst_files - src_files)
        raise RuntimeError(
            "本地同步校验失败: "
            f"missing={len(missing)}, extra={len(extra)}"
        )

    print(f"[完成] 来源: 本地仓库 {local_repo}")
    print(f"[完成] 文件数: {len(dst_files)}")
    print(f"[完成] 目标目录: {dst}")


def _sync_from_github(zip_url: str, dst: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="zzz_plugin_res_") as td:
        tmp_dir = Path(td)
        zip_path = tmp_dir / "zzz_plugin.zip"
        print(f"[下载] {zip_url}")
        urllib.request.urlretrieve(zip_url, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)

        candidates = list(tmp_dir.glob("ZZZ-Plugin-*/resources"))
        if not candidates:
            raise FileNotFoundError("压缩包中未找到 resources 目录")

        src = candidates[0]
        _replace_dir(src, dst)

    print("[完成] 来源: GitHub 压缩包")
    print(f"[完成] 文件数: {_file_count(dst)}")
    print(f"[完成] 目标目录: {dst}")


def main() -> None:
    parser = argparse.ArgumentParser(description="同步 ZZZ-Plugin 的 resources 到 ZZZeroUID")
    parser.add_argument(
        "--source",
        choices=("auto", "local", "github"),
        default="auto",
        help="资源来源: auto(优先本地), local, github",
    )
    parser.add_argument(
        "--local-repo",
        type=Path,
        default=DEFAULT_LOCAL_REPO,
        help="本地 ZZZ-Plugin 仓库路径",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help="同步目标目录",
    )
    parser.add_argument(
        "--github-zip-url",
        default=DEFAULT_GITHUB_ZIP,
        help="GitHub zip 下载地址",
    )
    args = parser.parse_args()

    dest = args.dest.resolve()

    local_ok = (args.local_repo / "resources").exists()
    if args.source == "local":
        _sync_from_local(args.local_repo.resolve(), dest)
        return

    if args.source == "auto" and local_ok:
        _sync_from_local(args.local_repo.resolve(), dest)
        return

    _sync_from_github(args.github_zip_url, dest)


if __name__ == "__main__":
    main()
