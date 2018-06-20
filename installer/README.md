# Resources for creating standalone juicebox-cli executables

## General procedure

- Get Python 2 and pip installed
- Get virtualenv installed (if you prefer) (probably using `pip install --user virtualenv`)
- Create and activate a virtualenv (if you prefer)
- Clone this juicebox-cli repo. Within it:
- `pip install -r requirements-dev.txt pyinstaller`
- and then...
  - *OSX*: `pyinstaller -F installer/juice.py`
  - *Windows*: `pyinstaller -F installer/juice.windows.py`
  - *Linux*: `pyinstaller -F installer/juice.py`

This will result in a standalone executable being placed in `dist/`.

## Known issues

- See the code comments in installer/juice.windows.py
