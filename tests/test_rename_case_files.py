import sys
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rename_case_files import find_case_number, main, parse_filename, plan_renames  # noqa: E402


def make_pdf(path: Path, first_line: str) -> Path:
    """Write a one-page PDF whose first line of text is first_line."""
    c = canvas.Canvas(str(path))
    c.drawString(72, 750, first_line)
    c.drawString(72, 700, "Decedent information follows.")
    c.save()
    return path


def fake_reader(texts):
    """Stand-in for PDF reading in unit tests: returns the text given for each file name."""
    return lambda path: texts[path.name]


# --- filename parsing ---

def test_parse_filename_reads_year_and_month():
    assert parse_filename("abstraction_split_2022_case07_May2022_001.pdf") == ("2022", "May2022")


def test_parse_filename_rejects_short_names():
    with pytest.raises(ValueError, match="at least 3"):
        parse_filename("scan_001.pdf")


def test_parse_filename_rejects_bad_year():
    with pytest.raises(ValueError, match="4-digit year"):
        parse_filename("abstraction_split_22_case07_May2022_001.pdf")


# --- case number extraction ---

def test_find_case_number():
    assert find_case_number("OCME Case Header ME#22-01234 Received") == "22-01234"


def test_find_case_number_allows_repeats_of_the_same_number():
    assert find_case_number("ME#22-01234 ... ME#22-01234") == "22-01234"


def test_find_case_number_missing():
    with pytest.raises(ValueError, match="no ME#"):
        find_case_number("Case header with no identifier")


def test_find_case_number_conflicting():
    with pytest.raises(ValueError, match="more than one"):
        find_case_number("ME#22-01234 and ME#22-09999")


# --- planning renames ---

def test_one_bad_file_does_not_shift_the_others(tmp_path):
    # the original notebook paired files and case numbers by position, so a file with no case
    # number next to a file with two could silently give every later file the wrong name
    names = {
        "abs_split_2022_a_May2022_1.pdf": "ME#111",
        "abs_split_2022_b_May2022_2.pdf": "no number here",
        "abs_split_2022_c_May2022_3.pdf": "ME#333",
    }
    for name in names:
        (tmp_path / name).touch()

    plans = {p.source.name: p for p in plan_renames(tmp_path, read_text=fake_reader(names))}

    assert plans["abs_split_2022_a_May2022_1.pdf"].target.name == "111_2022_May2022.pdf"
    assert plans["abs_split_2022_b_May2022_2.pdf"].problem.startswith("no ME#")
    assert plans["abs_split_2022_c_May2022_3.pdf"].target.name == "333_2022_May2022.pdf"


def test_duplicate_targets_are_both_skipped(tmp_path):
    names = {
        "abs_split_2022_a_May2022_1.pdf": "ME#111",
        "abs_split_2022_b_May2022_2.pdf": "ME#111",
    }
    for name in names:
        (tmp_path / name).touch()

    plans = plan_renames(tmp_path, read_text=fake_reader(names))

    assert all("another file" in p.problem for p in plans)


def test_existing_file_is_not_overwritten(tmp_path):
    (tmp_path / "abs_split_2022_a_May2022_1.pdf").touch()
    (tmp_path / "111_2022_May2022.pdf").touch()

    plans = plan_renames(tmp_path, read_text=lambda path: "ME#111" if path.name.startswith("abs") else "")
    plan = next(p for p in plans if p.source.name.startswith("abs"))

    assert "already exists" in plan.problem


def test_non_pdf_files_are_ignored(tmp_path):
    (tmp_path / "notes.txt").touch()
    (tmp_path / ".DS_Store").touch()

    assert plan_renames(tmp_path, read_text=lambda path: "") == []


# --- end to end, with real PDFs ---

def test_preview_does_not_rename(tmp_path):
    make_pdf(tmp_path / "abs_split_2022_a_May2022_1.pdf", "Case ME#22-01234")

    exit_code = main([str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "abs_split_2022_a_May2022_1.pdf").exists()
    assert not (tmp_path / "22-01234_2022_May2022.pdf").exists()


def test_apply_renames_good_files_and_reports_bad_ones(tmp_path):
    make_pdf(tmp_path / "abs_split_2022_a_May2022_1.pdf", "Case ME#22-01234")
    make_pdf(tmp_path / "abs_split_2022_b_May2022_2.pdf", "Case header missing its number")
    (tmp_path / "abs_split_2022_c_May2022_3.pdf").write_bytes(b"not really a pdf")

    exit_code = main([str(tmp_path), "--apply"])

    assert exit_code == 1  # some files were skipped
    assert (tmp_path / "22-01234_2022_May2022.pdf").exists()
    assert (tmp_path / "abs_split_2022_b_May2022_2.pdf").exists()
    assert (tmp_path / "abs_split_2022_c_May2022_3.pdf").exists()
