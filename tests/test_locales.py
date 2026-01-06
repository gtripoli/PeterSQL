import pytest
from unittest.mock import patch, MagicMock
import os
import shutil
import subprocess

from locales import execute_command, update, compile, LANGUAGES, OUTPUT_DIRECTORY


class TestLocales:
    @patch('subprocess.run')
    def test_execute_command(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = 'stdout'
        mock_result.stderr = 'stderr'
        mock_run.return_value = mock_result

        stdout, stderr = execute_command('echo hello')

        mock_run.assert_called_once_with('echo hello', shell=True, capture_output=True, text=True)
        assert stdout == 'stdout'
        assert stderr == 'stderr'

    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('shutil.copy')
    @patch('locales.execute_command')
    def test_update(self, mock_execute, mock_copy, mock_exists, mock_makedirs):
        mock_exists.return_value = False  # No existing .po files

        update(None)

        mock_makedirs.assert_called()
        mock_execute.assert_called_with('pybabel extract -F babel.cfg -o locales/messages.pot ./ --omit-header')
        mock_copy.assert_called()  # For each language
        # More asserts for the calls

    @patch('locales.execute_command')
    def test_compile(self, mock_execute):
        compile()

        mock_execute.assert_called_once_with('pybabel compile -d locales -f')
