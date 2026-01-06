#!/usr/bin/env python
import argparse
import os
import os.path
import shutil
import subprocess

LANGUAGES = ["fr_FR", "it_IT", "es_ES", "en_US", "de_DE"]
OUTPUT_DIRECTORY = "locales"

parser = argparse.ArgumentParser()


def execute_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr


def update(loco_key):
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    source_messages = os.path.join(OUTPUT_DIRECTORY, "messages.pot")

    execute_command(f"pybabel extract -F babel.cfg -o {source_messages} ./ --omit-header")


    for language in LANGUAGES:
        lc_messages = os.path.join(OUTPUT_DIRECTORY, language, "LC_MESSAGES")
        os.makedirs(lc_messages, exist_ok=True)

        language_messages = os.path.join(lc_messages, "messages.po")

        if not os.path.exists(language_messages):
            shutil.copy(source_messages, language_messages)
        else:
            execute_command(f"pybabel update -i {source_messages} -d locales -l {language} --omit-header")


def compile():

    execute_command(f"pybabel compile -d {OUTPUT_DIRECTORY} -f")


if __name__ == "__main__":
    args = parser.parse_args()

    update(getattr(args, "loco_key", None))
    compile()
