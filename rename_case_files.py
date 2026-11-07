"""
Rename medical examiner case files with their case number, case year, and the month they were received.

The first page of each PDF contains a case identifier in the form "ME#<number>". Each file is
renamed in place to:

    <ME number>_<case year>_<month received>.pdf

By default the script only previews the renames. Pass --apply to rename the files.

Created by: Myrela Bauman (May 2022, as a notebook)
"""

import argparse
import logging
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pypdf import PdfReader

# the case number is read from the start of the first page only, where the case header sits
HEADER_CHARS = 100
ME_PATTERN = re.compile(r"ME#(\S+)")
YEAR_PATTERN = re.compile(r"\d{4}")
MONTH_PATTERN = re.compile(r"[A-Za-z]+\d{4}")  # e.g. May2022

log = logging.getLogger("rename_case_files")


@dataclass
class Rename:
    source: Path
    target: Optional[Path] = None
    problem: Optional[str] = None


def parse_filename(name: str) -> tuple:
    """Return (case year, month received) from a split-abstraction filename.

    The case year is the third underscore-separated part of the name and the month received is the
    second-to-last, e.g. 'abstraction_split_2022_case07_May2022_001.pdf' -> ('2022', 'May2022').
    """
    parts = Path(name).stem.split("_")
    if len(parts) < 3:
        raise ValueError(f"expected at least 3 underscore-separated parts in the name, found {len(parts)}")
    year, month = parts[2], parts[-2]
    if not YEAR_PATTERN.fullmatch(year):
        raise ValueError(f"case year '{year}' isn't a 4-digit year")
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError(f"month received '{month}' doesn't look like 'May2022'")
    return year, month


def find_case_number(text: str) -> str:
    """Return the single ME case number in the text, or raise if there is none or more than one."""
    numbers = set(ME_PATTERN.findall(text))
    if not numbers:
        raise ValueError("no ME# case number at the start of the first page")
    if len(numbers) > 1:
        raise ValueError(f"more than one ME# case number at the start of the first page: {sorted(numbers)}")
    return numbers.pop()


def read_first_page(path: Path) -> str:
    return PdfReader(path).pages[0].extract_text() or ""


def plan_renames(folder: Path, read_text: Callable[[Path], str] = read_first_page) -> list:
    """Work out the new name for every PDF in the folder, flagging any file that can't be renamed safely.

    Each file is matched with its own case number, so a problem with one file never shifts the
    names of the others.
    """
    plans = []
    pdfs = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    for pdf in pdfs:
        try:
            year, month = parse_filename(pdf.name)
        except ValueError as e:
            plans.append(Rename(pdf, problem=str(e)))
            continue
        try:
            text = read_text(pdf)
        except Exception as e:  # pypdf raises several error types for damaged or encrypted files
            plans.append(Rename(pdf, problem=f"couldn't read the PDF ({e})"))
            continue
        try:
            case_number = find_case_number(text[:HEADER_CHARS])
        except ValueError as e:
            plans.append(Rename(pdf, problem=str(e)))
            continue
        plans.append(Rename(pdf, target=folder / f"{case_number}_{year}_{month}.pdf"))

    # never let two files claim the same name, and never overwrite a file that's already there
    target_counts = Counter(p.target for p in plans if p.target)
    for p in plans:
        if p.problem:
            continue
        if target_counts[p.target] > 1:
            p.problem = f"another file would also be renamed to {p.target.name}"
        elif p.target.exists() and p.target != p.source:
            p.problem = f"{p.target.name} already exists"

    return plans


def apply_renames(plans: list) -> int:
    renamed = 0
    for p in plans:
        if p.problem is None and p.target != p.source:
            p.source.rename(p.target)
            renamed += 1
    return renamed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Rename medical examiner case PDFs to <ME number>_<case year>_<month received>.pdf"
    )
    parser.add_argument("folder", type=Path, help="folder containing the PDF files")
    parser.add_argument("--apply", action="store_true", help="rename the files (without it, only a preview is shown)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not args.folder.is_dir():
        parser.error(f"{args.folder} is not a folder")

    plans = plan_renames(args.folder)
    ready = [p for p in plans if p.problem is None]
    skipped = [p for p in plans if p.problem]

    for p in ready:
        log.info("%s  ->  %s", p.source.name, p.target.name)
    for p in skipped:
        log.warning("SKIPPED %s: %s", p.source.name, p.problem)

    if args.apply:
        renamed = apply_renames(plans)
        log.info("\nRenamed %d file(s); skipped %d.", renamed, len(skipped))
    else:
        log.info("\nPreview only: %d file(s) would be renamed; %d skipped. Run again with --apply to rename.",
                 len(ready), len(skipped))

    # a non-zero exit code lets a scheduler or script notice that some files need attention
    return 1 if skipped else 0


if __name__ == "__main__":
    sys.exit(main())
