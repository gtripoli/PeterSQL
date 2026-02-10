#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from pathlib import Path

APP_NAME = "petersql"
LANGUAGES = ["fr_FR", "it_IT", "es_ES", "en_US", "de_DE"]

BASE_DIR = Path(__file__).parent
LOCALE_DIR = BASE_DIR.joinpath("locale")
POT_FILE = LOCALE_DIR.joinpath(f"{APP_NAME}.pot")

def run(cmd):
    subprocess.run(cmd, shell=True, check=True)


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
            shutil.copy(POT_FILE, po_file)

        else:
            run(
                f"pybabel update "
                f"-i {POT_FILE} "
                f"-o {po_file} "
                f"-l {lang} "
                f"--omit-header"
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
