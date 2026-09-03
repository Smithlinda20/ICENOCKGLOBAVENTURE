Local development virtual environment
======================================
python -m venv development/venv

Windows:
  development\venv\Scripts\activate

Linux/macOS:
  source development/venv/bin/activate

Then from the project root:
  pip install -r requirements.txt

Do NOT commit development/venv - it is OS/Python-version specific and is
already excluded in .gitignore.
