# Import specific sub-modules for easy access in controller_main.py
from src.settings.constants import *
from src.settings.config import *

from opensourceleg.logging import Logger, LogLevel
from src.utils.filing_utils import get_logging_info

CONSOLE_LOGGER = Logger(enable_csv_logging=False,
                        log_path=get_logging_info(user_input_flag=False)[0],
                        stream_level = LogLevel.INFO,
                        log_format = "%(levelname)s: %(message)s"
                        )
