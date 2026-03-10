#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import toml
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import WORKDIR, Language

APP_NAME = "petersql"
LANGUAGES = Language.get_codes()

LOCALE_DIR = WORKDIR.joinpath("locale")
POT_FILE = LOCALE_DIR.joinpath(f"{APP_NAME}.pot")
PYPROJECT_FILE = WORKDIR.joinpath("pyproject.toml")


def get_project_info():
    """Read project information from pyproject.toml"""
    try:
        with open(PYPROJECT_FILE, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        project = data.get('project', {})
        return {
            'name': project.get('name'),
            'version': project.get('version')
        }
    except Exception:
        return {'name': 'PeterSQL', 'version': '0.1.0'}

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)


def generate_header(lang):
    """Generate proper header for .po files based on language"""
    project_info = get_project_info()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M%z")
    
    language = Language.from_code(lang)
    lang_name = f"{language.label} ({lang})"
    
    return f'''# {lang_name} translations for {project_info['name']}.
# Copyright (C) 2026 {project_info['name']}
# This file is distributed under the same license as the {project_info['name']} project.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: {project_info['name']} {project_info['version']}\\n"
"POT-Creation-Date: {current_date}\\n"
"PO-Revision-Date: {current_date}\\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

'''


def extract():
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)

    run(
        f"pybabel extract "
        f"-F babel.cfg "
        f"-o {POT_FILE} "
        f"./ "
        f"--omit-header"
    )


def update():
    for lang in LANGUAGES:
        message_dir = LOCALE_DIR.joinpath(lang, "LC_MESSAGES")
        message_dir.mkdir(parents=True, exist_ok=True)

        po_file = message_dir.joinpath(f"{APP_NAME}.po")

        if not po_file.exists():
            # Create new .po file with proper header
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(generate_header(lang))
            
            # Then update with babel to add translations
            run(
                f"pybabel update "
                f"-i {POT_FILE} "
                f"-o {po_file} "
                f"-l {lang} "
            )
        else:
            # Always prepend header for existing files (one-time patch)
            with open(po_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(generate_header(lang))
                f.write(existing_content)
            
            # Update with babel
            run(
                f"pybabel update "
                f"-i {POT_FILE} "
                f"-o {po_file} "
                f"-l {lang} "
            )


def compile():
    for lang in LANGUAGES:
        message_dir = LOCALE_DIR.joinpath(lang, "LC_MESSAGES")
        po_file = message_dir.joinpath(f"{APP_NAME}.po")
        mo_file = message_dir.joinpath(f"{APP_NAME}.mo")

        if po_file.exists():
            run(f"msgfmt {po_file} -o {mo_file}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    extract()
    update()
    compile()
