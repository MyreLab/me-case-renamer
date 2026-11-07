"""
Create a folder of fake case PDFs for trying out rename_case_files.py.

The files contain no real data. Four are valid, and the rest are broken in ways the tool should catch.
"""

import sys
from pathlib import Path

from reportlab.pdfgen import canvas

SAMPLES = {
    "abstraction_split_2022_case01_May2022_001.pdf": "Case header ME#22-01234 Received",
    "abstraction_split_2022_case02_May2022_002.pdf": "Case header ME#22-01290 Received",
    "abstraction_split_2022_case03_May2022_003.pdf": "Case header ME#22-01295 Received",
    "abstraction_split_2022_case04_May2022_004.pdf": "Case header ME#22-01301 Received",
    "abstraction_split_2022_case05_May2022_005.pdf": "Case header ME#22-01388 and ME#22-01389",
    "abstraction_split_2022_case06_May2022_006.pdf": "Case header, case number missing",
}


def make_pdf(path: Path, first_line: str) -> None:
    c = canvas.Canvas(str(path))
    c.drawString(72, 750, first_line)
    c.drawString(72, 700, "Sample file for testing. Contains no real data.")
    c.save()


def main(folder: str = "sample_case_files") -> None:
    out = Path(folder)
    out.mkdir(exist_ok=True)
    for name, first_line in SAMPLES.items():
        make_pdf(out / name, first_line)
    (out / "notes.txt").write_text("Not a PDF, so the tool should ignore it.\n")
    print(f"Created {len(SAMPLES)} sample PDFs and one text file in {out}/")


if __name__ == "__main__":
    main(*sys.argv[1:])
