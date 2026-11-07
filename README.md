# Python File Reader

*Background*: My team and I are responsible for the data analysis and management of hundreds of mortality data files received from the Chief Medical Examiner's Office on a monthly basis. A solution was needed to continually rename incoming files with required information, including a case identifier number unique to each mortality case. Automating it cut the monthly renaming from about 4 hours to 5 minutes.

*Solution*: `rename_case_files.py` reads the unique case identifier (`ME#...`) from the first page of each PDF with `pypdf`, takes the case year and month received from the original file name, and renames every file to `<ME number>_<case year>_<month received>.pdf`.

It started as a personal notebook (`MBrenaming.ipynb`, kept here for reference). I later rebuilt it as a command-line tool with safety checks:
- Previews every rename by default, and only renames files when run with `--apply`
- Pairs each file with its own case number, so one problem file can't shift the names of the others
- Skips and reports any file it can't rename safely: no case number, conflicting case numbers, an unreadable PDF, an unexpected file name, two files that would get the same name, or a name that already exists
- Ignores anything in the folder that isn't a PDF, and leaves already-renamed files alone, so it's safe to re-run on the same folder
- Exits with a non-zero code when files are skipped, so a scheduled job can flag them
- Covered by 15 automated `pytest` tests, which run on every push with GitHub Actions

Run it:
```bash
pip install -r requirements.txt

# preview the renames
python rename_case_files.py path/to/case_files

# rename the files
python rename_case_files.py path/to/case_files --apply
```

Try it on sample files:
```bash
# install the extra packages for sample files and tests
pip install -r requirements-dev.txt

# 1. create a folder of 6 fake case PDFs (no real data): 4 valid, 1 with two
#    conflicting case numbers, 1 with no case number, plus a text file to ignore
python make_sample_files.py

# 2. preview what would happen; nothing is renamed yet
python rename_case_files.py sample_case_files

# 3. rename the valid files
python rename_case_files.py sample_case_files --apply

# 4. run it again: the renamed files are left alone, and only the 2 problem files are reported
python rename_case_files.py sample_case_files
```

The preview in step 2 looks like this:
```
abstraction_split_2022_case01_May2022_001.pdf  ->  22-01234_2022_May2022.pdf
abstraction_split_2022_case02_May2022_002.pdf  ->  22-01290_2022_May2022.pdf
abstraction_split_2022_case03_May2022_003.pdf  ->  22-01295_2022_May2022.pdf
abstraction_split_2022_case04_May2022_004.pdf  ->  22-01301_2022_May2022.pdf
SKIPPED abstraction_split_2022_case05_May2022_005.pdf: more than one ME# case number at the start of the first page: ['22-01388', '22-01389']
SKIPPED abstraction_split_2022_case06_May2022_006.pdf: no ME# case number at the start of the first page

Preview only: 4 file(s) would be renamed; 2 skipped. Run again with --apply to rename.
```

Tests:
```bash
pytest
```
The 15 automated tests use fake files and check that the tool:
- reads the case year, month received, and case number correctly, and rejects malformed ones
- matches each file with its own case number, even when a neighbouring file is broken
- skips files that would end up with the same name, or would overwrite an existing file
- previews without renaming, renames only with `--apply`, and finds nothing new on a re-run
- ignores files that aren't PDFs
