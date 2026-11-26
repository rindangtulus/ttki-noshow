from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r"[A-Za-z0-9_.<>/-]+")
PARENTHETICAL = re.compile(r"\([^)]*\)")
MODULES = {
    "__init__",
    "config",
    "data",
    "features",
    "splits",
    "models",
    "metrics",
    "run_experiments",
    "make_figures",
}


def structure_lines() -> list[str]:
    lines = ROOT.joinpath("README.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "## Struktur")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    return [
        line.strip()
        for line in lines[start + 1 : end]
        if line.strip() and not line.strip().startswith("```")
    ]


def tracked_files() -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [Path(name) for name in output.splitlines() if name]


def clean_tokens(line: str) -> list[str]:
    before_comment = line.split("#", 1)[0]
    without_parentheses = PARENTHETICAL.sub(" ", before_comment)
    before_note = without_parentheses.split("=", 1)[0]
    return [token.strip("` ,;") for token in TOKEN.findall(before_note)]


def is_candidate(token: str) -> bool:
    return (
        "/" in token
        or "." in token
        or "_" in token
        or token == "LICENSE"
        or token in MODULES
    )


def target_name(token: str, base: Path) -> str:
    if token in MODULES or (base.name == "figures" and token.startswith("fig_")):
        return token + (".png" if base.name == "figures" else ".py")
    return token


def structure_paths() -> set[Path]:
    paths: set[Path] = set()
    directory: list[Path] = []
    for line in structure_lines():
        lowered = line.lower()
        if "belum ada" in lowered or "kosong" in lowered:
            continue
        tokens = clean_tokens(line)
        line_directories: list[Path] = []
        for token in tokens:
            if token.endswith("/"):
                if "<fs>" in token:
                    line_directories.extend([Path("results/full"), Path("results/no_proxy")])
                else:
                    line_directories.append(Path(token.rstrip("/")))
        if line_directories:
            directory = line_directories
        for path in directory:
            paths.add(path)
        for token in tokens:
            if not is_candidate(token) or token.endswith("/"):
                continue
            if "/" in token:
                paths.add(Path(token))
                continue
            for base in directory or [Path(".")]:
                paths.add(base / target_name(token, base))
    return paths


def under_allowed_root(path: Path, roots: tuple[Path, ...]) -> bool:
    try:
        return any(path.is_relative_to(root) for root in roots)
    except ValueError:
        return False


def test_gitignore_memuat_pengecualian_wajib() -> None:
    entries = {
        line.strip()
        for line in ROOT.joinpath(".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert {"data/raw/", "kaggle.json", ".env"}.issubset(entries)


def test_tidak_ada_csv_di_luar_results_dan_references() -> None:
    allowed = (ROOT / "results", ROOT / "references")
    skipped = {".git", ".venv", ".pytest_cache", "__pycache__"}
    for path in ROOT.rglob("*.csv"):
        parts = path.relative_to(ROOT).parts
        if any(part in skipped for part in parts[:-1]):
            continue
        if len(parts) > 2 and parts[0] == "data" and parts[1] == "raw":
            continue
        assert under_allowed_root(path, allowed), f"CSV di luar results/ dan references/: {path}"


def test_tidak_ada_kaggle_json_yang_dilacak_git() -> None:
    tracked = tracked_files()
    assert not [path for path in tracked if path.name == "kaggle.json"]
    assert not [
        path
        for path in tracked
        if path.suffix == ".csv" and not under_allowed_root(path, (Path("results"), Path("references")))
    ]


def test_berkas_pada_bagian_struktur_readme_ada() -> None:
    missing = sorted(str(ROOT / path) for path in structure_paths() if not (ROOT / path).exists())
    assert not missing, f"Berkas pada bagian Struktur README tidak ada: {missing}"


def test_naskah_di_folder_paper_ada() -> None:
    paper = ROOT / "paper"
    assert list(paper.glob("*.docx")) or list(paper.glob("*.pdf"))


def test_notebooks_di_readme_memang_ditandai_kosong() -> None:
    block = "\n".join(structure_lines())
    assert "notebooks/" in block
    assert "kosong" in block
