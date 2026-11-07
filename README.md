# Python File Reader

*Background*: My team and I are responsible for the data analysis and management of hundreds of mortality data files received from the Chief Medical Examiner's Office on a monthly basis. A solution was needed to continually rename incoming files with required information, including a case identifier number unique to each mortality case. Automating it cut the monthly renaming from about 4 hours to 5 minutes.

*Solution*: `rename_case_files.py` reads the unique case identifier (`ME#...`) from the first page of each PDF with `pypdf`, takes the case year and month received from the original file name, and renames every file to `<ME number>_<case year>_<month received>.pdf`.

It started as a notebook (`MBrenaming.ipynb`, kept here for reference) and was later rebuilt as a command-line tool with safety checks:
- Previews every rename by default, and only renames files when run with `--apply`
- Pairs each file with its own case number, so one problem file can't shift the names of the others
- Skips and reports any file it can't rename safely: no case number, conflicting case numbers, an unreadable PDF, an unexpected file name, two files that would get the same name, or a name that already exists
- Ignores anything in the folder that isn't a PDF
- Exits with a non-zero code when files are skipped, so a scheduled job can flag them

Run it:
```bash
pip install -r requirements.txt

# preview the renames
python rename_case_files.py path/to/case_files

# rename the files
python rename_case_files.py path/to/case_files --apply
```

Example preview:
```
abstraction_split_2022_case01_May2022_001.pdf  ->  22-01234_2022_May2022.pdf
abstraction_split_2022_case02_May2022_002.pdf  ->  22-01290_2022_May2022.pdf
SKIPPED abstraction_split_2022_case03_May2022_003.pdf: no ME# case number at the start of the first page

Preview only: 2 file(s) would be renamed; 1 skipped. Run again with --apply to rename.
```

Tests:
```bash
pip install -r requirements-dev.txt
pytest
```
The tests build sample PDFs on the fly, so no real case files are needed. They also run automatically on every push.
