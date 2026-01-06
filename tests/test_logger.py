import pytest
import logging
from helpers.logger import *


class TestLogger:
    def test_logger_creation(self):
        # The logger is set up in helpers/logger.py
        logger = logging.getLogger("PeterSQL")
        assert logger is not None
        assert logger.level == logging.DEBUG
